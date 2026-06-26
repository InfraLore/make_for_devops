# Chapter 5 - Variables and Configuration Management

\chaptersubtitle{Practical variable patterns that eliminate configuration drift
without over-engineering your workflows.}

## The Configuration Problem in DevOps

We have a conundrum: we want one deployment script that works everywhere, but
every environment is different.

The traditional solutions all have problems:

- **Separate scripts per environment**: Leads to drift—production gets a bug fix
  that staging doesn’t
- **Template systems**: Hide what’s actually running behind layers of
  indirection
- **External config management**: Adds dependencies and makes local development
  painful
- **Hard-coded values**: Everyone knows this is wrong but we’ve all done it

Make’s variable system offers a different approach: **one workflow with
environment-aware defaults.** The same `make deploy` command works locally, in
staging, and in production. The differences are captured in variables, not in
separate scripts.

The key insight: **configuration should be visible, not hidden.** When you run
`make show-config`, you should see exactly what will be used. When you run `make
deploy ENVIRONMENT=production`, you should understand what changed from the
defaults.

## You Need Some Variables

Make’s variable system is often presented as a powerful configuration management
platform. While this is technically true, the reality for most DevOps teams is
simpler: **you need a few variables with sensible defaults that users can easily
override.** That’s it.

Consider a typical scenario: you’re deploying to development, staging, and
production. Each environment needs different settings. The traditional approach
involves separate config files, environment-specific scripts, or elaborate
templating systems. Make’s variables offer something simpler: one workflow with
environment-aware defaults.

This chapter will teach you the variable patterns that actually matter in
practice. We’ll skip the theoretical possibilities and focus on what solves real
configuration problems.

The foundation of practical Make configuration is three simple patterns:

1. **Defaults with overrides**: `VERSION ?= latest` provides a sensible default
   that’s easy to override
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
Don’t add configuration files until you feel the pain of not having them.
\end{calloutbox}

## The Three Types of Variables (and When Each Matters)

Make has three assignment operators. Here’s when each actually matters:

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
variables, use ?= and don’t worry about it.}

Only consider := or = when: \begin{itemize} \item You have shell commands that
are slow (use :=) \item You need dynamic values that change (use =) \item Make
is noticeably slow \end{itemize}
\end{calloutbox}

## Environment-Specific Configuration: The Practical Approach

### Level 1: Simple Conditionals (Start Here)

```makefile
APP_NAME = myapp
ENVIRONMENT ?= development
VERSION ?= $(shell git describe --tags --always)

# Environment-specific settings
ifeq ($(ENVIRONMENT),production)
  REGISTRY = prod-registry.company.com
else ifeq ($(ENVIRONMENT),staging)
  REGISTRY = staging-registry.company.com
else
  REGISTRY = localhost:5000
endif

# Computed values
IMAGE_TAG = $(REGISTRY)/$(APP_NAME):$(VERSION)
```

**This handles most cases.** It’s clear, easy to modify, and everything is in
one place.

\pagebreak
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

The -include directive (with the leading dash) is Make’s way of saying “load
this file if it exists, but don’t fail if it doesn’t.“ This is exactly what you
want for optional environment-specific config files—if someone runs make deploy
without creating a config file first, the workflow should still work with the
defaults defined in the main Makefile. The leading dash is the “ignore errors”
prefix that tells Make to continue even if the include fails—we covered the
“ignore prefix” in Chapter 3 “Make Fundamentals” and will explore advanced uses
in Chapter 8 “Advanced Make.”

\newpage

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

**Don’t build this unless you need it.** Environment variables work fine for
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

**Never put secrets in Makefiles or config files.** Here’s the right approach:

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

Don’t validate everything. Validate what has caused actual problems:

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

Here’s what most teams actually need:

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
together. Everything you need, nothing you don’t.

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

For most teams, copy-paste is fine. It’s explicit, easy to modify, and doesn’t
hide anything.

## Common Patterns Worth Knowing

### Git-Based Versioning

```makefile
VERSION ?= $(shell git describe --tags --always --dirty)
GIT_COMMIT = $(shell git rev-parse --short HEAD)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
```
**Git-based versioning eliminates manual version management.** The git describe command generates version strings like `v1.2.3` (if on a tag) or `v1.2.3-5-g3a2b1c` (if 5 commits past the tag), and adds -dirty if you have uncommitted changes—giving you instant traceability from any deployed artifact back to its exact source code state. The commit hash and branch name are useful for feature environment deployments where you want namespaces like `myapp-feature-xyz` or build tags that include the commit. This approach means your version strings are always accurate and never require manual updating.

\pagebreak

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

