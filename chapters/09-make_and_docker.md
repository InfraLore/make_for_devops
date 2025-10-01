# Chapter 9: Make and Docker - Containerization Made Discoverable

\chaptersubtitle{Creating transparent, repeatable container workflows that eliminate the "works on my machine" problem.}

Docker transformed software deployment by packaging applications with their dependencies into portable containers. But Docker's power comes with complexity: multi-stage builds, registry management, image tagging strategies, development environment setup, and security scanning workflows. Teams often end up with scattered scripts, inconsistent commands, and the dreaded "I forgot how to build this" syndrome.

Make provides the perfect orchestration layer for Docker workflows. Instead of remembering complex `docker build` commands with multiple arguments, environment-specific tags, and intricate multi-stage coordination, team members can simply run `make build`, `make dev`, or `make deploy`. The Makefile becomes both the documentation and the implementation of your containerization strategy.

This chapter demonstrates how to create discoverable, maintainable Docker workflows using Make. We'll explore patterns for development environments, multi-stage builds, registry management, and local development with docker-compose.

\newpage
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

Each command has multiple flags, arguments that need calculation, and dependencies on previous steps. Documentation drifts, engineers forget flags, and "works on my machine" persists.

\newpage
Here's the discovery-based approach:

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

Running `make help` shows what's available. Each command is discoverable, and the complexity lives in scripts rather than being scattered across documentation.

\newpage
## Discovering Development Environments

Development with Docker involves multiple services and configuration. Make this discoverable:

```makefile
dev: ## Start development environment
	@echo "Starting development environment..."
	@$(MAKE) dev-services
	@$(MAKE) dev-app
	@echo "✓ Development ready: http://localhost:8080"
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

The workflow reveals itself progressively. `make dev` starts everything and tells you what commands are available. Each operation is independently discoverable.

\newpage
## Discovering Multi-Stage Builds

Multi-stage Dockerfiles create different images for different purposes. Make the stages discoverable:

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

Running `make build` shows available build targets. Each stage is independently buildable and the workflow is clear.

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

The registry workflow is discoverable through `make registry`. Authentication, versioning, and cleanup are all explicit operations.

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

Security becomes discoverable and repeatable. Developers can run the same scans locally that run in CI.

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

Compose operations are discoverable. Complex orchestration becomes simple commands.

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

The CI pipeline is discoverable and can be run locally. No surprises in CI that didn't happen locally.

\newpage
## Real-World Example

### Before: Scattered Scripts and Documentation

```
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
	@echo "✓ Dev ready: http://localhost:8080"

build: ## Build production image
	@./scripts/docker-build.sh $(VERSION)

test: ## Run tests
	@./scripts/docker-test.sh

push: build test security-scan ## Push to registry
	@./scripts/docker-push.sh $(VERSION)

security-scan: ## Scan for vulnerabilities
	@./scripts/security-scan.sh
```

One interface, works everywhere. CI and local development use identical commands. New team members run `make help` and understand the workflow immediately.

\newpage
## Key Patterns

Make Docker workflows discoverable through:

1. **Progressive menus** - `make docker` shows Docker operations, `make security` shows security operations
2. **Clear naming** - `dev`, `build`, `test`, `push` mean the same thing everywhere
3. **Built-in guidance** - Each target suggests next steps
4. **Script extraction** - Complex operations live in scripts, Makefile provides interface
5. **Composition** - Build complex workflows from simple, testable pieces

## Key Takeaways

Make transforms Docker workflows from scattered commands into discoverable operations:

1. **Discoverability**: `make help` reveals what's possible
2. **Consistency**: Same commands work locally and in CI
3. **Composability**: Build complex workflows from simple targets
4. **Safety**: Security and testing built into standard workflows
5. **Teachability**: New team members learn by discovering

The goal isn't to hide Docker complexity—it's to make it discoverable. Engineers can see what operations are available, understand dependencies between operations, and follow suggested next steps. The workflow reveals itself through interaction.

Most importantly, Docker workflows become team knowledge rather than individual expertise. That arcane `docker build` command with seven flags? It's now `make build`. The complex multi-service development setup? It's `make dev`. The workflow is captured, discoverable, and improvable by anyone on the team.

In the next chapter, we'll apply these same discovery patterns to Kubernetes orchestration, creating workflows that tame the complexity of cloud-native deployments.