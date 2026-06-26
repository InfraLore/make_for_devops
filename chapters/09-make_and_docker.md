# Chapter 9: Make and Docker - Containerization Made Discoverable

\chaptersubtitle{Creating transparent, repeatable container workflows that
eliminate the “works on my machine” problem.}

Docker transformed software deployment by packaging applications with their
dependencies into portable containers. But Docker’s power comes with complexity:
multi-stage builds, registry management, image tagging strategies, development
environment setup, and security scanning workflows. Teams often end up with
scattered scripts, inconsistent commands, and the dreaded “I forgot how to build
this“ syndrome.

Make provides the perfect orchestration layer for Docker workflows. Instead of
remembering complex `docker build` commands with multiple arguments,
environment-specific tags, and intricate multi-stage coordination, team members
can simply run `make build`, `make dev`, or `make deploy`. The Makefile becomes
both the documentation and the implementation of your containerization strategy.

This chapter demonstrates how to create discoverable, maintainable Docker
workflows using Make. We’ll explore patterns for development environments,
multi-stage builds, registry management, and local development with
docker-compose.

\newpage

## Why Make When Docker Compose Exists?

Docker Compose, Lando, Tilt, Skaffold, and dozens of other tools provide
sophisticated Docker orchestration. So why add Make to the stack?

**Make isn’t replacing these tools—it’s providing the discoverable interface to
them.**

And here’s the thing: your team probably can’t agree on which orchestration tool
to use. Someone swears by Lando. Someone else thinks it’s overcomplicated and
prefers plain Docker Compose. The frontend team wants Tilt for its live reload.
The backend team just wants something that works.

You’ve probably had the meeting. Maybe multiple meetings. Someone proposed
standardizing on “the one true dev tool.” It didn’t go well. Everyone has strong
opinions based on their previous projects, their mental models, their laptop
setup.

Make lets you sidestep this argument—or at least defer it. Instead of forcing
everyone to use the same underlying tool, Make provides a consistent interface:\footnote{Script delegation pattern — see Chapter 21 for how this aids learning.}

```makefile
dev: ## Start development environment
	@$(MAKE) dev-$(DEV_TOOL)

dev-compose: ## Start using Docker Compose
	@docker-compose up -d
	@$(MAKE) dev-ready

dev-lando: ## Start using Lando
	@lando start
	@$(MAKE) dev-ready

dev-ready:
	@./scripts/wait-for-services.sh
	@$(MAKE) migrate
	@echo "Ready at http://localhost:8000"
```

\pagebreak
Consider a typical project using Docker Compose. A new engineer arrives and
asks: “How do I start this?” The answer is scattered:

- **README.md** might explain it (if it’s current)
- **docker-compose.yml** contains configuration, not instructions
- **.env.example** needs copying and editing (but where’s that documented?)
- **Slack history** has the real answers (“oh yeah, run migrations first”)
- **Team lore** fills in the gaps (“restart Redis if it acts weird”)

There’s no single source of truth, no clear entry point. The engineer copies
commands from Slack, gets an error about missing `.env`, copies that file, gets
an error about the database not being ready, waits a bit, runs migrations
manually, and finally gets things working. Thirty minutes later, they’ve figured
it out—but the next engineer will repeat the same process.

Six months later, someone adds a new service that needs initialization. The
README gets updated... eventually. Maybe. The Slack message explaining the new
step gets lost in history. The initialization becomes team lore: “Oh yeah, you
need to run the seed script after starting, otherwise the API returns 500s.“
Every new engineer discovers this the hard way.

The problem compounds over time. Each addition to the development environment—a
new database, a cache layer, a message queue, a mock external service—adds
another step that might or might not be documented, might or might not be in the
right order, might or might not still be current.

The problem isn’t Docker Compose. The problem is that Docker Compose starts
services but doesn’t encode the full workflow: the preparation, the waiting, the
post-startup steps, the initialization sequences, the “what do I do now?”
guidance. Docker Compose is configuration, not documentation. It describes what
to run, not how to use it.

\pagebreak
With Make as the interface:

```makefile
help: ## Show available commands
	@echo "Development:"
	@echo "  make dev        Start everything"
	@echo "  make dev-reset  Fresh start (destroys data)"
	@echo "  make logs       Show all logs"
	@echo "  make shell      Get shell in app container"

dev: ## Start development environment
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "Created .env - edit if needed"; \
	fi
	@docker-compose up -d
	@$(MAKE) _wait-for-services
	@$(MAKE) migrate
	@echo "✓ Dev ready: http://localhost:8000"
	@echo "  Logs: make logs"
	@echo "  Shell: make shell"

_wait-for-services:
	@./scripts/wait-for-postgres.sh
	@./scripts/wait-for-redis.sh
```

**Make provides what orchestration tools don’t:**

1. **Discoverability**: Docker Compose is powerful but doesn’t tell you what to
   do. `docker-compose up` doesn’t explain that you need to copy `.env.example`
   first, or run migrations, or wait for Postgres to be ready.

2. **Workflow coordination**: Orchestration tools start services. They don’t
   capture the sequence: “copy config, start services, wait for readiness, run
   migrations, show next steps.“

3. **Progressive disclosure**: `make help` shows common tasks. `make dev`
   handles the happy path. `make dev-reset` handles “my database is corrupted.”
   The complexity is there when you need it, hidden when you don’t.

4. **Tool composition**: Your project might use Docker Compose for services, `go
   run` for the app during development, and `kubectl` for deployment. Make
   provides one consistent interface across all of them.

5. **Team patterns**: Different engineers prefer different tools. Some use
   Docker Desktop, some use Colima, some use Podman. Make abstracts over these
   choices while still allowing them.

**The pattern**: Use specialized tools for what they’re good at, use Make for
discoverability and coordination.

```makefile
# Make doesn't replace Docker Compose
# It makes Docker Compose discoverable and composable

dev: ## Start development (using Docker Compose)
	@docker-compose up -d
	@$(MAKE) dev-ready

dev-ready:
	@./scripts/wait-for-services.sh
	@$(MAKE) migrate
	@echo "Ready at http://localhost:8000"

# Make doesn't replace Lando
# It provides a consistent interface whether you use Lando or not

dev-lando: ## Start development (using Lando)
	@lando start
	@$(MAKE) dev-ready  # Same post-startup steps

# Make doesn't replace kubectl
# It makes kubectl commands discoverable and safer

deploy: ## Deploy to staging
	@$(MAKE) build
	@$(MAKE) test
	@kubectl apply -f k8s/staging/
	@$(MAKE) wait-for-rollout
```

**When to skip Make**: If your project is simple enough that `docker-compose up`
is literally all anyone needs, skip Make. But the moment you have:

- Pre-startup steps (copying config, checking prerequisites)
- Post-startup steps (migrations, seeding data, health checks)
- Multiple environments (dev, test, CI)
- Multiple ways to run locally (Compose, Lando, native)
- Testing, building, or deployment workflows

...then Make’s discoverability layer starts providing real value.

**The test**: Can a new engineer run one command to get started? Can they
discover what else is possible? Can they understand the workflow without reading
documentation?

If yes, you probably have Make (or something like it) providing that interface.
If no, you’re relying on documentation staying current and team lore.

## Discovering Docker Workflows

The traditional approach to Docker involves remembering complex commands:

```bash
# Development
docker build --target development -t myapp:dev \
  --build-arg USER_ID=$(id -u) \
  --build-arg GROUP_ID=$(id -g) .
docker-compose -f docker-compose.dev.yml up -d

# Production
docker build --target production -t myapp:v1.2.3 \
  --build-arg VERSION=v1.2.3 \
  --build-arg BUILD_DATE=$(date -u +%Y-%m-%dT%H:%M:%SZ) .
docker tag myapp:v1.2.3 registry.company.com/myapp:v1.2.3
docker push registry.company.com/myapp:v1.2.3

# Testing
docker build --target test -t myapp:test .
docker run --rm myapp:test pytest tests/
```

Each command has multiple flags, arguments that need calculation, and
dependencies on previous steps. Documentation drifts, engineers forget flags,
and “works on my machine” persists.

Here’s the discovery-based approach:

```makefile
.DEFAULT_GOAL := help

APP_NAME := myapp
VERSION := $(shell git describe --tags --always --dirty)

help: ## Show Docker workflow commands
	@echo "Docker Workflows"
	@echo "================"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; \
		{printf "  %-20s %s\n", $$1, $$2}'

dev: ## Start development environment
	@echo "Starting development environment..."
	@./scripts/docker-dev.sh

build: ## Build production image
	@echo "Building $(APP_NAME):$(VERSION)..."
	@./scripts/docker-build.sh $(VERSION)

test: ## Run tests in container
	@echo "Running tests..."
	@./scripts/docker-test.sh

push: ## Push to registry
	@echo "Pushing to registry..."
	@./scripts/docker-push.sh $(VERSION)
```

