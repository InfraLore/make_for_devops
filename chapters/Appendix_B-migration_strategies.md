# Appendix B - Migration Strategies

This appendix provides step-by-step guides for migrating existing workflows to
Make-based approaches. Each strategy addresses a common starting point and
provides a gradual, low-risk path to adoption.

The central theme: **Make doesn't replace your tools—it makes them
discoverable.** And in making them discoverable, you often improve them too.

## General Migration Principles

**Make Orchestrates, Doesn't Replace**: Your existing scripts, tools, and
processes stay. Make provides a discoverable interface to them. But as you build
that interface, you'll naturally improve the underlying scripts.

**Start Small**: Begin with high-value, low-risk targets (like `help`, `test`,
`build`).

**Look for what devs do all the time**: Identify common tasks that developers
perform frequently, such as starting development environments, running tests,
building artifacts, or deploying applications. Create Make targets for these
tasks first. This is where most of the friction is, so this is wher you need to
add oil.

**Run in Parallel**: Keep existing workflows while introducing Make targets.
Validate they produce identical results before switching.

**Document Through Doing**: Each Make target becomes executable documentation.
If someone asks "how do I deploy?", the answer is `make deploy`.

**Improve as You Wrap**: When you add a Make target for a script, you'll notice
missing features (like verbose flags or better error messages). Fix them in the
script, not in Make.

**Get Feedback Early**: Involve the team from day one. They'll tell you which
workflows matter most.

---

## Migration 1: From README Instructions to Executable Targets

**Starting Point**: Traditional README with manual setup instructions that
developers follow (or forget) step by step.

**Goal**: Create executable `make setup` and `make dev` targets that encode
those steps.

**Why This Matters**: README instructions go stale, get skipped, and vary by
developer. Executable targets ensure everyone runs the same setup and can start
contributing immediately.

### Current State: The 10-Step README

Here's what developers face today:

```markdown
## Setup
1. Install Node.js 18+
2. Install Python 3.9+
3. Run `npm install`
4. Run `pip install -r requirements.txt`
5. Copy `.env.example` to `.env`
6. Edit `.env` with your configuration
7. Run database migrations: `python manage.py migrate`
8. Start the database: `docker run -d postgres:14`
9. Start the API: `python app.py`
10. In another terminal, start the frontend: `npm start`
```

**The problem**: New developers spend 30-60 minutes on setup. They miss steps,
run them out of order, or use wrong versions. Senior developers answer the same
"how do I set this up?" questions monthly.

### Step 1: Create a Help Target

Start with the most valuable target of all—showing what's available:

```makefile
.DEFAULT_GOAL := help

help: ## Show available commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'
```

**What this does**: When someone runs `make` with no arguments, this target
searches the Makefile for any line matching the pattern `target: ## description`
and formats it nicely.

**Why it matters**: Developers can type `make` and immediately see what's
possible. No digging through README files or asking in Slack.

Try it now - even with just this one target, running `make` shows:

```
help            Show available commands
```

As you add more targets with `##` comments, they automatically appear in the
help output.

### Step 2: Create Prerequisites Check

Start your setup target by checking what's already installed:

```makefile
setup: ## Set up development environment (run once)
	@echo "Checking prerequisites..."
	@command -v node >/dev/null \
	|| (echo "❌ Node.js required. Install from nodejs.org" && exit 1)
	@echo "✓ Node.js found"
```

**Breaking this down**:

- `@echo` prints a message (the `@` prevents Make from also printing the command itself)
- `command -v node` checks if `node` is in your PATH
- `>/dev/null` throws away the output (we only care if it succeeds or fails)
- `||` means "or" - if the previous command failed, run the next part
- `exit 1` stops the entire target immediately

**Why check prerequisites first**: Fail fast with a clear message. Better to see
"Node.js required" immediately than to get cryptic errors 3 steps later when
`npm install` fails.

Now add checks for the other prerequisites:

```makefile
setup: ## Set up development environment (run once)
	@echo "Checking prerequisites..."
	@command -v node >/dev/null \
	|| (echo "❌ Node.js required. Install from nodejs.org" && exit 1)
	@command -v python3 >/dev/null \
	|| (echo "❌ Python 3 required" && exit 1)
	@command -v docker >/dev/null \
	|| (echo "❌ Docker required" && exit 1)
	@echo "✓ All prerequisites found"
```

