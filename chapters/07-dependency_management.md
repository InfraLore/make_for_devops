# Chapter 7: Dependency Management for DevOps Workflows

\chaptersubtitle{Leveraging Make's dependency system to ensure correct execution
order and prevent common deployment pitfalls.}

Make's dependency system is where the magic happens in DevOps workflows. While
other automation tools require you to explicitly script every step in sequence,
Make lets you declare what depends on what, then automatically figures out the
optimal execution order. This declarative approach transforms error-prone linear
scripts into robust, self-organizing workflows.

Consider a typical deployment: build application, run tests, push image, update
manifests, deploy to cluster. A traditional script runs every step regardless of
whether it's necessary, fails catastrophically if any step breaks, and can't
leverage parallelization. Make's dependency system solves these issues
elegantly.

\begin{calloutbox}[Start Simple: Basic Dependency Patterns]
Master these fundamental dependency patterns:

\begin{enumerate} \item \textbf{Linear dependencies}: \texttt{deploy: test}
ensures tests run before deployment \item \textbf{Parallel opportunities}:
\texttt{test: build} and \texttt{push: build} can run simultaneously \item
\textbf{Validation gates}: \texttt{deploy: validate build test push} enforces
prerequisites \item \textbf{Conditional execution}: Make only rebuilds what
changed \item \textbf{Failure isolation}: If tests fail, deployment never runs
\end{enumerate}

These patterns handle most workflow orchestration needs.
\end{calloutbox}

## Modeling Deployment Dependencies

Dependencies come in different forms:

**Sequential Dependencies** - operations in order:

```makefile
deploy: test
test: build
build: lint
```

**Parallel Dependencies** - operations simultaneously:

```makefile
all-checks: lint security-scan  # Both can run in parallel on same source
lint: src
security-scan: src
```

**Validation Dependencies/Quality Gates** - prerequisites before proceeding:

```makefile
deploy: validate-environment validate-secrets build test
```

\newpage

### Real-World Pipeline Dependencies

Model a complete deployment pipeline:

```makefile
# Final deployment with all prerequisites
deploy: validate-ready push-image update-manifests apply verify

# Validation (parallel)
validate-ready: validate-env validate-secrets validate-cluster

# Build phase
build: lint security-scan
	@./scripts/build.sh \footnote{Script delegation pattern---see Chapter 21 for how this aids learning.}

# Testing phase
test: build
	@./scripts/test.sh

# Preparation (parallel after build)
push-image: build test
	@./scripts/push.sh

update-manifests: build
	@./scripts/update-manifests.sh

# Deployment (requires all preparation)
apply: push-image update-manifests
	@./scripts/apply.sh

verify: apply
	@./scripts/verify.sh
```

This ensures: validation first, building after checks, testing on actual
artifacts, parallel preparation, deployment only after prerequisites,
verification after deployment.

\newpage

### Multi-Service Dependencies

Model inter-service dependencies:

```makefile
# Deploy entire stack
deploy-stack: deploy-database deploy-cache deploy-api deploy-frontend

# Database first
deploy-database: build-database
	@./scripts/deploy-database.sh

# Cache parallel with database
deploy-cache: build-cache
	@./scripts/deploy-cache.sh

# API requires both
deploy-api: deploy-database deploy-cache build-api test-api
	@./scripts/deploy-api.sh

# Frontend only needs API
deploy-frontend: deploy-api build-frontend
	@./scripts/deploy-frontend.sh
```

\newpage

## File-Based Dependencies

Track infrastructure state with files:

```makefile
# Deploy infrastructure only when config changes
infra/.applied: infra/main.tf infra/variables.tf
	@./scripts/terraform-apply.sh
	@touch infra/.applied

# Deploy app when infrastructure ready
deploy-app: infra/.applied k8s/deployment.yaml
	@./scripts/deploy-app.sh

# Update manifests when templates change
k8s/deployment.yaml: k8s/deployment.yaml.template config/$(ENV).env
	@./scripts/generate-manifest.sh
```

\newpage

### Docker Image Dependencies

Track Docker builds efficiently:

```makefile
# Build only when source changes
.image-built: Dockerfile $(shell find src -type f)
	@./scripts/build-image.sh
	@touch .image-built

# Push when built and tested
.image-pushed: .image-built .tests-passed
	@./scripts/push-image.sh
	@touch .image-pushed

# Test when built
.tests-passed: .image-built
	@./scripts/test-image.sh
	@touch .tests-passed

# Deploy when pushed
deploy: .image-pushed k8s-manifests
	@./scripts/deploy.sh
```

