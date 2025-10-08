# Chapter 5 - Variables and Configuration Management

\chaptersubtitle{Practical variable patterns that eliminate configuration drift
without over-engineering your workflows.}

## The Configuration Problem in DevOps

We have a conundrum: we want one deployment script that works everywhere, but
every environment is different.

The traditional solutions all have problems:

* **Separate scripts per environment**: Leads to drift—production gets a bug fix that staging doesn't
* **Template systems**: Hide what's actually running behind layers of indirection
* **External config management**: Adds dependencies and makes local development painful
* **Hard-coded values**: Everyone knows this is wrong but we've all done it

Make's variable system offers a different approach: **one workflow with
environment-aware defaults.** The same `make deploy` command works locally, in
staging, and in production. The differences are captured in variables, not in
separate scripts.

The key insight: **configuration should be visible, not hidden.** When you run
`make show-config`, you should see exactly what will be used. When you run `make
deploy ENVIRONMENT=production`, you should understand what changed from the
defaults.

## You Need Some Variables

Make's variable system is often presented as a powerful configuration management
platform. While this is technically true, the reality for most DevOps teams is
simpler: **you need a few variables with sensible defaults that users can easily
override.** That's it.

Consider a typical scenario: you're deploying to development, staging, and
production. Each environment needs different settings. The traditional approach
involves separate config files, environment-specific scripts, or elaborate
templating systems. Make's variables offer something simpler: one workflow with
environment-aware defaults.

This chapter will teach you the variable patterns that actually matter in
practice. We'll skip the theoretical possibilities and focus on what solves real
configuration problems.

The foundation of practical Make configuration is three simple patterns:

1. **Defaults with overrides**: `VERSION ?= latest` provides a sensible default
   that's easy to override
2. **Computed values**: `IMAGE_TAG = $(REGISTRY)/$(APP):$(VERSION)` builds
   complex values from simple inputs  
3. **Environment detection**: `VERSION = $(shell git describe --tags --always)`
   pulls values from your system

These three patterns handle 90% of configuration needs. Everything else in this
chapter is for the remaining 10%.

The simplest way to start is with environment variables. In your Makefile,
define defaults with `?=`:

```makefile
ENVIRONMENT ?= development
VERSION ?= $(shell git describe --tags --always)
REPLICAS ?= 1
```

Then override them at the command line when needed:

```bash
make deploy                           # Uses defaults
ENVIRONMENT=staging make deploy       # Override one
VERSION=v1.2.3 REPLICAS=3 make deploy # Override many
```

\begin{calloutbox}[Configuration: Start with Environment Variables, Not Files]
Only create config files when: \begin{itemize} \item You have 10+ variables per
environment \item Team members need to share configs \item Variables need
documentation and structure \item Environment variables become unwieldy
\end{itemize}

Most teams can go months or years with just environment variable overrides.
Don't add configuration files until you feel the pain of not having them.
\end{calloutbox}

## The Three Types of Variables (and When Each Matters)

Make has three assignment operators. Here's when each actually matters:

### `?=` Conditional Assignment (Use This Most)

Sets a variable only if not already set. **This is what you want 90% of the
time:**

```makefile
ENVIRONMENT ?= development
VERSION ?= $(shell git describe --tags --always)
REGISTRY ?= localhost:5000
```

**Use `?=` for:** Configuration that users should be able to override.

### `=` Recursive Assignment (Rarely Needed)

Evaluates the right side every time the variable is used:

```makefile
# Evaluated fresh each time TIMESTAMP is used
TIMESTAMP = $(shell date +%s)

# This will show different values
test:
	@echo $(TIMESTAMP)
	@sleep 1
	@echo $(TIMESTAMP)
```

**Use `=` for:** Values that should be computed dynamically. **Warning:** Can
hurt performance if overused.

### `:=` Simple Assignment (For Performance)

Evaluates once and stores the result:

```makefile
# Evaluated once at definition
TIMESTAMP := $(shell date +%s)

# This will show the same value twice
test:
	@echo $(TIMESTAMP)
	@sleep 1
	@echo $(TIMESTAMP)
```