**Pattern recognition**: Notice the repetition? You could extract this to a
helper function, but for migration start simple. Optimize later when patterns
become clearer.

### Step 3: Add Dependency Installation

Now install the dependencies:

```makefile
setup: ## Set up development environment (run once)
	@echo "Checking prerequisites..."
	@command -v node >/dev/null \
	|| (echo "❌ Node.js required. Install from nodejs.org" && exit 1)
	@command -v python3 >/dev/null \
	|| (echo "❌ Python 3 required" && exit 1)
	@command -v docker >/dev/null \
	|| (echo "❌ Docker required" && exit 1)
	@echo "✓ All prerequisites found"
	@echo ""
	@echo "Installing dependencies..."
	@npm install --silent
	@pip install -r requirements.txt --quiet
	@echo "✓ Dependencies installed"
```

**About those flags**: The `--silent` and `--quiet` flags reduce noise. You'll
still see errors if something fails - these just hide the routine "installing
package X..." messages.

**Learning moment**: If npm or pip didn't have these flags, this would be
harder. When wrapping tools with Make, you discover which flags you need. This
often drives improvements to the underlying tools.

### Step 4: Add Configuration Setup

Finally, handle the configuration file:

```makefile
setup: ## Set up development environment (run once)
	@echo "Checking prerequisites..."
	@command -v node >/dev/null \
	|| (echo "❌ Node.js required. Install from nodejs.org" && exit 1)
	@command -v python3 >/dev/null \
	|| (echo "❌ Python 3 required" && exit 1)
	@command -v docker >/dev/null \
	|| (echo "❌ Docker required" && exit 1)
	@echo "✓ All prerequisites found"
	@echo ""
	@echo "Installing dependencies..."
	@npm install --silent
	@pip install -r requirements.txt --quiet
	@echo "✓ Dependencies installed"
	@echo ""
	@echo "Setting up configuration..."
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✓ Created .env - edit with your settings"; \
	else \
		echo "✓ .env already exists"; \
	fi
	@echo ""
	@echo "Setup complete! Edit .env, then run 'make dev'"
```

**The idempotency check**: `[ ! -f .env ]` tests "if .env file does NOT exist".
This means running `make setup` twice is safe - it won't overwrite your
configured `.env` file.

**Why the backslashes**: The `\` at the end of lines inside the `if` statement
tells Make "this command continues on the next line." Without them, Make would
try to run each line as a separate shell command.

**Current payoff**: Steps 1-6 of the original README are now `make setup`. One
command, with validation, clear feedback, and idempotency.

### Step 5: Add Development Target - Database First

Now tackle the development workflow. Start with just the database:

```makefile
dev: ## Start development environment
	@echo "Starting development environment..."
	@echo ""
	@echo "Starting database..."
	@docker run -d --name myapp-db \
		-e POSTGRES_DB=myapp \
		-e POSTGRES_PASSWORD=dev \
		-p 5432:5432 \
		postgres:14 2>/dev/null || true
	@echo "✓ Database starting"
```

**What's that `|| true` doing?**: If the container already exists, `docker run`
will fail. The `|| true` means "or just succeed anyway." We check if it's
actually running next.

Now check if the database is actually ready:

```makefile
dev: ## Start development environment
	@echo "Starting development environment..."
	@echo ""
	@echo "Starting database..."
	@docker run -d --name myapp-db \
		-e POSTGRES_DB=myapp \
		-e POSTGRES_PASSWORD=dev \
		-p 5432:5432 \
		postgres:14 2>/dev/null || true
	@echo "Waiting for database to be ready..."
	@for i in 1 2 3 4 5; do \
		docker exec myapp-db pg_isready -q && break || sleep 1; \
	done
	@echo "✓ Database ready"
