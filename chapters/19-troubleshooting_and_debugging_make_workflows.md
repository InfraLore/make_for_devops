# Chapter 19 - Troubleshooting and Debugging Make Workflows

\chaptersubtitle{Mastering the tools and techniques to diagnose, fix, and
optimize complex Make-based workflows.}

You run `make deploy-staging` and it fails. But it's not a simple failure—you've
already checked the obvious things. You've run `make -n` to see what commands
would execute. You've verified your variables with `$(info ...)`. You've
confirmed the target is declared `.PHONY`. The basics are correct, yet something
deeper is wrong.

Maybe the deployment succeeds but produces incorrect results. Maybe targets run
in an unexpected order despite explicit prerequisites. Maybe the workflow works
on your machine but fails in CI. Maybe it worked yesterday and fails today with
no obvious changes.

These are the hard debugging problems—the ones that require understanding Make's
execution model at a deeper level, the ones that surface only in complex
multi-service deployments, the ones that appear under load or in production.

This chapter equips you with advanced techniques for diagnosing and fixing these
challenging issues.

\begin{calloutbox}[Prerequisites: Chapter 3] This chapter assumes you're
comfortable with the debugging basics covered in Chapter 3: using \texttt{make
-n} for dry runs, \texttt{make -p} to inspect variables, adding \texttt{@} for
output control, and basic error handling patterns. If you're new to Make
debugging, start with Chapter 3's "Debugging and Troubleshooting Makefile
Execution" section before proceeding here. \end{calloutbox}

\pagebreak