Running `make help` shows what’s available. Each command is discoverable, and
the complexity lives in scripts rather than being scattered across
documentation.

\newpage

## Discovering Development Environments

Development with Docker involves multiple services and configuration. Make this
discoverable:

```makefile
dev: ## Start development environment
	@echo "Starting development environment..."
	@$(MAKE) dev-services
	@$(MAKE) dev-app
	@echo "Development ready: http://localhost:8080"
	@echo "  Logs: make dev-logs"
	@echo "  Shell: make dev-shell"

dev-services: ## Start supporting services (DB, Redis, etc)
	@echo "Starting services..."
	@./scripts/start-services.sh

dev-app: ## Start application
	@echo "Starting application..."
	@./scripts/start-app.sh

dev-stop: ## Stop development environment
	@./scripts/stop-dev.sh

dev-logs: ## Show development logs
	@./scripts/show-logs.sh

dev-shell: ## Get shell in container
	@./scripts/dev-shell.sh

dev-test: ## Run tests in dev environment
	@./scripts/run-tests-dev.sh
```

The workflow reveals itself progressively. `make dev` starts everything and
tells you what commands are available. Each operation is independently
discoverable.

\newpage

## Discovering Multi-Stage Builds

Multi-stage Dockerfiles create different images for different purposes. Make the
stages discoverable:

```makefile
build: ## Show build options
	@echo "Build Options"
	@echo "============="
	@echo "  make build-dev     - Development image"
	@echo "  make build-test    - Test image"
	@echo "  make build-prod    - Production image"
	@echo ""
	@echo "Current version: $(VERSION)"

build-dev: ## Build development image
	@echo "Building development image..."
	@./scripts/build-stage.sh development

build-test: ## Build test image
	@echo "Building test image..."
	@./scripts/build-stage.sh test

build-prod: ## Build production image
	@echo "Building production image..."
	@./scripts/build-stage.sh production $(VERSION)
```

Running `make build` shows available build targets. Each stage is independently
buildable and the workflow is clear.

\newpage

## Discovering Registry Operations

Registry management involves tagging, pushing, and version control:

```makefile
REGISTRY := registry.company.com
IMAGE_NAME := $(REGISTRY)/$(APP_NAME)

registry: ## Show registry operations
	@echo "Registry Operations"
	@echo "==================="
	@echo "  make login        - Login to registry"
	@echo "  make push         - Push current version"
	@echo "  make push-latest  - Push as latest"
	@echo "  make list-tags    - List tags in registry"
	@echo ""
	@echo "Current version: $(VERSION)"
	@echo "Registry: $(REGISTRY)"

login: ## Login to registry
	@./scripts/registry-login.sh

push: build-prod login ## Push to registry
	@echo "Pushing $(VERSION)..."
	@./scripts/registry-push.sh $(VERSION)

push-latest: push ## Tag and push as latest
	@./scripts/registry-push-latest.sh $(VERSION)

list-tags: ## List tags in registry
	@./scripts/registry-list-tags.sh
```

The registry workflow is discoverable through `make registry`. Authentication,
versioning, and cleanup are all explicit operations.

\newpage

## Discovering Security Scanning

Security scanning should be built into the workflow:

```makefile
security: ## Show security operations
	@echo "Security Operations"
	@echo "==================="
	@echo "  make security-scan        - Scan for vulnerabilities"
	@echo "  make security-secrets     - Check for secrets"
	@echo "  make security-compliance  - Check compliance"
	@echo ""
	@echo "Image: $(APP_NAME):$(VERSION)"

security-scan: build-prod ## Scan for vulnerabilities
	@echo "Scanning for vulnerabilities..."
	@./scripts/security-scan.sh $(APP_NAME):$(VERSION)

security-secrets: ## Scan for exposed secrets
	@echo "Scanning for secrets..."
	@./scripts/scan-secrets.sh

security-compliance: ## Check compliance
	@echo "Checking compliance..."
	@./scripts/check-compliance.sh
```

Security becomes discoverable and repeatable. Developers can run the same scans
locally that run in CI.

\newpage

## Discovering Compose Orchestration

Docker Compose involves multiple services and dependencies:

```makefile
compose: ## Show compose operations
	@echo "Docker Compose Operations"
	@echo "========================="
	@echo "  make compose-up       - Start all services"
	@echo "  make compose-down     - Stop all services"
	@echo "  make compose-logs     - Show logs"
	@echo "  make compose-ps       - Show running services"

compose-up: ## Start all services
	@echo "Starting services..."
	@./scripts/compose-up.sh

compose-down: ## Stop all services
	@./scripts/compose-down.sh

compose-logs: ## Show service logs
	@./scripts/compose-logs.sh

compose-ps: ## Show running services
	@./scripts/compose-ps.sh
```

Compose operations are discoverable. Complex orchestration becomes simple
commands.

\newpage

## Discovering CI/CD Integration

CI/CD pipelines need consistent, reliable Docker operations:

```makefile
ci: ## Show CI/CD operations
	@echo "CI/CD Operations"
	@echo "================"
	@echo "  make ci-pipeline    - Run full CI pipeline"
	@echo "  make ci-test        - CI test phase"
	@echo "  make ci-build       - CI build phase"
	@echo "  make ci-security    - CI security phase"

ci-pipeline: ## Run full CI pipeline
	@echo "Running CI pipeline..."
	@$(MAKE) ci-test
	@$(MAKE) ci-build
	@$(MAKE) ci-security
	@$(MAKE) push

ci-test: ## CI test phase
	@./scripts/ci-test.sh

ci-build: ## CI build phase
	@./scripts/ci-build.sh

ci-security: ## CI security phase
	@./scripts/ci-security.sh
```

The CI pipeline is discoverable and can be run locally. No surprises in CI that
didn’t happen locally.

\newpage

## Real-World Example

### Before: Scattered Scripts and Documentation

```text
README.md:
  "To build for production:
   docker build --target production -t myapp:$(git describe --tags) ...
   Remember to set BUILD_DATE and VERSION args
   Then tag for registry..."

dev-setup.sh:
  "Run docker-compose up with the right flags..."

.gitlab-ci.yml:
  "Complex Docker commands that differ from local builds..."

Result: Confusion, inconsistency, broken builds
```

\newpage

### After: Discoverable Workflow

```makefile
help: ## Show available commands
	@echo "Docker Workflows"
	@echo "  make dev      - Start development"
	@echo "  make build    - Build production"
	@echo "  make test     - Run tests"
	@echo "  make push     - Push to registry"
	@echo "  make security - Security scan"

dev: ## Start development environment
	@./scripts/docker-dev.sh
	@echo "Dev ready: http://localhost:8080"

build: ## Build production image
	@./scripts/docker-build.sh $(VERSION)

test: ## Run tests
	@./scripts/docker-test.sh

push: build test security-scan ## Push to registry
	@./scripts/docker-push.sh $(VERSION)

security-scan: ## Scan for vulnerabilities
	@./scripts/security-scan.sh
```

One interface, works everywhere. CI and local development use identical
commands. New team members run `make help` and understand the workflow
immediately.

\newpage

## Key Patterns

Make Docker workflows discoverable through:

1. **Progressive menus** - `make docker` shows Docker operations, `make
   security` shows security operations
2. **Clear naming** - `dev`, `build`, `test`, `push` mean the same thing
   everywhere
3. **Built-in guidance** - Each target suggests next steps
4. **Script extraction** - Complex operations live in scripts, Makefile provides
   interface
5. **Composition** - Build complex workflows from simple, testable pieces

## Key Takeaways

Make transforms Docker workflows from scattered commands into discoverable
operations:

1. **Discoverability**: `make help` reveals what’s possible
2. **Consistency**: Same commands work locally and in CI
3. **Composability**: Build complex workflows from simple targets
4. **Safety**: Security and testing built into standard workflows
5. **Teachability**: New team members learn by discovering

The goal isn’t to hide Docker complexity—it’s to make it discoverable. Engineers
can see what operations are available, understand dependencies between
operations, and follow suggested next steps. The workflow reveals itself through
interaction.

Most importantly, Docker workflows become team knowledge rather than individual
expertise. That arcane `docker build` command with seven flags? It’s now `make
build`. The complex multi-service development setup? It’s `make dev`. The
workflow is captured, discoverable, and improvable by anyone on the team.

In the next chapter, we’ll apply these same discovery patterns to Kubernetes
orchestration, creating workflows that tame the complexity of cloud-native
deployments.