```

**The retry loop**: Try `pg_isready` up to 5 times, sleeping 1 second between
attempts. This handles the common problem where the container starts but
Postgres isn't accepting connections yet.

**Better approach**: You might notice this is clumsy. A better solution: create
a `scripts/wait-for-db.sh` script that does proper health checking with better
error messages. The Make target would call it: `@./scripts/wait-for-db.sh`. This
is Make driving script improvements.

### Step 6: Add Migrations

With the database ready, run migrations:

```makefile
dev: ## Start development environment
	@echo "Starting development environment..."
	@echo ""
	@echo "Starting database..."
	@docker run -d --name myapp-db \
		-e POSTGRES_DB=myapp \
		-e POSTGRES_PASSWORD=dev \
		-p 5432:5432 \
		postgres:14 2>/dev/null || true
	@echo "Waiting for database to be ready..."
	@for i in 1 2 3 4 5; do \
		docker exec myapp-db pg_isready -q && break || sleep 1; \
	done
	@echo "✓ Database ready"
	@echo ""
	@echo "Running migrations..."
	@python manage.py migrate --no-input
	@echo "✓ Migrations complete"
```

**The `--no-input` flag**: Prevents Django from asking for confirmation. In an
automated workflow, you want non-interactive commands.

**Script improvement opportunity**: If `manage.py migrate` doesn't have a
`--quiet` flag, this is your signal to add one. Make targets should have clean
output - verbose details only when things fail.

### Step 7: Start Application Services

Finally, start both the API and frontend:

```makefile
dev: ## Start development environment
	@echo "Starting development environment..."
	@echo ""
	@echo "Starting database..."
	@docker run -d --name myapp-db \
		-e POSTGRES_DB=myapp \
		-e POSTGRES_PASSWORD=dev \
		-p 5432:5432 \
		postgres:14 2>/dev/null || true
	@echo "Waiting for database to be ready..."
	@for i in 1 2 3 4 5; do \
		docker exec myapp-db pg_isready -q && break || sleep 1; \
	done
	@echo "✓ Database ready"
	@echo ""
	@echo "Running migrations..."
	@python manage.py migrate --no-input
	@echo "✓ Migrations complete"
	@echo ""
	@echo "Starting services (Ctrl+C to stop all)..."
	@trap 'kill %1 %2 2>/dev/null' INT; \
		python app.py & \
		npm start & \
		wait
```

**Process management explained**:

- `trap 'kill %1 %2' INT` sets up a handler for Ctrl+C (INT signal)
- `python app.py &` starts the API in the background (`&` means background)
- `npm start &` starts the frontend in the background
- `wait` waits for both background processes
- When you hit Ctrl+C, the trap kills both processes (`%1` and `%2` refer to the
  background jobs)

**Why this matters**: Without the trap, Ctrl+C would leave orphan processes
running. The Make target handles cleanup automatically.

### Step 8: Update README

Now drastically simplify your README:

```markdown
## Quick Start

```bash
make setup    # One-time setup
# Edit .env with your settings
make dev      # Start everything
```

That's it! For all available commands, run `make help`.

## What Just Happened?

- `make setup` checked prerequisites, installed dependencies, and created `.env`
- `make dev` started the database, ran migrations, and launched the API and
  frontend
- Press Ctrl+C to stop all services

## Manual Setup

If you prefer manual setup, see [docs/manual-setup.md](docs/manual-setup.md).
```

**The transformation**: 10 manual steps became 2 commands. More importantly, the
steps are now *validated*, *idempotent*, and *discoverable*.

### What You'll Notice Next

After your team uses this for a week, you'll hear:

- "Can we add `make clean` to reset everything?"
- "The database logs are noisy, can we suppress them?"
- "I want to run just the frontend, not the whole stack"

These requests drive your next targets. Don't predict what people will want -
let usage guide you.

---

## Migration 2: From Shell Scripts to Discoverable Workflows

**Starting Point**: Collection of bash scripts in `scripts/` directory that work
well but require team lore to use.

**Goal**: Make existing scripts discoverable and composable through Make targets
while improving the scripts themselves.

**Why This Matters**: Scripts in `scripts/` are invisible until someone tells
you about them. You don't know they exist, what they do, or when to use them.
Make solves discoverability. But as you wrap scripts, you'll discover missing
features—and that's when you improve the scripts.

### Current State: The Hidden Scripts

```bash
scripts/
├── deploy.sh           # Deploys to environment (but how?)
├── run-tests.sh        # Runs tests (all of them? unit? integration?)
├── build-docker.sh     # Builds Docker image (with what tag?)
├── backup-db.sh        # Backs up database (to where?)
└── cleanup.sh          # Cleans what, exactly?
```

**The problem**: Scripts exist but nobody knows:

- What arguments they take
- What they do exactly
- When to use them
- What their output means

### Step 1: Make Scripts Discoverable

Start by wrapping the simplest script:

```makefile
test: ## Run all tests
	@./scripts/run-tests.sh