**Build metadata helps with debugging and audit trails.** When something goes
wrong in production, knowing exactly when an image was built and by whom can be
crucial—especially in teams where multiple people might build from the same
commit. These values are typically embedded into the application itself (via
Docker build args that become environment variables) so they’re available at
runtime through health check endpoints or logging. The timestamp uses UTC format
to avoid timezone confusion, and the format `%Y%m%d-%H%M%S` sorts correctly and is
human-readable. This pattern is especially valuable in organizations with
compliance requirements.

**Most deployment platforms—Docker, Kubernetes, AWS, GCP, Azure—support labels,
tags, and annotations on deployed resources.** Your operations team has probably
already mandated certain tags like `cost-center` or `owner`, but you can add as many
as you want. Adding Git and build metadata as labels means you can look at any
running pod, container, or instance and instantly see what commit it’s running,
when it was built, and who built it. This is invaluable during incidents when
you need to know “is staging running the same code as production?” or “when did
this version get deployed?“ Without these labels, you’re stuck correlating
deployment logs, Git history, and CI timestamps. With them, `kubectl describe pod`
or checking your cloud console immediately shows you the complete provenance of
what’s running. It takes seconds to add these labels during deployment and saves
hours during troubleshooting.

### Dynamic Namespace Names

```makefile
# Clean branch name for feature environments
CLEAN_BRANCH = $(shell git branch --show-current | \
	sed 's/[^a-z0-9-]/-/g' | tr '[:upper:]' '[:lower:]')
NAMESPACE = $(APP_NAME)-$(CLEAN_BRANCH)
```
**Feature branch deployments need unique namespaces, but branch names aren’t valid Kubernetes identifiers.** A branch named `feature/NEW_Auth-System` needs to become `feature-new-auth-system` to work as a namespace. This pattern strips invalid characters, converts to lowercase, and combines it with your app name to create isolated environments for each feature branch. Run `make deploy` from any branch and you automatically get a namespace like `myapp-feature-new-auth-system` without having to specify anything.

**This pattern really sings if you’re also doing Continuous Deployment.** When every push automatically deploys, having a clear, easily understandable name associated with the code that’s running is magical. Reviewers can instantly find the right environment to test—no hunting through deployment logs or asking “which URL has your changes?” With multiple feature-testing environments deployed, the predictable naming scheme means everyone knows exactly where to look. When the branch is merged and deleted, you can clean up the corresponding namespace just as easily with `make delete-env` or similar. The combination of automatic deployment and automatic naming means feature environments become: push code, share a link, get feedback.

\newpage

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

**Make your configuration discoverable so people don’t have to read the Makefile
to understand it.** A config-help target serves as living documentation—it’s
always up to date because it lives next to the code it documents. New team
members can run make config-help and immediately understand what variables are
available, what they do, what the defaults are, and see concrete examples of how
to use them. This is especially valuable for variables that behave differently
across environments (like REPLICAS in the example above) or for documenting
which secrets are required. The ## comment after the target name means it will
also appear in your main help output (from make help), making configuration help
easily discoverable.

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

**When a deployment fails or behaves unexpectedly, the first question is always
“what configuration was actually used?”** A debug-config target dumps everything
relevant—variable values, computed results, git state, and whether required
secrets are present (without exposing their values). This eliminates the
guessing game of “did my override actually work?” or “why is it using the wrong
registry?“ The target shows three categories: explicit configuration (the
variables you set), computed values (what Make calculated from those variables),
and environment state (secrets and git info). Run make debug-config
ENVIRONMENT=production before a deployment to verify everything looks correct,
or run it after a failure to see exactly what configuration was used. This
single target will save you countless hours of debugging mysterious
configuration issues.

## Key Takeaways

Configuration management in Make should be simple and practical:

1. **Start with `?=` and environment variables** - This handles most cases

2. **Use config files when you have 10+ variables** - Not before; `-include`
lets them be optional

3. **Never store secrets in files** - Environment variables only

4. **Validate what has broken** - Not everything theoretically possible

5. **Keep it in one place** - Don’t fragment configuration across files

6. **Make it discoverable** - `config-help` target shows what’s available;
`debug-config` reveals what’s actually running

7. **Environment-aware defaults** - Different sensible defaults per environment

8. **Copy-paste over libraries** - Unless maintaining many identical projects

9. **Add Git and build metadata** - Tag your deployments with version, commit,
timestamp, and builder for instant traceability

10. **Use dynamic namespaces for feature branches** - Especially powerful with
Continuous Deployment; predictable naming eliminates coordination overhead

The goal isn’t sophisticated configuration management—it’s having one clear
place where configuration lives, with sensible defaults that work locally and
simple overrides for other environments.

In the next chapter, we’ll explore how to organize targets and dependencies to
create intuitive, discoverable workflows that match how your team actually
thinks about their deployment process.
