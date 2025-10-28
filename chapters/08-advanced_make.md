# Chapter 8: Advanced Make Features for Workflow Automation

\chaptersubtitle{Exploring Make's powerful advanced features that enable sophisticated workflow automation while maintaining simplicity and discoverability.}

Up to this point, we've explored Make's fundamental features: variables, targets, dependencies, and organization patterns. These basics handle most DevOps workflow needs effectively. But Make has a deeper toolkit of advanced features that can transform complex, repetitive operational tasks into elegant, maintainable automation.

This chapter explores Make's sophisticated features: pattern rules that eliminate repetitive target definitions, recursive Make for coordinating multiple projects, external tool integration patterns, and conditional execution based on system state.

## The DevOps Automation Dilemma

DevOps work inherently involves managing **multiplicity at scale**: multiple environments (dev, staging, prod), multiple services (api, frontend, worker), multiple deployment strategies (rolling, canary, blue-green), and multiple cloud providers or regions. This multiplicity creates a tension between three competing needs:

**Consistency**: Every environment should deploy the same way. Every service should follow the same standards. When you fix a bug in one workflow, that fix should apply everywhere automatically.

**Flexibility**: Production needs extra safety checks that dev doesn't. The payment service needs PCI compliance steps that other services don't. Some teams use Docker, others use native builds.

**Maintainability**: When deployment requirements change, you shouldn't need to update fifty similar targets. When a new team member reads your Makefile, they should understand the pattern, not memorize individual cases.

Traditional Makefile approaches force you to choose: either duplicate targets for consistency (brittle and hard to maintain), or write complex shell scripts that hide logic from Make (losing discoverability), or create a web of dependencies that nobody understands.

Make's advanced features solve this dilemma by letting you **encode patterns without losing transparency**. Pattern rules say "here's how we deploy to *any* environment" while still letting you see exactly what `make deploy-prod` will do. Recursive Make coordinates multiple projects while keeping each project's Makefile simple and focused. Functions encapsulate complex sequences while keeping the invocation readable.

The key insight: **these features let you scale automation without scaling complexity for users**. A new developer can still run `make help` and understand what's possible. They can run `make -n deploy-staging` and see exactly what will happen. But behind that simplicity, you've eliminated hundreds of lines of duplication.

## When Multiplicity Demands Abstraction

Look for these signals that you need advanced features:

**Copy-paste proliferation**: You have `deploy-dev`, `deploy-staging`, `deploy-prod` that are identical except for one word. Or five services with identical build targets.

**Change amplification**: When you improve your deployment process, you need to update it in twelve places. Miss one and environments diverge.

**Implicit knowledge**: Team members say "we deploy to staging the same way as prod, but..." and the "but" is only in their heads, not in the Makefile.

**Multi-project coordination**: You're running make commands in five different directories in a specific order, and that order isn't documented anywhere.

These patterns indicate that your workflow has inherent structure that isn't captured in your Makefile. The advanced features in this chapter give you tools to make that implicit structure explicit and automatic.

## Applying Advanced Features to Your Workflows

You understand the tools. Now here's how to recognize when to use them in your actual DevOps work.

### Start with Your Pain Points

Look at your current Makefile. What makes you groan?

- **"I just added a fifth environment and had to update 20 targets"** → Pattern rules
- **"I keep forgetting to run the pre-deploy checks"** → Functions that bundle checks with deployment
- **"I have to coordinate three repos in the right order"** → Recursive Make
- **"Production needs different validation than staging"** → Conditional execution
- **"Every team reinvents deployment slightly differently"** → Extensible frameworks

### The Incremental Adoption Pattern

Don't rewrite your Makefile. Add one advanced feature to solve one specific pain point:

1. **Pick the most annoying duplication** - The targets you copy-paste most often
2. **Convert just that set** - Leave everything else alone
3. **Live with it for a week** - Does it actually help? Is it clear to others?
4. **Refine or revert** - If it's not clearly better, go back to simple targets
5. **Move to the next pain point** - Only after the first one proves valuable

### Example Progression

**Week 1**: You have `deploy-dev`, `deploy-staging`, `deploy-prod` that are 90% identical. Convert to `deploy-%` pattern rule. Three targets become one rule.

**Week 3**: You realize every deployment should notify Slack but you keep forgetting. Create a `deploy_with_notification` function. Now it's automatic.

**Week 5**: You're coordinating API, frontend, and worker deployments manually. Add recursive Make to orchestrate them. The sequence is now encoded, not team lore.

### Warning Signs You're Over-Engineering

- You're using pattern rules for two targets (just write two targets)
- Your functions have functions calling functions (flatten it)
- New team members can't figure out what `make deploy-prod` does (too much indirection)
- You're writing advanced features "because we might need this later" (YAGNI)

### The Test

After adding an advanced feature, run `make -n <target>` and read the output. If you can't easily understand what will happen, you've gone too far. Revert to something simpler.

\begin{calloutbox}[The Glide Path: Evolving to Advanced Features]
Don't jump straight to advanced features—evolve into them naturally as your needs grow:

\textbf{Stage 1: Start with Repetition}
\begin{itemize}
\item Write \texttt{deploy-dev}, \texttt{deploy-staging}, \texttt{deploy-prod} as separate targets
\item Copy-paste is fine when learning what each environment needs
\item Focus on making each target work reliably first
\end{itemize}

\textbf{Stage 2: Notice the Patterns}
\begin{itemize}
\item After 3-4 similar targets, you'll see the repetition
\item This is when pattern rules (\texttt{deploy-\%}) start making sense
\item Convert one set of repetitive targets at a time
\end{itemize}

\textbf{Stage 3: Handle Exceptions}
\begin{itemize}
\item Some environments need special handling
\item Use pattern rules for common cases, specific targets for exceptions
\item Don't force everything into patterns if it doesn't fit
\end{itemize}

The key is solving today's problems with today's complexity level, not building for imaginary future requirements.
\end{calloutbox}

\newpage
## Pattern Rules for Handling Multiple Environments

Pattern rules eliminate repetitive target definitions:

```makefile
# Instead of this repetition:
deploy-dev:
	@./scripts/deploy.sh dev

deploy-staging:
	@./scripts/deploy.sh staging

deploy-prod:
	@./scripts/deploy.sh prod

# Use a pattern rule:
deploy-%: validate-% ## Deploy to specified environment
	@echo "Deploying to $*..."
	@./scripts/deploy.sh $*

# Now: make deploy-dev, make deploy-staging, make deploy-prod
```

The `%` matches any string, and `$*` contains the matched portion. One rule creates multiple targets.

\newpage
### Environment-Specific Validation

Different environments need different safety levels:

```makefile
# Minimal validation for development
validate-dev:
	@./scripts/validate-basic.sh

# Enhanced validation for staging
validate-staging: validate-dev
	@./scripts/validate-staging.sh

# Maximum validation for production
validate-prod: validate-staging
	@./scripts/validate-production.sh
	@./scripts/security-audit.sh

# Pattern rule uses environment-specific validation
deploy-%: validate-%
	@./scripts/deploy.sh $*
```

Pattern rules work with prerequisites. Each environment gets appropriate validation automatically.

\newpage
### Service-Specific Pattern Rules

Handle multiple services consistently:

```makefile
# Pattern rule for services
build-%-service: ## Build specified service
	@echo "Building $* service..."
	@./scripts/build-service.sh $*

test-%-service: build-%-service ## Test specified service
	@./scripts/test-service.sh $*

deploy-%-service: test-%-service ## Deploy specified service
	@./scripts/deploy-service.sh $*

# Deploy all services
SERVICES := user order payment notification
deploy-all-services: $(SERVICES:%=deploy-%-service)
```

One pattern handles all services. Add new services without changing the Makefile.

\newpage
## Recursive Make for Multi-Project Orchestration

Coordinate multiple related projects:

```makefile
# Project structure:
# /
# ├── services/api/Makefile
# ├── services/frontend/Makefile
# └── infrastructure/Makefile

# Coordinate builds across projects
build-all: ## Build all projects
	@$(MAKE) -C services/api build
	@$(MAKE) -C services/frontend build
	@$(MAKE) -C infrastructure plan

# Test all projects
test-all: ## Test all projects
	@$(MAKE) -C services/api test
	@$(MAKE) -C services/frontend test

# Deploy in correct order
deploy-all: ## Deploy all projects
	@$(MAKE) -C infrastructure apply
	@sleep 10  # Wait for infrastructure
	@$(MAKE) -C services/api deploy
	@$(MAKE) -C services/frontend deploy
```

Simple orchestration across projects. Each project has its own Makefile.

\newpage
### Parallel Execution

Execute independent projects in parallel:

```makefile
SERVICES := services/api services/frontend services/worker

# Build services in parallel
build-services: ## Build all services in parallel
	@$(MAKE) -j3 $(SERVICES:%=build-%)

# Pattern for individual services
build-%:
	@$(MAKE) -C $* build

# Sequential deployment (infrastructure first)
deploy-orchestrated: ## Deploy with sequencing
	@$(MAKE) -C infrastructure apply
	@sleep 30
	@$(MAKE) -j3 $(SERVICES:%=deploy-%)
```

Use `-j` flag for parallel execution where safe.

\newpage
## Integration with External Tools

Integrate with APIs and external services:

```makefile
# Notify deployment via API
notify-start: ## Notify deployment start
	@curl -X POST $(WEBHOOK_URL)/deployment/start \
		-d '{"app":"$(APP_NAME)","version":"$(VERSION)"}' \
		|| echo "Failed to notify"

notify-complete: ## Notify deployment complete
	@curl -X POST $(WEBHOOK_URL)/deployment/complete \
		-d '{"app":"$(APP_NAME)","version":"$(VERSION)"}' \
		|| echo "Failed to notify"

# Deploy with notifications
deploy-with-api: notify-start deploy notify-complete
```

Integration adds observability without complicating core workflows.

\newpage
### Cloud Provider Integration

Fetch configuration from cloud services:

```makefile
# Fetch secrets from AWS
fetch-aws-secrets: ## Fetch secrets from AWS
	@aws secretsmanager get-secret-value \
		--secret-id $(APP_NAME)-secrets \
		--query SecretString --output text > .secrets

# Fetch secrets from GCP
fetch-gcp-secrets: ## Fetch secrets from GCP
	@gcloud secrets versions access latest \
		--secret=$(APP_NAME)-secrets > .secrets

# Deploy with cloud secrets
deploy-cloud: fetch-$(CLOUD)-secrets deploy
```

Abstract cloud provider differences behind consistent interfaces.

\newpage
## Conditional Execution Based on System State

Execute different workflows based on current state:

```makefile
# Detect deployment state
detect-state: ## Detect current deployment state
	@./scripts/detect-deployment-state.sh

# Deploy based on state
deploy-smart: ## Deploy based on current state
	@STATE=$$($(MAKE) -s detect-state); \
	case $$STATE in \
		fresh) $(MAKE) deploy-fresh ;; \
		scaled-down) $(MAKE) deploy-scale-up ;; \
		unhealthy) $(MAKE) deploy-heal ;; \
		healthy) $(MAKE) deploy-update ;; \
	esac

deploy-fresh:
	@./scripts/deploy-fresh.sh

deploy-update:
	@./scripts/deploy-update.sh
```

Workflows adapt to system state automatically.

\newpage
## Robust Shell Configuration and Error Handling

DevOps workflows fail in production for predictable reasons: a command in the
middle of a deployment script fails silently, environment variables don't
persist between commands, or a script that worked on your laptop breaks in CI
because of different shell behavior. These aren't exotic edge cases—they're the
daily reality of operational automation.

Make executes each line of a target in a separate shell by default. This
isolation protects you from side effects but creates problems when your workflow
needs commands to work together:

```makefile
# This doesn't work as expected
deploy-broken:
	cd infrastructure/
	terraform apply  # Runs in original directory, not infrastructure/
```

The `cd` command executes in one shell, which exits. The `terraform` command
runs in a new shell, back in the original directory. Your deployment fails and
you don't understand why.

Similarly, Make continues executing after non-critical failures by default:

```makefile
# Silent failures
deploy-database:
	./scripts/backup-db.sh      # Might fail silently
	./scripts/migrate-schema.sh # Runs anyway
	./scripts/deploy-db.sh      # Deploys broken schema
```

If the backup fails but returns exit code 0, or if you don't check its return
code, the deployment continues with no backup. Production data loss becomes
possible.

Make's shell configuration directives solve these problems by changing how
targets execute. The key is knowing when the default behavior helps you and
when it hurts you.

\newpage
### Understanding Make's Default Shell Behavior

Make's default shell execution has specific characteristics that affect
reliability:

```makefile
# Make's default behavior (implicit):
# .SHELL := /bin/sh
# Each line runs in separate subshell
# Lines with errors stop that target but exit code may vary

standard-target:
	echo "Line 1" # Shell process 1
	echo "Line 2" # Shell process 2
	echo "Line 3" # Shell process 3
```

Each line spawns a new shell process. This isolation means:

- **Variables don't persist**: `VAR=value` on one line doesn't affect the next
- **Directory changes don't persist**: `cd` commands have no effect on
subsequent lines
- **Pipelines can hide failures**: `command1 | command2` reports only the last
command's exit code

For simple targets, this behavior is fine. For complex DevOps workflows, it
causes subtle failures.

\newpage
### The .ONESHELL Directive

`.ONESHELL` runs all lines of a target in a single shell session:

```makefile
.ONESHELL:

# Now this works
deploy-with-context:
	cd infrastructure/
	export TF_VAR_env=production
	terraform apply
	cd ..

# All four commands run in the same shell
# Variables persist, directory changes persist
```

Benefits for DevOps workflows:

- **Environment setup persists**: Export variables once, use them throughout
- **Directory context maintained**: Navigate into subdirectories naturally
- **Complex sequences simplified**: Multi-step operations read linearly

The tradeoff: if one line fails, Make might not stop the target immediately
unless you configure error handling explicitly.

\newpage
### Advanced .SHELLFLAGS Configuration

`.SHELLFLAGS` controls which flags Make passes to the shell. The default is
`-c`, meaning "execute the following string as a command." For robust DevOps
workflows, add flags that catch errors early:

```makefile
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

deploy-safe:
	cd infrastructure/
	terraform plan
	terraform apply
```

Each flag provides specific protection:

- **`-e`**: Exit immediately if any command fails (errexit)
- **`-u`**: Treat unset variables as errors (nounset)
- **`-o pipefail`**: Fail if any command in a pipeline fails

The `-c` at the end tells the shell to execute what follows as a command (this
is Make's requirement).

\newpage
#### Why Each Flag Matters

**`-e` (errexit)**: Without this, commands continue after failures:

```makefile
# Without -e
deploy-dangerous:
	./scripts/backup.sh      # Fails, but execution continues
	./scripts/destructive-migration.sh  # Runs anyway!

# With .SHELLFLAGS := -e -c
.ONESHELL:
.SHELLFLAGS := -e -c

deploy-safe:
	./scripts/backup.sh      # If this fails, target stops
	./scripts/destructive-migration.sh  # Never runs
```

**`-u` (nounset)**: Catches typos and undefined variables:

```makefile
# Without -u, typos fail silently
deploy-with-typo:
	./scripts/deploy.sh $(ENVIRONMNT)  # Typo! Passes empty string

# With -u, Make stops and reports the error
.SHELLFLAGS := -eu -c

deploy-catches-typos:
	./scripts/deploy.sh $(ENVIRONMNT)  # Error: ENVIRONMNT unbound
```
\newpage
**`-o pipefail`**: Pipelines hide failures without this flag:

```makefile
# Without pipefail
check-broken:
	grep "ERROR" app.log | wc -l  # grep fails, but wc succeeds
	                               # Target reports success!

# With pipefail
.SHELLFLAGS := -eo pipefail -c

check-correct:
	grep "ERROR" app.log | wc -l  # grep failure stops target
```

### Handling Expected Non-Zero Exit Codes

Strict error handling breaks commands that legitimately return non-zero:

```makefile
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

# grep returns 1 when no matches found
check-errors:
	grep "ERROR" app.log || echo "No errors found"
	# The || operator handles the expected failure
```

Common patterns for expected failures:

```makefile
# Pattern 1: Provide alternative
check-logs:
	grep "CRITICAL" logs/*.log || echo "No critical errors"

# Pattern 2: Explicitly allow failure
check-optional:
	- ./scripts/optional-check.sh  # Prefix with - to allow failure

# Pattern 3: Test the exit code
check-conditional:
	if grep -q "ERROR" app.log; then \
		echo "Errors found"; \
		exit 1; \
	fi
```

The `-` prefix tells Make to ignore the exit code for that specific line, even
with `-e` enabled.

\newpage
### Adding a DEBUG Flag

DevOps workflows need visibility during development and troubleshooting. A DEBUG
flag adds shell tracing without modifying target code:

```makefile
DEBUG ?= 0

.ONESHELL:
ifeq ($(DEBUG),1)
	.SHELLFLAGS := -xeuo pipefail -c
else
	.SHELLFLAGS := -euo pipefail -c
endif

deploy-api:
	./scripts/health-check.sh
	./scripts/deploy.sh api
	./scripts/verify.sh
```

The `-x` flag prints each command before executing it:

```bash
# Normal execution
$ make deploy-api
Checking health...
Deploying API...
Verifying deployment...

# Debug mode shows every command
$ make DEBUG=1 deploy-api
+ ./scripts/health-check.sh
Checking health...
+ ./scripts/deploy.sh api
Deploying API...
+ ./scripts/verify.sh
Verifying deployment...
```

This visibility helps debug CI failures where you can't easily add `echo`
statements. You see exactly which command failed and what preceded it.

\newpage
### Conditional Debug Configuration

More sophisticated projects use conditional configuration:

```makefile
DEBUG ?= 0
VERBOSE ?= 0

.ONESHELL:
ifeq ($(DEBUG),1)
	.SHELLFLAGS := -xeuo pipefail -c
else ifeq ($(VERBOSE),1)
	.SHELLFLAGS := -veuo pipefail -c
else
	.SHELLFLAGS := -euo pipefail -c
endif
```

The `-v` flag prints lines as read (before variable expansion), while `-x`
prints commands as executed (after expansion). Use `-v` for build debugging,
`-x` for runtime debugging.

\newpage
### Real-World Example: Database Migration

Here's how these configurations solve a common DevOps scenario:

```makefile
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

DB_BACKUP_DIR := /backups/$(shell date +%Y%m%d)

migrate-database: ## Migrate database with safety checks
	echo "Starting migration for $(DB_NAME)"
	mkdir -p $(DB_BACKUP_DIR)
	./scripts/backup-db.sh $(DB_NAME) $(DB_BACKUP_DIR)
	./scripts/verify-backup.sh $(DB_BACKUP_DIR)
	./scripts/run-migrations.sh $(DB_NAME)
	./scripts/verify-migrations.sh $(DB_NAME)
	echo "Migration complete"
```

What this configuration guarantees:

- If `DB_NAME` isn't set, the target fails immediately (`-u`)
- If backup fails, migrations never run (`-e`)
- If backup verification fails, migrations never run (`-e`)
- All commands run in the same shell context (`.ONESHELL`)
- The backup directory path is consistent throughout

Without these configurations, any step could fail silently, and you'd migrate
production with no valid backup.

\newpage
### Real-World Example: Multi-Environment Deploy

Configuration management across environments benefits from strict shell
handling:

```makefile
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

REQUIRED_VARS := AWS_REGION CLUSTER_NAME APP_VERSION

deploy-%: ## Deploy to specified environment
	echo "Deploying to $* environment"
	$(foreach var,$(REQUIRED_VARS),\
		test -n "$($(var))" || \
		(echo "Error: $(var) not set" && exit 1);)
	./scripts/configure-$*.sh
	./scripts/deploy.sh $*
	./scripts/health-check.sh $* || \
		(echo "Deployment unhealthy, rolling back" && \
		 ./scripts/rollback.sh $* && exit 1)
```

The strict flags ensure:

- All required variables must be set before deployment starts
- Configuration must succeed before deploy runs
- Health check failure triggers automatic rollback
- Any unexpected error stops the deployment immediately

\newpage
### Pitfalls and Workarounds

Strict shell configuration changes behavior that some commands rely on:

#### Problem: grep Returns 1 When No Match

```makefile
.SHELLFLAGS := -e -c

# This fails if no errors exist
check-errors:
	grep "ERROR" app.log  # Returns 1 if no matches, stops target
```

**Solution**: Handle the expected exit code:

```makefile
check-errors:
	grep "ERROR" app.log || true  # Continue if no matches
	# Or provide meaningful output:
	grep "ERROR" app.log || echo "No errors found"
```

#### Problem: Commands with Intentional Non-Zero Exits

Some tools return different exit codes for different conditions:

```makefile
# diff returns 0 if identical, 1 if different, 2 if error
check-config-drift:
	- diff config.yaml deployed-config.yaml  # Allow 1, but not 2
```

**Better solution**: Test the exit code explicitly:

```makefile
check-config-drift:
	if diff config.yaml deployed-config.yaml > /dev/null; then \
		echo "No configuration drift"; \
	else \
		exit_code=$$?; \
		if [ $$exit_code -eq 1 ]; then \
			echo "Configuration has drifted"; \
			exit 1; \
		else \
			echo "Error comparing configs"; \
			exit 2; \
		fi; \
	fi
```

\newpage
### When to Use Strict Shell Configuration

Use `.ONESHELL` and strict `.SHELLFLAGS` when:

- **Multi-step operations need shared context**: Database migrations, deployment
sequences, infrastructure provisioning
- **Errors must halt immediately**: Production deployments, destructive
operations, data migrations
- **Variable typos could cause silent failures**: Configuration management,
environment-specific deployments
- **Pipeline failures matter**: Log analysis, data processing, backup
verification

**Don't use strict configuration for**:

- **Simple, independent commands**: Building artifacts, running tests, basic
checks
- **Targets that intentionally continue after failures**: Cleanup operations,
best-effort notifications
- **Compatibility with varied environments**: Shared Makefiles across teams with
different shells

### Configuration Scope

Apply strict configurations selectively:

```makefile
# Strict configuration for production targets
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

deploy-prod: strict-deploy-prod

strict-deploy-prod:
	./scripts/deploy.sh production

# Reset for development targets
.SHELLFLAGS := -c

deploy-dev:
	./scripts/deploy.sh dev || echo "Dev deploy failed, continuing"
```

This pattern gives you safety where it matters and flexibility where you need
it.

\newpage
### Summary: Building Reliability Into Your Workflows

Shell configuration directives transform Make from a simple task runner into a
robust execution environment for critical DevOps operations. The defaults work
for basic automation. Advanced configurations prevent the silent failures that
cause production incidents.

**Key techniques**:

- **`.ONESHELL`**: Runs target commands in one shell, preserving context
- **`.SHELLFLAGS := -euo pipefail -c`**: Strict error handling that catches
failures early
  - `-e`: Stop on any error
  - `-u`: Treat undefined variables as errors
  - `-o pipefail`: Catch pipeline failures
  - `-c`: Execute command (Make requirement)
- **`DEBUG` flag**: Add `-x` for command tracing during troubleshooting
- **Explicit exit code handling**: Use `|| true` or `- command` for expected
non-zero exits

The discipline: apply strict configurations to targets where failures have real
consequences—deployments, migrations, production operations. Keep simple targets
simple. Let the importance of the operation dictate the complexity of its error
handling.

The result: workflows that fail fast with clear error messages rather than
continuing with corrupt state. That's the difference between an incident you
catch in staging and one that wakes you up at 3 AM.
\newpage
### Git-Based Conditional Execution

Different actions for different branches:

```makefile
# Deploy based on branch
deploy-by-branch: ## Deploy based on Git branch
	@BRANCH=$$(git rev-parse --abbrev-ref HEAD); \
	case $$BRANCH in \
		main) $(MAKE) deploy-prod ;; \
		develop) $(MAKE) deploy-staging ;; \
		feature/*) $(MAKE) deploy-dev ;; \
	esac

# Ensure working directory is clean
check-git-clean: ## Ensure clean working directory
	@git diff --quiet || \
		(echo "Uncommitted changes" && exit 1)
```

Git state influences workflow decisions.

\newpage
## Creating Extensible Frameworks

Build frameworks teams can customize:

```makefile
# Core framework with hooks
framework-build: ## Framework: build with hooks
	@$(MAKE) pre-build-hooks
	@./scripts/core-build.sh
	@$(MAKE) post-build-hooks

framework-deploy: ## Framework: deploy with hooks
	@$(MAKE) pre-deploy-hooks
	@./scripts/core-deploy.sh
	@$(MAKE) post-deploy-hooks

# Hook system - teams define these
pre-build-hooks:
	@./scripts/run-hooks.sh pre-build

post-build-hooks:
	@./scripts/run-hooks.sh post-build

# Example: teams put scripts in hooks/pre-build/
# hooks/
# ├── pre-build/
# │   ├── lint.sh
# │   └── security-scan.sh
# └── post-build/
#     └── notify.sh
```

Framework provides structure, teams add customization through hooks.

\newpage
### Configuration-Driven Workflows

Adapt based on configuration files:

```makefile
# Load configuration
load-config: ## Load workflow configuration
	@./scripts/load-config.sh

# Execute workflow based on config
execute-workflow: load-config ## Execute configured workflow
	@WORKFLOW=$$(./scripts/get-workflow-type.sh); \
	case $$WORKFLOW in \
		standard) $(MAKE) workflow-standard ;; \
		canary) $(MAKE) workflow-canary ;; \
		blue-green) $(MAKE) workflow-blue-green ;; \
	esac

workflow-standard:
	@./scripts/workflow-standard.sh

workflow-canary:
	@./scripts/workflow-canary.sh
```

Configuration determines workflow without changing the Makefile.

\newpage
### Reusable Components with Functions

Functions encapsulate repetitive command sequences into reusable blocks. When you find yourself copying the same multi-line command pattern across targets, functions eliminate the duplication while keeping the logic in one maintainable location.

Make functions use `define` and `endef` to wrap commands, accept parameters through `$(1)`, `$(2)`, etc., and get invoked with `$(call function_name,arg1,arg2)`.

Start with a simple example:

```makefile
# Function for consistent logging
define log_message
	@echo "[$(shell date +'%Y-%m-%d %H:%M:%S')] $(1)"
endef

deploy-api:
	$(call log_message,Starting API deployment)
	@./scripts/deploy-api.sh
	$(call log_message,API deployment complete)
```

The `$(1)` represents the first argument passed to the function. Simple functions like this standardize output formatting across all targets without repeating date formatting logic.

\newpage
#### Standardizing Repetitive Notifications

DevOps workflows need consistent notifications. Functions centralize the notification logic:

```makefile
# Function for cleanup reminders
define cleanup_reminder
	@echo "⚠️  Remember to run 'make cleanup-$(1)' after testing"
	@echo "   Temporary $(1) resources will persist until cleaned up"
endef

deploy-test-db:
	@./scripts/deploy-test-database.sh
	$(call cleanup_reminder,database)

deploy-test-cache:
	@./scripts/deploy-test-cache.sh
	$(call cleanup_reminder,cache)

# Cleanup targets
cleanup-database:
	@./scripts/cleanup-test-database.sh

cleanup-cache:
	@./scripts/cleanup-test-cache.sh
```

Before functions, each target repeated the notification text. Functions ensure consistent messaging and make updates happen in one place.

\newpage
#### Environment Configuration Pattern

Setting up environment context involves repetitive checks and configuration:

```makefile
# Before: Repetitive environment setup
deploy-api-dev:
	@echo "Deploying API to dev..."
	@[ -f .env.dev ] || (echo "Missing .env.dev" && exit 1)
	@export ENV=dev && ./scripts/deploy-api.sh

deploy-worker-dev:
	@echo "Deploying worker to dev..."
	@[ -f .env.dev ] || (echo "Missing .env.dev" && exit 1)
	@export ENV=dev && ./scripts/deploy-worker.sh

# After: Function handles the pattern
define deploy_service
	@echo "Deploying $(1) to $(2)..."
	@[ -f .env.$(2) ] || (echo "Missing .env.$(2)" && exit 1)
	@export ENV=$(2) && ./scripts/deploy-$(1).sh
endef

deploy-api-dev:
	$(call deploy_service,api,dev)

deploy-worker-dev:
	$(call deploy_service,worker,dev)

deploy-api-staging:
	$(call deploy_service,api,staging)
```

The function handles environment file validation and service deployment with two parameters: service name `$(1)` and environment `$(2)`. Changes to deployment logic happen once, not in every target.

\newpage
#### Multi-Step Operations with Error Handling

Complex operations benefit from centralized error handling:

```makefile
# Function for safe deployment steps
define safe_deploy
	@echo "==> Deploying $(1) to $(2)"
	@./scripts/health-check.sh $(2) || \
		(echo "Environment $(2) unhealthy, aborting" && exit 1)
	@./scripts/deploy.sh $(1) $(2) || \
		(echo "Deployment failed, rolling back" && \
		 ./scripts/rollback.sh $(1) $(2) && exit 1)
	@./scripts/verify-deployment.sh $(1) $(2)
	@echo "✓ $(1) deployed successfully to $(2)"
endef

deploy-api-prod:
	$(call safe_deploy,api,prod)

deploy-frontend-prod:
	$(call safe_deploy,frontend,prod)
```

Health checks, deployment, rollback logic, and verification exist in one function. Every service gets the same safety guarantees without duplicating the error handling code.

\newpage
#### Framework Integration with Functions

Functions shine in extensible frameworks where teams need consistent patterns:

```makefile
# Core framework function for service lifecycle
define service_lifecycle
	@echo "===> Service Lifecycle: $(1)"
	@./scripts/pre-deploy-hooks.sh $(1)
	@./scripts/deploy-service.sh $(1) $(2)
	@./scripts/post-deploy-hooks.sh $(1)
	@./scripts/health-check.sh $(1) $(2) || \
		(echo "Health check failed" && exit 1)
endef

# Teams use the framework consistently
deploy-user-service:
	$(call service_lifecycle,user-service,production)

deploy-order-service:
	$(call service_lifecycle,order-service,production)

# Framework evolution happens in the function
# Teams don't change individual targets
```

Framework functions let you evolve deployment patterns without touching every target. Add monitoring, change health check logic, or enhance error handling in one place.

\newpage
#### When to Use Functions

Use functions when you have:

- **Identical multi-line sequences** appearing in 3+ targets
- **Consistent error handling** patterns across workflows
- **Standard notification or logging** requirements
- **Repetitive validation or setup** steps

Avoid functions when:

- **Single-line commands** work fine (use variables instead)
- **Logic differs significantly** between targets (use separate targets)
- **Only used once** (inline the commands directly)
- **Team unfamiliar with Make functions** (simpler approaches exist)

Functions add a layer of indirection. Teams need to understand `$(call ...)` syntax and find function definitions to understand what targets do. Use functions when duplication pain exceeds learning curve pain.

The right balance: functions for framework code that many teams use, simple targets for team-specific workflows. Functions become infrastructure—stable, well-tested, and trusted by everyone.

\newpage
## Key Takeaways

Make's advanced features solve the DevOps multiplicity problem—managing many
environments, services, and strategies without drowning in duplication or hiding
logic in opaque scripts.

### The Tools:
1. **Pattern Rules**: Eliminate repetition with `%` wildcards
2. **Recursive Make**: Coordinate multiple projects
3. **External Integration**: Connect to APIs and cloud services
4. **Conditional Execution**: Adapt to system state
5. **Extensible Frameworks**: Build customizable systems
6. **Functions**: Encapsulate multi-line sequences with `define/endef` and `$(call)`

### The Discipline:
Use these features when they solve real problems:

- Pattern rules when you have 3+ similar targets
- Recursive Make when coordinating multiple projects
- Conditionals when workflows need to adapt
- Frameworks when standardizing across teams
- Functions when command sequences repeat across targets

Don't use advanced features for their own sake. Simple, clear Makefiles beat clever, complex ones unless complexity solves a real problem.

\newpage
### The Payoff:
Advanced features turn duplication into abstraction without sacrificing
visibility. Pattern rules let you write `deploy-%` once instead of copying
`deploy-dev`, `deploy-staging`, and `deploy-prod`. Functions encapsulate your standard
health-check-deploy-verify sequence so improvements propagate automatically.
Recursive Make coordinates five microservices without a 200-line orchestration
script.

The real power: these features compress your Makefile's *size* while expanding its
*capability*. A 50-line Makefile with pattern rules can handle twelve
environments. A well-placed function eliminates 300 lines of duplication. This
compression means fewer places for bugs to hide and fewer targets to update when
requirements change.

Advanced features let you encode your operational patterns directly in Make's
syntax. The result is automation that scales as your infrastructure grows,
without the Makefile growing proportionally.