```

Now `make help` shows this target exists. But you immediately notice a problem:
when tests fail, you get a wall of output. You want a quiet mode for CI and a
verbose mode for debugging.

**This is the insight**: You needed a `--quiet` and `--verbose` flag, but the
script doesn't have them. Time to improve the script.

Edit `scripts/run-tests.sh`:

```bash
#!/bin/bash
# Add flag handling to the script

VERBOSE=false
QUIET=false

while [[ $# -gt 0 ]]; do
  case $1 in
    -v|--verbose) VERBOSE=true; shift ;;
    -q|--quiet) QUIET=true; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Now use these flags in your test runs
if [ "$QUIET" = true ]; then
  pytest -q
elif [ "$VERBOSE" = true ]; then
  pytest -v
else
  pytest
fi
```

Now update the Make target to use these new flags:

```makefile
test: ## Run all tests
	@./scripts/run-tests.sh

test-verbose: ## Run tests with detailed output
	@./scripts/run-tests.sh --verbose

test-quiet: ## Run tests (minimal output)
	@./scripts/run-tests.sh --quiet
```

**What improved**: The script gained flexibility it didn't have before. Make
exposed the need. The script now works better both in Make *and* standalone.

### Step 2: Wrap Scripts That Need Validation

Now tackle the deploy script:

```makefile
deploy: ## Deploy to environment (ENVIRONMENT=dev|staging|prod)
	@./scripts/deploy.sh $(ENVIRONMENT)
```

Run this without an environment: `make deploy`

You get a confusing error from deep inside the script. The problem: the script
expects an argument but doesn't validate it at the top.

**Improve the script first**. Edit `scripts/deploy.sh`:

```bash
#!/bin/bash
set -euo pipefail  # Exit on errors, undefined variables, pipe failures

ENVIRONMENT=$1

# Validate at the top of the script
if [ -z "$ENVIRONMENT" ]; then
  echo "Usage: $0 <environment>"
  echo "Environment must be: dev, staging, or prod"
  exit 1
fi

if [[ ! "$ENVIRONMENT" =~ ^(dev|staging|prod)$ ]]; then
  echo "Error: Invalid environment '$ENVIRONMENT'"
  echo "Must be: dev, staging, or prod"
  exit 1
fi

echo "Deploying to $ENVIRONMENT..."
# ... rest of deployment logic
```

**What improved**:

- `set -euo pipefail` makes the script safer (fails on errors, undefined
  variables)
- Early validation with clear error messages
- The script is now safer whether called from Make or manually

Now the Make target can trust the script's validation:

```makefile
deploy: ## Deploy to environment (ENVIRONMENT=dev|staging|prod)
	@test -n "$(ENVIRONMENT)" \
	|| (echo "Usage: make deploy ENVIRONMENT=dev|staging|prod" && exit 1)
	@./scripts/deploy.sh $(ENVIRONMENT)
```

**Defense in depth**: Both Make and the script validate. If someone calls the
script directly, it still works correctly.

### Step 3: Add Debug Support

While testing deployments, you want to see what's happening. But the script
doesn't have a debug mode.

**Add it to the script**. Edit `scripts/deploy.sh`:

```bash
#!/bin/bash
set -euo pipefail

DEBUG=false
ENVIRONMENT=""

# Parse flags
while [[ $# -gt 0 ]]; do
  case $1 in
    --debug) DEBUG=true; shift ;;
    dev|staging|prod) ENVIRONMENT=$1; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [ "$DEBUG" = true ]; then
  set -x  # Print every command
fi

# Validation
if [ -z "$ENVIRONMENT" ]; then
  echo "Usage: $0 [--debug] <environment>"
  exit 1
fi

echo "Deploying to $ENVIRONMENT..."
# ... rest of deployment
```

Now add Make targets that use it:

```makefile
deploy: ## Deploy to environment (ENVIRONMENT=dev|staging|prod)
	@test -n "$(ENVIRONMENT)" \
	|| (echo "Usage: make deploy ENVIRONMENT=dev" && exit 1)
	@./scripts/deploy.sh $(ENVIRONMENT)