\newpage

## Parallel Execution

One of Make's most powerful features is automatic parallel execution—the ability
to run independent targets simultaneously. When you have targets like `lint`,
`security-scan`, and `type-check` that all depend on the same source files but
don't depend on each other, they can run at the same time rather than
sequentially. This can dramatically reduce workflow execution time.

However, **parallelism is not automatic**. This is a common misconception: Make
will not parallelize your workflow unless you explicitly ask it to with the `-j`
flag. Running `make test` executes everything sequentially, even if your
dependency structure allows parallelism. Only `make -j4 test` enables parallel
execution with 4 simultaneous jobs.

The candidates for parallel execution are targets that:

- Share the same prerequisites (like both depending on `build`)
- Have no dependencies on each other
- Perform independent operations (one doesn't need the other's output)

For example: `build-frontend: src/frontend` and `build-backend: src/backend` can
run in parallel because they're building independent services. But
`deploy-frontend: build-frontend test-frontend` cannot run in parallel with
`build-frontend` because it depends on the build completing first. This creates
efficient workflows where independent builds happen simultaneously.

\begin{calloutbox}[Parallelism: An Optimization You Discover, Not Design]
Don't start by trying to design parallel execution into your Makefiles. Instead:

\begin{enumerate}
\item Write targets with correct dependencies first
\item Run your workflows and notice where they're slow
\item Look for independent operations that could run simultaneously
\item Add \texttt{make -j4} to see what parallelizes naturally
\item If nothing speeds up, your dependencies are too sequential
\end{enumerate}

\textbf{Important:} Parallelism only happens when you invoke Make with
\texttt{-j}. Running \texttt{make deploy} executes sequentially no matter how
your dependencies are structured. Run \texttt{make -j4 deploy} to enable
parallel execution with 4 jobs.