![Make's Execution Model](images/chapter19.png)

\pagebreak

## Understanding Make's Execution Model in Depth

Most advanced Make debugging requires understanding what happens between when
you press Enter and when commands execute. Make's execution has three distinct
phases, and problems can hide in any of them:

### 1. Parsing Phase

Make reads all Makefiles, expands immediate variables (`:=`), evaluates
includes, processes conditionals, and builds an internal representation of
targets and their relationships. 

**Common issues in this phase:**
- Syntax errors in conditionals or function calls
- Circular includes or recursive variable definitions
- Expensive shell commands in `:=` assignments slowing Makefile loading

### 2. Dependency Resolution Phase

Make walks the dependency graph, determines which targets are out of date based
on file timestamps or phony declarations, and decides what needs to run.

**Common issues in this phase:**
- Unexpected target execution order in complex graphs
- File-based dependencies behaving incorrectly
- Timestamp confusion in networked filesystems or containers
- Race conditions in parallel execution

### 3. Execution Phase

Make runs shell commands for each selected target, handling errors and
maintaining the execution environment.

**Common issues in this phase:**
- Environment variable scoping problems
- Shell flags not propagating correctly
- Resource exhaustion in long-running workflows
- Subtle shell behavior differences across systems

Understanding which phase contains your problem dramatically narrows the
debugging space.

## Advanced Debugging Techniques

### Debugging Complex Dependency Graphs

When you have targets with 3+ levels of prerequisites and things execute in the
wrong order:

```makefile
# Visualize the actual dependency resolution
debug-deps: ## Show detailed dependency resolution
	@echo "Dependency analysis for: $(TARGET)"
	@make --debug=v $(TARGET) 2>&1 | \
		grep -E "(Considering|prerequisite|newer|Must remake)" | \
		head -50

# Example: make debug-deps TARGET=deploy-production
```

For really complex graphs, export to GraphViz:

```makefile
graph-deps: ## Generate dependency graph
	@make -Bnd $(TARGET) | \
		make2graph | \
		dot -Tpng -o deps-$(TARGET).png
	@echo "Generated deps-$(TARGET).png"

# Requires: apt-get install make2graph graphviz
```

**Real-world example:** A deployment target wasn't running tests because an
intermediate target (`validate-manifests`) inadvertently created a file called
`test`, causing Make to think tests were up to date:

```makefile
# Problem: validate-manifests creates 'test' file
validate-manifests:
	helm template charts/ --output-dir test/
	yamllint test/

# Solution: Use a uniquely named output directory
validate-manifests:
	helm template charts/ --output-dir .helm-output/
	yamllint .helm-output/
```

### Debugging Recursive Make

When orchestrating multiple services with recursive Make calls, failures become
opaque:

```makefile
# Poor: Silent failures in recursive make
deploy-all:
	for service in $(SERVICES); do \
		$(MAKE) -C services/$$service deploy; \
	done

# Better: Explicit error handling and context
deploy-all:
	@failed=""; \
	for service in $(SERVICES); do \
		echo "Deploying $$service..."; \
		if ! $(MAKE) -C services/$$service deploy; then \
			failed="$$failed $$service"; \
			echo "FAILED: $$service"; \
		fi; \
	done; \
	if [ -n "$$failed" ]; then \
		echo ""; \
		echo "Deployment failed for:$$failed"; \
		echo ""; \
		echo "To retry individual services:"; \
		for service in $$failed; do \
			echo "  make -C services/$$service deploy"; \
		done; \
		exit 1; \
	fi
```

Add recursive make debugging:

```makefile
# Track recursive make depth
export MAKE_DEPTH ?= 0

deploy:
	@echo "$(shell printf '%*s' $$((MAKE_DEPTH * 2)) '')→ Deploying $(SERVICE_NAME)"
	@MAKE_DEPTH=$$((MAKE_DEPTH + 1)) $(MAKE) _deploy

_deploy:
	# Actual deployment commands
```

### Race Conditions in Parallel Execution

Parallel make (`make -j`) can expose hidden dependencies:

```makefile
# Problem: These targets aren't truly independent
test-unit test-integration:
	pytest tests/$@/ --cov-report=xml

# Both write to the same coverage file, causing corruption

# Solution: Separate outputs or serialize
test-unit:
	pytest tests/unit/ --cov-report=xml:coverage-unit.xml

test-integration:
	pytest tests/integration/ --cov-report=xml:coverage-integration.xml

# Or explicitly prevent parallelism for this target
.NOTPARALLEL: test-unit test-integration
```

**Detecting race conditions:**

```makefile
test-race: ## Test for race conditions
	@echo "Running targets in parallel 10 times..."
	@for i in $$(seq 1 10); do \
		echo "Iteration $$i"; \
		make -j4 build test > /dev/null 2>&1 || \
			(echo "FAILED on iteration $$i" && exit 1); \
	done
	@echo "No race conditions detected"
```

### Timestamp Issues in Distributed Systems

File timestamps behave unexpectedly in Docker, NFS, or CI environments:

```makefile
# Problem: Docker build always runs because context files have "future" timestamps
docker-build: .docker-build-timestamp

.docker-build-timestamp: Dockerfile $(shell find src/ -type f)
	docker build -t $(IMAGE_NAME) .
	touch .docker-build-timestamp

# In CI, this fails because git checkout sets weird timestamps
```

**Solution:** Use content hashing instead of timestamps:

```makefile
# Content-based dependency
.docker-build.hash: Dockerfile $(shell find src/ -type f)
	@current=$$(find src/ Dockerfile -type f -exec sha256sum {} \; | \
		sha256sum | cut -d' ' -f1); \
	if [ -f .docker-build.hash ]; then \
		previous=$$(cat .docker-build.hash); \
		if [ "$$current" = "$$previous" ]; then \
			echo "Docker build not needed (content unchanged)"; \
			exit 0; \
		fi; \
	fi; \
	docker build -t $(IMAGE_NAME) .; \
	echo "$$current" > .docker-build.hash

docker-build: .docker-build.hash
```

## Performance Debugging

Slow Makefiles kill productivity. Here's how to find and fix bottlenecks:

### Profiling Make Execution

```makefile
# Time every target automatically
SHELL := /usr/bin/time -f "Target took: %E elapsed, %U user, %S system" /bin/bash

# Or build custom profiling
profile-deploy: ## Profile deployment workflow
	@echo "Profiling: deploy workflow"
	@echo "=========================="
	@echo ""
	@start=$$(date +%s); \
	$(MAKE) lint; \
	echo "[$$((($$(date +%s) - start)))s] lint completed"; \
	\
	start=$$(date +%s); \
	$(MAKE) test-unit; \
	echo "[$$((($$(date +%s) - start)))s] test-unit completed"; \
	\
	start=$$(date +%s); \
	$(MAKE) test-integration; \
	echo "[$$((($$(date +%s) - start)))s] test-integration completed"; \
	\
	start=$$(date +%s); \
	$(MAKE) docker-build; \
	echo "[$$((($$(date +%s) - start)))s] docker-build completed"; \
	\
	start=$$(date +%s); \
	$(MAKE) docker-push; \
	echo "[$$((($$(date +%s) - start)))s] docker-push completed"
```

### Optimizing Expensive Shell Operations

```makefile
# Problem: Git commands run on every invocation
VERSION = $(shell git describe --tags --always)
BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
COMMIT = $(shell git rev-parse --short HEAD)

# These run even for 'make help'!

# Solution: Lazy evaluation for expensive operations
_git_version = $(shell git describe --tags --always)
_git_branch = $(shell git rev-parse --abbrev-ref HEAD)
_git_commit = $(shell git rev-parse --short HEAD)

VERSION = $(if $(VERSION_CACHED),$(VERSION_CACHED),\
	$(eval VERSION_CACHED := $(_git_version))$(VERSION_CACHED))

# Or: Only compute when needed
docker-build:
	@VERSION=$$(git describe --tags --always); \
	docker build --build-arg VERSION=$$VERSION -t $(IMAGE_NAME) .
```

### Parallel Execution Strategy

```makefile
# Identify parallelizable targets
test-unit test-integration test-e2e:
	pytest tests/$@/

# Run with: make -j3 test-unit test-integration test-e2e

# But serialize where needed
deploy-services: _deploy-database _deploy-backend _deploy-frontend

_deploy-database:
	kubectl apply -f k8s/database/

# Backend depends on database
_deploy-backend: _deploy-database
	kubectl apply -f k8s/backend/

# Frontend depends on backend
_deploy-frontend: _deploy-backend
	kubectl apply -f k8s/frontend/
```

## Production Incident Debugging

When a deployment fails in production at 2 AM:

### Forensic Debugging

```makefile
# Capture state for post-mortem
incident-snapshot: ## Capture debugging snapshot
	@mkdir -p incident-$$(date +%Y%m%d-%H%M%S)
	@cd incident-$$(date +%Y%m%d-%H%M%S) && \
	echo "Capturing incident snapshot..." && \
	kubectl get all -n $(NAMESPACE) > k8s-state.txt && \
	kubectl describe deployment/$(SERVICE_NAME) -n $(NAMESPACE) > deployment.txt && \
	kubectl logs deployment/$(SERVICE_NAME) -n $(NAMESPACE) --tail=500 > logs.txt && \
	make debug > make-debug.txt && \
	env > environment.txt && \
	git log -1 --pretty=fuller > git-info.txt && \
	git diff > git-changes.txt
	@echo "Snapshot captured in incident-*/"
```

### Emergency Rollback with Diagnostics

```makefile
emergency-rollback: ## Rollback with full diagnostics
	@echo "=== EMERGENCY ROLLBACK ==="
	@echo ""
	@echo "Current state:"
	@kubectl get deployment/$(SERVICE_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "Rolling back..."
	@kubectl rollout undo deployment/$(SERVICE_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "Waiting for rollback to complete..."
	@kubectl rollout status deployment/$(SERVICE_NAME) -n $(NAMESPACE) --timeout=120s
	@echo ""
	@echo "New state:"
	@kubectl get deployment/$(SERVICE_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "Recent events:"
	@kubectl get events -n $(NAMESPACE) --sort-by='.lastTimestamp' | tail -20
	@echo ""
	@echo "Rollback complete. Capture logs with: make incident-snapshot"
```

## CI/CD-Specific Debugging

### Reproducing CI Failures Locally

```makefile
# Run in CI-like environment
ci-shell: ## Start shell in CI environment
	docker run -it --rm \
		-v $(PWD):/workspace \
		-w /workspace \
		-e CI=true \
		-e ENVIRONMENT=ci \
		--entrypoint /bin/bash \
		$(CI_IMAGE)

ci-test: ## Run tests exactly as CI does
	docker run --rm \
		-v $(PWD):/workspace \
		-w /workspace \
		-e CI=true \
		$(CI_IMAGE) \
		make test
```

### Debugging CI-Only Failures

```makefile
# Add CI debugging mode
ifdef CI
  # In CI: verbose output
  Q :=
  QUIET :=
  DEBUG := 1
else
  # Locally: clean output
  Q := @
  QUIET := --quiet
  DEBUG := 0
endif

deploy:
	$(Q)echo "Deploying $(IMAGE_NAME)..."
ifeq ($(DEBUG),1)
	$(Q)echo "Environment: $(ENVIRONMENT)"
	$(Q)echo "Namespace: $(NAMESPACE)"
	$(Q)echo "Image: $(IMAGE_NAME)"
	$(Q)kubectl version
	$(Q)kubectl config current-context
endif
	$(Q)kubectl apply -f k8s/
```

## Memory and Resource Debugging

Large builds can exhaust system resources:

```makefile
# Monitor resource usage
monitor-build: ## Build with resource monitoring
	@(while true; do \
		echo "$$(date): CPU: $$(top -bn1 | grep "Cpu(s)" | awk '{print $$2}')% \
		MEM: $$(free -m | awk 'NR==2{printf "%.0f%%", $$3*100/$$2}')"; \
		sleep 5; \
	done) & \
	monitor_pid=$$!; \
	$(MAKE) docker-build; \
	kill $$monitor_pid 2>/dev/null

# Limit Docker build resources
docker-build:
	docker build \
		--memory=4g \
		--cpu-quota=200000 \
		-t $(IMAGE_NAME) .
```

## Testing Your Debugging Tools

Yes, test your debugging infrastructure:

```makefile
test-debugging: ## Test debugging tools work
	@echo "Testing debug infrastructure..."
	@$(MAKE) debug > /dev/null || \
		(echo "FAIL: debug target broken" && exit 1)
	@$(MAKE) -n deploy > /dev/null || \
		(echo "FAIL: deploy dry-run broken" && exit 1)
	@$(MAKE) incident-snapshot > /dev/null || \
		(echo "FAIL: incident-snapshot broken" && exit 1)
	@echo "All debugging tools functional"
```

## Building a Support Bundle

Help others help you:

```makefile
support-bundle: ## Generate complete debugging bundle
	@echo "Generating support bundle..."
	@mkdir -p support-bundle
	@echo "=== Make Information ===" > support-bundle/make-info.txt
	@make --version >> support-bundle/make-info.txt
	@echo "" >> support-bundle/make-info.txt
	@echo "=== Variables ===" >> support-bundle/make-info.txt
	@$(MAKE) debug >> support-bundle/make-info.txt 2>&1
	@echo "" >> support-bundle/make-info.txt
	@echo "=== Dependency Graph ===" >> support-bundle/make-info.txt
	@$(MAKE) -nd deploy 2>&1 | head -100 >> support-bundle/make-info.txt
	@echo "" >> support-bundle/make-info.txt
	@echo "=== Environment ===" > support-bundle/environment.txt
	@env | sort >> support-bundle/environment.txt
	@echo "=== Git State ===" > support-bundle/git-state.txt
	@git status >> support-bundle/git-state.txt
	@git log -5 --oneline >> support-bundle/git-state.txt
	@echo "=== System Info ===" > support-bundle/system.txt
	@uname -a >> support-bundle/system.txt
	@docker version >> support-bundle/system.txt 2>&1 || true
	@kubectl version --client >> support-bundle/system.txt 2>&1 || true
	@cp Makefile support-bundle/
	@tar czf support-bundle-$$(date +%Y%m%d-%H%M%S).tar.gz support-bundle/
	@rm -rf support-bundle/
	@echo "Created support-bundle-*.tar.gz"
```

## Key Takeaways

Advanced Make debugging requires:

1. **Understanding the three execution phases**: parsing, dependency resolution,
   execution
2. **Specialized techniques for complex scenarios**: recursive make, parallel
   execution, timestamp issues
3. **Production-ready debugging tools**: incident snapshots, emergency
   rollbacks, support bundles
4. **Performance profiling**: identifying bottlenecks in large workflows
5. **CI/CD awareness**: reproducing failures and debugging in automated
   environments

The most important skill is knowing *which layer* contains your problem. Is it
dependency ordering? Variable expansion? Shell behavior? Resource constraints?
Once you identify the layer, the appropriate debugging technique becomes clear.

Build debugging capabilities into your Makefiles from the start. The `debug`,
`profile`, `incident-snapshot`, and `support-bundle` targets aren't
overhead—they're essential infrastructure that pays for itself the first time
something goes wrong at 2 AM.

When your Makefile can diagnose its own problems and guide users toward
solutions, you've created something that scales far beyond your own expertise.