deploy-debug: ## Deploy with debug output (ENVIRONMENT=dev|staging|prod)
	@test -n "$(ENVIRONMENT)" \
	|| (echo "Usage: make deploy-debug ENVIRONMENT=dev" && exit 1)
	@./scripts/deploy.sh --debug $(ENVIRONMENT)
```

**Usage**:

```bash
make deploy ENVIRONMENT=staging           # Normal output
make deploy-debug ENVIRONMENT=staging     # See every command
```

**The pattern**: Make exposed the need for debug output. You added it to the
script. Now both Make users and script users benefit.

### Step 4: Add Safety Checks

Production deployments need extra safety. Add a confirmation step:

```makefile
deploy: _pre-deploy-checks ## Deploy to environment (ENVIRONMENT=dev|staging|prod)
	@test -n "$(ENVIRONMENT)" \
	|| (echo "Usage: make deploy ENVIRONMENT=dev" && exit 1)
	@$(MAKE) _confirm-deploy
	@./scripts/deploy.sh $(ENVIRONMENT)
	@echo "✓ Deployed to $(ENVIRONMENT)"

_pre-deploy-checks:
	@echo "Running pre-deployment checks..."
	@./scripts/run-tests.sh --quiet \
	|| (echo "❌ Tests must pass before deployment" && exit 1)
	@echo "✓ Tests passed"

_confirm-deploy:
	@if [ "$(ENVIRONMENT)" = "prod" ]; then \
		echo "⚠️  Deploying to PRODUCTION"; \
		echo -n "Type 'production' to confirm: "; \
		read ans && [ "$$ans" = "production" ] || exit 1; \
	fi
```

**What this adds**:

- Tests must pass before deployment
- Production deployments require explicit confirmation
- Helper targets use `_` prefix so they don't clutter `make help`

**Script improvement opportunity**: Maybe the deploy script should support a
`--skip-tests` flag for emergencies. Or a `--confirm` flag that prompts for
production. These improvements make the script better for everyone.

### Step 5: Add Convenience Aliases

Common operations should be easy to type:

```makefile
deploy-dev: ## Deploy to development
	@$(MAKE) deploy ENVIRONMENT=dev

deploy-staging: ## Deploy to staging
	@$(MAKE) deploy ENVIRONMENT=staging

deploy-prod: ## Deploy to production
	@$(MAKE) deploy ENVIRONMENT=prod

# Composite workflow
full-deploy: test build deploy-staging ## Complete staging deployment
	@echo "✓ Full staging deployment complete"
```

**Why aliases help**: `make deploy-dev` is easier than `make deploy
ENVIRONMENT=dev`. The full workflow composes three operations into one command.

**Note**: These call other Make targets, not scripts directly. The scripts stay
simple, Make handles orchestration.

### The Improvement Cycle

**What happened here**:

1. Wrapped scripts with Make targets
2. Discovered missing features (verbose flag, debug mode, validation)
3. Improved the scripts to add those features
4. Both Make users and script users benefited
5. Repeated as usage revealed more needs

**The key insight**: Make doesn't just wrap scripts—it reveals their gaps. When
you add `make test-verbose`, you discover the test script needs a verbose flag.
When you add `make deploy`, you discover it needs better validation. Fix these
in the scripts, and everyone benefits.

---

## Migration 3: From CI/CD Platform Config to Local Reproducibility

**Starting Point**: CI/CD logic embedded in `.gitlab-ci.yml` or
`.github/workflows/` that works in CI but can't be tested locally.

**Goal**: CI/CD files that call Make targets, making workflows locally reproducible.

**Why This Matters**: When CI fails, developers currently push commits to test
fixes. A 5-minute local test becomes a 20-minute CI round-trip. Making CI
workflows locally testable saves hours per week and builds confidence.

### Current State: Logic Locked in CI

Here's typical GitHub Actions config:

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    steps:
      - name: Build
        run: docker build -t myapp:${{ github.sha }} .

      - name: Test
        run: docker run myapp:${{ github.sha }} pytest

      - name: Push
        run: |
          docker tag myapp:${{ github.sha }} myapp:latest
          docker push myapp:${{ github.sha }}
          docker push myapp:latest
```

**The problem**: These commands only exist in the CI config. You can't run "what
CI runs" locally. When CI fails, you're debugging blind.

### Step 1: Extract Just the Build Step

Start by moving just the build logic:

```makefile
VERSION ?= $(shell git rev-parse --short HEAD)
IMAGE := myapp:$(VERSION)

build: ## Build Docker image
	@echo "Building $(IMAGE)..."
	@docker build -t $(IMAGE) .
	@echo "✓ Built $(IMAGE)"
```

**What's happening**:

- `VERSION ?=` sets a default value that can be overridden
- `git rev-parse --short HEAD` gets the current commit hash
- `IMAGE :=` combines the name and version

**Test it locally**:

```bash
make build          # Uses current git commit
make build VERSION=test-123  # Override for testing
```

Now update the CI config:

```yaml
- name: Build
  run: make build VERSION=${{ github.sha }}
```

**Immediate benefit**: You can now build locally exactly what CI builds. If the
build fails in CI, run `make build` locally to debug.

### Step 2: Add the Test Step

Extract test logic:

```makefile
test: ## Run tests in container
	@echo "Running tests..."
	@docker run --rm $(IMAGE) pytest
	@echo "✓ Tests passed"
```

**Problem discovered**: When tests fail, you get minimal output. You want
verbose test output.

**Improve the underlying command**:

```makefile
test: ## Run tests in container
	@echo "Running tests..."
	@docker run --rm $(IMAGE) pytest -v
	@echo "✓ Tests passed"

test-debug: ## Run tests with extra debugging
	@echo "Running tests in debug mode..."
	@docker run --rm -it $(IMAGE) pytest -vv --pdb
```

**What improved**: CI gets verbose output by default. Developers get
`test-debug` for local debugging with pdb (Python debugger). The underlying
Docker command got better.

Update CI:

```yaml
- name: Test
  run: make test
```

### Step 3: Handle CI-Specific Behavior

Some things should behave differently in CI vs locally:

```makefile
# Detect CI environment
ifdef CI
  DOCKER_BUILD_ARGS := --no-cache --progress=plain
  TEST_ARGS := --junit-xml=test-results.xml
else
  DOCKER_BUILD_ARGS :=
  TEST_ARGS :=
endif

build: ## Build Docker image
	@echo "Building $(IMAGE)..."
	@docker build $(DOCKER_BUILD_ARGS) -t $(IMAGE) .
	@echo "✓ Built $(IMAGE)"

test: ## Run tests in container
	@echo "Running tests..."
	@docker run --rm $(IMAGE) pytest -v $(TEST_ARGS)
	@echo "✓ Tests passed"
```

**What this does**:

- CI builds always use `--no-cache` (reproducible, no stale layers)
- CI tests generate JUnit XML (for test reporting dashboards)
- Local builds use cache (fast iteration)
- Local tests skip XML generation (you don't need it)

**The pattern**: The CI environment variable is set automatically by GitHub
Actions, GitLab CI, etc. Make detects it and adjusts.

### Step 4: Add Push and Deploy

Complete the pipeline:

```makefile
push: ## Push image to registry
	@echo "Pushing $(IMAGE)..."
	@docker tag $(IMAGE) myapp:latest
	@docker push $(IMAGE)
	@docker push myapp:latest
	@echo "✓ Pushed $(IMAGE)"

deploy: ## Deploy to Kubernetes
	@echo "Deploying $(IMAGE)..."
	@kubectl set image deployment/myapp app=$(IMAGE)
	@kubectl rollout status deployment/myapp
	@echo "✓ Deployed $(VERSION)"
```

**Local testing**:

```bash
make build           # Build the image
make test            # Run tests
# Push and deploy would work too if you have credentials
```

### Step 5: Create Complete Workflow

Compose individual steps into a full pipeline:

```makefile
ci: ## Run complete CI pipeline
	@echo "Running CI pipeline..."
	@$(MAKE) build
	@$(MAKE) test
	@$(MAKE) push
	@$(MAKE) deploy
	@echo "✓ CI pipeline complete"
```

Now the GitHub Actions config is trivial:

```yaml
jobs:
  deploy:
    steps:
      - name: Run CI Pipeline
        run: make ci VERSION=${{ github.sha }}
```

**The transformation**:

- **Before**: 20+ lines of CI config with Docker commands
- **After**: 1 line calling Make
- **Benefit**: Run `make ci` locally to test the full pipeline

### What You Discovered

As you extracted CI logic to Make, you probably discovered:

- Missing verbose flags in test commands
- Hardcoded values that should be variables
- Steps that could fail silently
- No way to test individual stages locally

**Fix these in the Makefile and the commands it calls**. Now improvements
benefit both CI and local development.

---

## Migration 4: From Multiple Tools to Unified Interface

**Starting Point**: Multiple tools (Terraform, Helm, kubectl, aws-cli) each with
different command patterns and argument styles.

**Goal**: Consistent Make interface across all tools, with improvements to the
tools' usage patterns.

**Why This Matters**: Developers shouldn't need to remember that Terraform uses
`-var-file`, Helm uses `-f`, and kubectl uses `--filename`. A consistent
interface reduces cognitive load. And as you build that interface, you'll
improve how you use these tools.

### Current State: Tool Chaos

```bash
# Terraform
cd terraform && terraform plan -var-file=staging.tfvars

# Helm  
helm upgrade myapp ./charts -f charts/values-staging.yaml

# kubectl
kubectl apply -f k8s/staging/ --recursive
```

**The problem**: Every tool has different flags, different working directories,
different patterns. You need to remember (or look up) each one.

### Step 1: Wrap One Tool - Start with Terraform

Begin with the most common operation:

```makefile
ENVIRONMENT ?= dev

infra-plan: ## Plan infrastructure changes
	@cd terraform && terraform plan -var-file=$(ENVIRONMENT).tfvars
```

**Try it**:

```bash
make infra-plan                    # Uses dev
make infra-plan ENVIRONMENT=staging
```

**Problem discovered**: When the plan fails, you want to see detailed output. But Terraform's default verbosity isn't always enough.

**Check what Terraform offers**:

```bash
terraform plan --help | grep -i verbose
```

You find `TF_LOG=DEBUG`. Add a debug target:

```makefile
infra-plan: ## Plan infrastructure changes
	@echo "Planning $(ENVIRONMENT) infrastructure..."
	@cd terraform && terraform plan -var-file=$(ENVIRONMENT).tfvars

infra-plan-debug: ## Plan with debug output
	@echo "Planning $(ENVIRONMENT) infrastructure (debug)..."
	@cd terraform && TF_LOG=DEBUG terraform plan -var-file=$(ENVIRONMENT).tfvars
```

**What improved**: You discovered Terraform's debug mode and made it easily
accessible. Now when plans fail, `make infra-plan-debug` shows what's happening.

### Step 2: Add Apply with Safety

```makefile
infra-apply: ## Apply infrastructure changes
	@cd terraform && terraform apply -var-file=$(ENVIRONMENT).tfvars
```

**Problem**: This applies changes immediately. You want a confirmation step,
especially for production.

Add validation and confirmation:

```makefile
infra-apply: _validate-terraform _confirm-infra-apply ## Apply infrastructure changes
	@echo "Applying $(ENVIRONMENT) infrastructure..."
	@cd terraform && terraform apply -var-file=$(ENVIRONMENT).tfvars
	@echo "✓ Infrastructure applied"

_validate-terraform:
	@echo "Validating Terraform configuration..."
	@cd terraform && terraform validate
	@cd terraform && terraform fmt -check \
	|| (echo "Run 'make infra-format' to fix formatting" && exit 1)
	@echo "✓ Terraform valid"

_confirm-infra-apply:
	@if [ "$(ENVIRONMENT)" = "prod" ]; then \
		echo "⚠️  Applying to PRODUCTION infrastructure"; \
		echo -n "Type '$(ENVIRONMENT)' to confirm: "; \
		read ans && [ "$$ans" = "$(ENVIRONMENT)" ]; \
	fi

infra-format: ## Format Terraform files
	@cd terraform && terraform fmt
```

**What this adds**:

- Validation before every apply
- Formatting check (with fix command)
- Production confirmation
- Clear feedback

**Tool improvement**: You might create a wrapper script
`scripts/terraform-wrapper.sh` that always validates and formats. The Make
target would call that. The script becomes the improved interface to Terraform.

### Step 3: Add Helm with Dry-Run

```makefile
app-upgrade: ## Upgrade application with Helm
	@echo "Upgrading app in $(ENVIRONMENT)..."
	@helm upgrade myapp ./charts/myapp \
		-f charts/myapp/values-$(ENVIRONMENT).yaml
	@echo "✓ App upgraded"