\textbf{Make it part of your review process:} When reviewing Makefiles (yours or
your team's), ask: "Can any of these targets run in parallel?" Look for targets
with the same prerequisites but no dependencies on each other. These are natural
parallelization opportunities.

Most developers discover parallelism by running \texttt{make -j4} on an existing
Makefile and noticing which operations suddenly run simultaneously. This reveals
which dependencies are truly independent. \end{calloutbox}

\newpage
Make automatically identifies parallelization opportunities:

```makefile
# All run in parallel (no interdependencies)
all-checks: lint security-scan type-check format-check
	@echo "All checks complete"

# Run with: make -j4 all-checks

# Dependencies allow parallelism
deploy-all: deploy-backend deploy-frontend deploy-monitoring

# Backend and frontend build in parallel
deploy-backend: build-backend test-backend
	@./scripts/deploy-backend.sh

deploy-frontend: build-frontend test-frontend
	@./scripts/deploy-frontend.sh

# Monitoring depends on both
deploy-monitoring: deploy-backend deploy-frontend
	@./scripts/deploy-monitoring.sh
```

\newpage

### Controlling Parallelism

Fine-tune parallel execution:

```makefile
# CPU-intensive (limit parallelism)
build-all: ## Build all images
	@$(MAKE) -j2 build-api build-frontend build-worker

# I/O-bound (allow more parallelism)
test-all: ## Test all services
	@$(MAKE) -j8 test-api test-frontend test-worker

# Mixed workload
ci-pipeline: ## CI pipeline with optimal parallelism
	@$(MAKE) -j4 lint security-scan type-check
	@$(MAKE) -j2 build-api build-frontend
	@$(MAKE) -j4 test-unit test-integration
```

## Handling Failures

Implement recovery mechanisms:

```makefile
# Deployment with rollback
deploy-safe: backup deploy-attempt || rollback

backup:
	@./scripts/backup-state.sh
	@touch .backup-created

deploy-attempt: build test push
	@./scripts/deploy.sh
	@./scripts/verify.sh

rollback:
	@echo "Rolling back..."
	@./scripts/rollback.sh
```

### Partial Completion

Handle scenarios where some operations succeed:

```makefile
# Deploy with state tracking
deploy-tracked:
	@rm -f .deploy-state-*
	@$(MAKE) deploy-database && touch .deploy-state-db || true
	@$(MAKE) deploy-api && touch .deploy-state-api || true
	@$(MAKE) check-completeness

check-completeness:
	@test -f .deploy-state-db || echo "Database failed"
	@test -f .deploy-state-api || echo "API failed"
```

## Pattern Rules for Scale

Use patterns for multiple similar dependencies:

```makefile
# Pattern for service deployments
deploy-%-service: build-%-service test-%-service
	@./scripts/deploy-service.sh $*

# Pattern for environments
deploy-to-%: validate-% build test
	@./scripts/deploy-to-env.sh $*

# Use the patterns
deploy-all-services: deploy-user-service deploy-order-service

deploy-all-envs: deploy-to-dev deploy-to-staging
```

## Using Parallelism Responsibly

While Make's parallel execution can dramatically speed up workflows, not all
parallelization opportunities should be taken. The technical ability to run
tasks simultaneously doesn't mean it's operationally wise.

### When Parallelism Makes Sense

**Safe parallel operations** share inputs but produce independent outputs:

```makefile
# Multiple validations on same code - safe to parallelize
validate-all: lint security-scan type-check format-check
	@echo "All validations complete"

# Multiple builds from same source - safe to parallelize
build-all: build-api build-frontend build-worker
	@echo "All services built"

# Multiple tests on same artifacts - safe to parallelize
test-all: test-unit test-integration test-e2e
	@echo "All tests complete"
```

### When Parallelism Is Risky

**Avoid parallelizing operations with quality gates:**

```makefile
# DON'T: Push while testing (technically possible, operationally bad)
# deploy: push test  # Both depend on build - could run in parallel
# push: build
# test: build

# DO: Test before pushing (sequential quality gate)
deploy: push
push: test
test: build
```

\newpage
**Avoid parallelizing operations that compete for resources:**

```makefile
# DON'T: Multiple database migrations simultaneously
# migrate-all: migrate-users migrate-orders migrate-inventory

# DO: Sequential migrations to avoid conflicts
migrate-all: migrate-users migrate-orders migrate-inventory
migrate-orders: migrate-users
migrate-inventory: migrate-orders
```

### Quality Gates vs Speed

The fundamental tension in DevOps automation is between speed and safety. Make's
dependency system helps you be explicit about this trade-off:

```makefile
# Quality-first approach (slower, safer)
deploy-safe: validate build test security-scan push deploy-step verify
	@echo "Safe deployment complete"

# Speed-optimized approach (faster, with calculated risks)
deploy-fast: deploy-step verify
deploy-step: push
push: build validate  # Skip some validations, parallel where safe
validate: lint type-check  # Parallel validations only
```

\newpage

### Team Communication

Document parallelization decisions in your Makefile:

```makefile
# Parallel execution safe - independent validations
validate-code: lint security-scan type-check ## Run code validations (parallel safe)

# Sequential execution required - quality gate
deploy-production: test push deploy verify ## Prod deployment (sequential for safety)
	@echo "Production deployment follows strict sequence"

# Parallel builds, sequential deployment
deploy-all: build-all test-all deploy-sequential ## Build parallel, deploy sequential
build-all: ## Build all services (parallel safe)
	@$(MAKE) -j4 build-api build-frontend build-worker
```

The key principle: **parallelize for efficiency, sequence for safety**. When in
doubt, choose the safer sequential approach. Your future self (and your team)
will thank you when a bug doesn't make it to production because tests caught it
before the push completed.

## Key Takeaways

Make's dependency system transforms workflows from brittle scripts into robust
orchestration:

1. **Declare Relationships**: Focus on what depends on what, not execution order
2. **Leverage Parallelism**: Make runs independent tasks in parallel automatically
3. **Use File Dependencies**: Track state and configuration changes
4. **Handle Failures**: Implement rollback and partial completion strategies
5. **Pattern Rules**: Scale dependency patterns across services and environments
6. **Use Parallelism Responsibly**: While Make can parallelize independent
      operations automatically, prioritize safety over speed—test before
      pushing, validate before deploying, and sequence quality gates even when
      parallel execution is technically possible


The power lies in the declarative approach: describe relationships, Make figures
out optimal execution. This creates workflows that are more reliable, efficient,
and maintainable than traditional scripts.

In the next chapter, we'll explore Make's advanced features that enable even
more sophisticated automation while maintaining simplicity and discoverability.