**Use `:=` for:** Expensive operations you want to run once (like `shell`
commands).

\begin{calloutbox}[?= vs := vs =: When It Actually Matters] \textbf{For 95\% of
variables, use ?= and don't worry about it.}

Only consider := or = when: \begin{itemize} \item You have shell commands that
are slow (use :=) \item You need dynamic values that change (use =) \item Make
is noticeably slow (profile, then optimize) \end{itemize}

The performance difference is usually negligible. Use ?= until you have a
specific reason not to. \end{calloutbox}

## Environment-Specific Configuration: The Practical Approach

Here's how to handle different environments without over-engineering:

### Level 1: Simple Conditionals (Start Here)

For 2-3 environments with a few different settings:

```makefile
APP_NAME = myapp
ENVIRONMENT ?= development
VERSION ?= $(shell git describe --tags --always)

# Environment-specific settings
ifeq ($(ENVIRONMENT),production)
  REPLICAS = 3
  REGISTRY = prod-registry.company.com
else ifeq ($(ENVIRONMENT),staging)
  REPLICAS = 2
  REGISTRY = staging-registry.company.com
else
  REPLICAS = 1
  REGISTRY = localhost:5000
endif

# Computed values
IMAGE_TAG = $(REGISTRY)/$(APP_NAME):$(VERSION)
```

**This handles most cases.** It's clear, easy to modify, and everything is in
one place.

### Level 2: Config Files (When Level 1 Gets Messy)

When you have 10+ variables per environment, move to config files:

```makefile
# Load environment-specific config
-include config/$(ENVIRONMENT).mk

# Show what config is being used
show-config: ## Display current configuration
	@echo "Config: config/$(ENVIRONMENT).mk"
	@echo "Version: $(VERSION)"
	@echo "Registry: $(REGISTRY)"
	@echo "Replicas: $(REPLICAS)"
```

**config/development.mk:**
```makefile
REGISTRY = localhost:5000
REPLICAS = 1
LOG_LEVEL = DEBUG
```

**config/production.mk:**
```makefile
REGISTRY = prod-registry.company.com
REPLICAS = 3
LOG_LEVEL = WARN
BACKUP_ENABLED = true
```

The `-include` (with dash) means Make won't error if the file doesn't exist.

### Level 3: External Config Systems (For Large Organizations)

Only reach for external systems when:
- Multiple teams share configuration
- Secrets management is required
- Audit trails are needed
- You already have these systems

```makefile
# Load from AWS Parameter Store (if you already use it)
load-aws-config:
	$(eval DATABASE_URL := $(shell aws ssm get-parameter \
		--name "/myapp/$(ENVIRONMENT)/database-url" \
		--query 'Parameter.Value' --output text))

# Load from Vault (if you already use it)
load-vault-config:
	$(eval DATABASE_URL := $(shell vault kv get -field=url \
		secret/myapp/$(ENVIRONMENT)))

deploy: load-vault-config
	@echo "Deploying with DB: $(DATABASE_URL)"
```

**Don't build this unless you need it.** Environment variables work fine for
most teams.

\begin{calloutbox}[Configuration Files vs Environment Variables vs External
Systems] Choose based on team size and complexity:

\textbf{Environment variables (1-5 people):} \begin{itemize} \item \texttt{make
deploy ENVIRONMENT=staging} \item Simple, transparent, no files to maintain
\end{itemize}

\textbf{Config files (5-20 people):} \begin{itemize} \item Organized, shareable,
version controlled \item Good when you have 10+ settings per environment
\end{itemize}

\textbf{External systems (20+ people, or regulated):} \begin{itemize} \item
Centralized, auditable, secrets management \item Only worth it if already using
these systems \end{itemize}

Start with the simplest approach. Most teams never need external systems.
\end{calloutbox}

## Managing Secrets: The Only Right Way

**Never put secrets in Makefiles or config files.** Here's the right approach:

### Require Secrets via Environment Variables

```makefile
# Check that secrets are provided
check-secrets:
	@test -n "$$DATABASE_PASSWORD" || \
		(echo "Set DATABASE_PASSWORD environment variable" && exit 1)
	@test -n "$$API_KEY" || \
		(echo "Set API_KEY environment variable" && exit 1)

# Use them without exposing in logs
deploy: check-secrets
	@echo "Deploying with secrets..."
	kubectl create secret generic app-secrets \
		--from-literal=db-password="$$DATABASE_PASSWORD" \
		--from-literal=api-key="$$API_KEY" \
		--dry-run=client -o yaml | kubectl apply -f -
```

**Note the `$$` double dollar signs** - this passes the environment variable
through to the shell instead of treating it as a Make variable.

### Development Secrets (Optional)

For local development, you might want an `.env` file:

```makefile
# Load .env for development only (never commit this file)
ifneq ($(ENVIRONMENT),production)
  -include .env
  export
endif

# Create template
setup-dev: ## Create .env template
	@if [ ! -f .env ]; then \
		echo "DATABASE_PASSWORD=dev_password" > .env; \
		echo "API_KEY=dev_key" >> .env; \
		echo "Created .env - edit with your values"; \
	fi
```

Add `.env` to your `.gitignore` immediately.

### Secret Validation

Validate without exposing values:

```makefile
validate-secrets:
	@test $${#DATABASE_PASSWORD} -ge 8 || \
		(echo "DATABASE_PASSWORD too short" && exit 1)
	@echo "✓ Secrets validated"
```
\newpage
## Validation: Only What Prevents Real Bugs

Don't validate everything. Validate what has caused actual problems:

```makefile
validate-config: ## Validate configuration
	@echo "Validating configuration..."
	
	# Has a missing VERSION broken deploys? Add this:
	@test -n "$(VERSION)" || (echo "VERSION required" && exit 1)
	
	# Has wrong ENVIRONMENT caused issues? Add this:
	@case "$(ENVIRONMENT)" in \
		development|staging|production) ;; \
		*) echo "Invalid ENVIRONMENT: $(ENVIRONMENT)" && exit 1 ;; \
	esac
	
	# Has production deployed with 1 replica? Add this:
	@if [ "$(ENVIRONMENT)" = "production" ]; then \
		test "$(REPLICAS)" -gt 1 || \
			(echo "Production needs REPLICAS > 1" && exit 1); \
	fi
	
	@echo "✓ Configuration valid"

# Run validation before critical targets
deploy: validate-config
	@echo "Deploying $(APP_NAME) to $(ENVIRONMENT)..."
```

**Add validation reactively** - when something breaks, add a check to prevent it
next time.

\newpage
## A Practical Complete Example

Here's what most teams actually need:

```makefile
# Configuration with sensible defaults
APP_NAME = myapp
ENVIRONMENT ?= development
VERSION ?= $(shell git describe --tags --always)

# Environment-specific settings
ifeq ($(ENVIRONMENT),production)
  REPLICAS = 3
  REGISTRY = prod-registry.company.com
else
  REPLICAS = 1
  REGISTRY = localhost:5000
endif

IMAGE_TAG = $(REGISTRY)/$(APP_NAME):$(VERSION)

# Validate before critical operations
validate:
	@test -n "$(VERSION)" || (echo "VERSION required" && exit 1)
	@test -n "$$DATABASE_PASSWORD" || (echo "Set DATABASE_PASSWORD" && exit 1)

# Main workflow
deploy: validate
	@echo "Deploying $(IMAGE_TAG) to $(ENVIRONMENT)"
	docker build -t $(IMAGE_TAG) . && docker push $(IMAGE_TAG)
	kubectl set image deployment/$(APP_NAME) app=$(IMAGE_TAG)

show-config:
	@echo "Environment: $(ENVIRONMENT) | Version: $(VERSION) | Replicas: $(REPLICAS)"
```

This shows variables, environment logic, validation, and computed values working
together. Everything you need, nothing you don't.

\newpage
## When to Use Reusable Variable Libraries

**Short answer: probably never.**

Variable libraries sound great in theory:

```makefile
include lib/common.mk
include lib/docker.mk
include lib/kubernetes.mk
```

But they add complexity without much benefit unless:
- You maintain 10+ similar projects
- Variables are genuinely identical across projects
- You have dedicated DevOps team maintaining libraries

For most teams, copy-paste is fine. It's explicit, easy to modify, and doesn't
hide anything.

## Common Patterns Worth Knowing

### Git-Based Versioning

```makefile
VERSION ?= $(shell git describe --tags --always --dirty)
GIT_COMMIT = $(shell git rev-parse --short HEAD)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
```

### Build Metadata

```makefile
BUILD_TIME = $(shell date -u +%Y%m%d-%H%M%S)
BUILD_USER = $(shell whoami)

# Use in Docker builds
build:
	docker build \
		--build-arg VERSION=$(VERSION) \
		--build-arg BUILD_TIME=$(BUILD_TIME) \
		-t $(IMAGE_TAG) .
```

### Dynamic Namespace Names

```makefile
# Clean branch name for feature environments
CLEAN_BRANCH = $(shell git branch --show-current | \
	sed 's/[^a-z0-9-]/-/g' | tr '[:upper:]' '[:lower:]')
NAMESPACE = $(APP_NAME)-$(CLEAN_BRANCH)
```

## Configuration Help and Documentation

Make your configuration discoverable:

```makefile
config-help: ## Show configuration help
	@echo "Configuration Variables:"
	@echo ""
	@echo "  ENVIRONMENT  - deployment target (development|staging|production)"
	@echo "                 default: development"
	@echo ""
	@echo "  VERSION      - application version"
	@echo "                 default: git describe --tags"
	@echo ""
	@echo "  REPLICAS     - number of replicas"
	@echo "                 default: 1 (dev), 2 (staging), 3 (production)"
	@echo ""
	@echo "Required secrets (environment variables):"
	@echo "  DATABASE_PASSWORD"
	@echo "  API_KEY"
	@echo ""
	@echo "Examples:"
	@echo "  make deploy"
	@echo "  make deploy ENVIRONMENT=staging"
	@echo "  make deploy ENVIRONMENT=production VERSION=v1.0.0"
```

\newpage
## Troubleshooting Configuration

When things go wrong:

```makefile
debug-config: ## Debug configuration values
	@echo "=== Configuration Debug ==="
	@echo "ENVIRONMENT: $(ENVIRONMENT)"
	@echo "VERSION: $(VERSION)"
	@echo "REGISTRY: $(REGISTRY)"
	@echo "IMAGE_TAG: $(IMAGE_TAG)"
	@echo "REPLICAS: $(REPLICAS)"
	@echo ""
	@echo "=== Computed Values ==="
	@echo "Git commit: $(shell git rev-parse --short HEAD)"
	@echo "Git branch: $(shell git rev-parse --abbrev-ref HEAD)"
	@echo ""
	@echo "=== Environment Variables ==="
	@echo "DATABASE_PASSWORD: $$(test -n "$$DATABASE_PASSWORD" && echo "SET" || \
	  echo "NOT SET")"
	@echo "API_KEY: $$(test -n "$$API_KEY" && echo "SET" || echo "NOT SET")"
```

## Key Takeaways

Configuration management in Make should be simple and practical:

1. **Start with `?=` and environment variables** - This handles most cases

2. **Use config files when you have 10+ variables** - Not before

3. **Never store secrets in files** - Environment variables only

4. **Validate what has broken** - Not everything theoretically possible

5. **Keep it in one place** - Don't fragment configuration across files

6. **Make it discoverable** - `config-help` target shows what's available

7. **Environment-aware defaults** - Different sensible defaults per environment

8. **Copy-paste over libraries** - Unless maintaining many identical projects

The goal isn't sophisticated configuration management—it's having one clear
place where configuration lives, with sensible defaults that work locally and
simple overrides for other environments.

---

**For More Examples:** See the online companion repository (Appendix D) for:
- External config system integrations (AWS, GCP, Vault)
- Multi-format config file support (YAML, JSON, TOML)
- Configuration drift detection
- Complex variable library examples

In the next chapter, we'll explore how to organize targets and dependencies to
create intuitive, discoverable workflows that match how your team actually
thinks about their deployment process.