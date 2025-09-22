# Chapter 9 - Make and Docker - Containerization Made Discoverable
_Creating transparent, repeatable container workflows that eliminate the "works on my machine" problem._

Docker transformed software deployment by packaging applications with their dependencies into portable containers. But Docker's power comes with complexity: multi-stage builds, registry management, image tagging strategies, development environment setup, and security scanning workflows. Teams often end up with scattered scripts, inconsistent commands, and the dreaded "I forgot how to build this" syndrome.

Make provides the perfect orchestration layer for Docker workflows. Instead of remembering complex `docker build` commands with multiple arguments, environment-specific tags, and intricate multi-stage coordination, team members can simply run `make build`, `make dev`, or `make deploy`. The Makefile becomes both the documentation and the implementation of your containerization strategy.

This chapter demonstrates how to create discoverable, maintainable Docker workflows using Make. We'll explore patterns for development environments, multi-stage builds, registry management, security scanning, and local development with docker-compose. By the end, your Docker workflows will be as reliable and discoverable as any other aspect of your DevOps infrastructure.

> **🐳 Start Simple: Essential Docker + Make Patterns**
> 
> Master these fundamental patterns before exploring advanced container orchestration:
> 
> 1. **Basic build**: `build: Dockerfile src/` ensures rebuilds only when needed
> 2. **Development vs production**: Use different targets for different build contexts
> 3. **Consistent tagging**: `IMAGE_TAG = $(REGISTRY)/$(APP_NAME):$(VERSION)` eliminates tag confusion
> 4. **Registry management**: Separate build, tag, and push operations for better control
> 5. **Local development**: `dev` target that starts containers and handles dependencies
> 
> These patterns handle 90% of Docker workflow needs. Advanced techniques become valuable when managing complex multi-service applications or sophisticated CI/CD pipelines.

## Dockerized Development Environment Setup

### The Challenge of Consistent Development Environments

Every developer has experienced the frustration: "It works on my machine, but not on yours." Different operating systems, different tool versions, different environment configurations—all create subtle variations that lead to bugs and wasted time. Docker solves this by creating consistent, isolated environments, but managing Docker-based development workflows can become complex.

Make simplifies Docker development by providing standard interfaces to container operations:

```makefile
# =============================================================================
# Dockerized Development Environment
# =============================================================================

# Configuration
APP_NAME ?= myapp
DEV_IMAGE = $(APP_NAME):dev
PROD_IMAGE = $(APP_NAME):latest
DOCKER_COMPOSE_FILE ?= docker-compose.yml

# Development workflow
.PHONY: dev dev-build dev-stop dev-restart dev-logs dev-shell clean-dev

dev: dev-build ## 🚀 Start development environment
	@echo "Starting $(APP_NAME) development environment..."
	@docker-compose -f $(DOCKER_COMPOSE_FILE) up -d
	@echo "✅ Development environment started"
	@echo "📋 Available services:"
	@docker-compose -f $(DOCKER_COMPOSE_FILE) ps
	@echo ""
	@echo "💡 Useful commands:"
	@echo "  make dev-logs    # View application logs"
	@echo "  make dev-shell   # Get shell in main container"
	@echo "  make dev-stop    # Stop development environment"

dev-build: ## 🔨 Build development Docker image
	@echo "Building development image..."
	@docker build \
		--target development \
		--tag $(DEV_IMAGE) \
		--build-arg USER_ID=$(shell id -u) \
		--build-arg GROUP_ID=$(shell id -g) \
		.
	@echo "✅ Development image built: $(DEV_IMAGE)"

dev-stop: ## ⏹️ Stop development environment
	@echo "Stopping development environment..."
	@docker-compose -f $(DOCKER_COMPOSE_FILE) down
	@echo "✅ Development environment stopped"

dev-restart: dev-stop dev ## 🔄 Restart development environment
	@echo "✅ Development environment restarted"

dev-logs: ## 📋 Show development environment logs
	@docker-compose -f $(DOCKER_COMPOSE_FILE) logs -f --tail=100

dev-shell: ## 🐚 Get shell in development container
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec app bash

dev-test: ## 🧪 Run tests in development environment
	@echo "Running tests in development environment..."
	@docker-compose -f $(DOCKER_COMPOSE_FILE) exec -T app pytest tests/ -v

clean-dev: ## 🧹 Clean development environment
	@echo "Cleaning development environment..."
	@docker-compose -f $(DOCKER_COMPOSE_FILE) down -v --remove-orphans
	@docker rmi $(DEV_IMAGE) 2>/dev/null || true
	@echo "✅ Development environment cleaned"
```

### Multi-Stage Dockerfile Integration

Multi-stage Dockerfiles create different images for different purposes (development, testing, production). Make can orchestrate these stages elegantly:

**Dockerfile:**

```dockerfile
# Development stage - includes dev tools and debuggers
FROM node:18-alpine AS development
RUN apk add --no-cache git curl bash
WORKDIR /app
COPY package*.json ./
RUN npm install --include=dev
COPY . .
CMD ["npm", "run", "dev"]

# Test stage - includes test dependencies
FROM development AS test
RUN npm run lint
RUN npm run test
RUN npm audit --audit-level high

# Production build stage
FROM node:18-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build

# Production runtime stage - minimal image
FROM node:18-alpine AS production
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nextjs -u 1001
WORKDIR /app
COPY --from=build --chown=nextjs:nodejs /app/dist ./dist
COPY --from=build --chown=nextjs:nodejs /app/package*.json ./
USER nextjs
EXPOSE 3000
CMD ["npm", "start"]
```

**Makefile integration:**

```makefile
# =============================================================================
# Multi-Stage Docker Builds
# =============================================================================

# Build different stages for different purposes
build-dev: ## 🔨 Build development image
	@echo "Building development image..."
	@docker build --target development -t $(APP_NAME):dev .

build-test: ## 🧪 Build test image (includes linting and tests)
	@echo "Building test image..."
	@docker build --target test -t $(APP_NAME):test .

build-prod: ## 📦 Build production image
	@echo "Building production image..."
	@docker build --target production -t $(APP_NAME):$(VERSION) .
	@docker tag $(APP_NAME):$(VERSION) $(APP_NAME):latest

# Run tests using the test stage
test: build-test ## 🧪 Run tests in test container
	@echo "Tests already run during build (see test stage)"
	@echo "✅ Tests passed"

# Alternative: run tests in existing test image
test-interactive: build-test ## 🧪 Run tests interactively
	@docker run --rm -it $(APP_NAME):test npm test -- --watchAll=false

# Security scan the production image
security-scan: build-prod ## 🔒 Run security scan on production image
	@echo "Running security scan..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image $(APP_NAME):$(VERSION)

# Complete CI pipeline using different stages
ci-pipeline: ## 🤖 Complete CI pipeline
	@echo "🚀 Running complete CI pipeline..."
	@$(MAKE) build-test  # Builds and runs tests
	@$(MAKE) build-prod  # Builds production image
	@$(MAKE) security-scan  # Scans production image
	@echo "✅ CI pipeline completed"
```

### Development Environment Dependencies

Modern applications often require multiple services (database, cache, message queue). Make can orchestrate complex development environments:

```makefile
# =============================================================================
# Multi-Service Development Environment
# =============================================================================

# Service management
.PHONY: dev-services dev-app dev-full dev-db dev-redis dev-migrate

dev-full: dev-services dev-migrate dev-app ## 🚀 Start complete development environment
	@echo "✅ Complete development environment started"

dev-services: ## 🛠️ Start supporting services only
	@echo "Starting supporting services..."
	@docker-compose -f docker-compose.services.yml up -d
	@$(MAKE) wait-for-services
	@echo "✅ Supporting services started"

dev-app: dev-build ## 🚀 Start application (requires services to be running)
	@echo "Starting application..."
	@docker-compose -f docker-compose.app.yml up -d
	@echo "✅ Application started"

# Individual service management
dev-db: ## 🗄️ Start database only
	@echo "Starting database..."
	@docker-compose -f docker-compose.services.yml up -d postgres
	@timeout 30 bash -c 'until docker-compose -f docker-compose.services.yml exec -T postgres pg_isready; do sleep 1; done'
	@echo "✅ Database ready"

dev-redis: ## 📊 Start Redis cache only
	@echo "Starting Redis..."
	@docker-compose -f docker-compose.services.yml up -d redis
	@timeout 10 bash -c 'until docker-compose -f docker-compose.services.yml exec -T redis redis-cli ping | grep -q PONG; do sleep 1; done'
	@echo "✅ Redis ready"

dev-migrate: dev-db ## 📈 Run database migrations
	@echo "Running database migrations..."
	@docker-compose -f docker-compose.services.yml exec -T postgres createdb -U postgres $(APP_NAME)_dev || echo "Database already exists"
	@docker run --rm --network $(APP_NAME)_dev-network \
		-e DATABASE_URL=postgresql://postgres:password@postgres:5432/$(APP_NAME)_dev \
		$(DEV_IMAGE) alembic upgrade head
	@echo "✅ Database migrations completed"

# Wait for services to be ready
wait-for-services: ## ⏳ Wait for services to be ready
	@echo "Waiting for services to be ready..."
	@docker-compose -f docker-compose.services.yml exec -T postgres pg_isready || $(MAKE) dev-db
	@docker-compose -f docker-compose.services.yml exec -T redis redis-cli ping | grep -q PONG || $(MAKE) dev-redis
	@echo "✅ All services ready"

# Development environment status
dev-status: ## 📊 Show development environment status
	@echo "Development Environment Status:"
	@echo "================================"
	@echo ""
	@echo "Services:"
	@docker-compose -f docker-compose.services.yml ps 2>/dev/null || echo "  No services running"
	@echo ""
	@echo "Application:"
	@docker-compose -f docker-compose.app.yml ps 2>/dev/null || echo "  Application not running"
	@echo ""
	@echo "Resource usage:"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}" | grep $(APP_NAME) || echo "  No containers running"
```

## Multi-Stage Build Orchestration Through Make

### Optimizing Build Performance

Multi-stage builds can be slow if not properly orchestrated. Make can optimize the process by building stages selectively and leveraging caching:

```makefile
# =============================================================================
# Optimized Multi-Stage Build Orchestration
# =============================================================================

# Build artifacts directory
BUILD_DIR = .build
CACHE_DIR = .cache

# Dependency tracking for selective rebuilds
$(BUILD_DIR)/.base-built: Dockerfile package*.json
	@mkdir -p $(BUILD_DIR)
	@echo "🔨 Building base image..."
	@docker build --target base --tag $(APP_NAME):base .
	@touch $(BUILD_DIR)/.base-built

$(BUILD_DIR)/.deps-installed: $(BUILD_DIR)/.base-built package*.json package-lock.json
	@echo "📦 Installing dependencies..."
	@docker build --target dependencies --tag $(APP_NAME):deps .
	@touch $(BUILD_DIR)/.deps-installed

$(BUILD_DIR)/.dev-built: $(BUILD_DIR)/.deps-installed $(shell find src -type f) Dockerfile
	@echo "🔨 Building development image..."
	@docker build --target development --tag $(APP_NAME):dev .
	@touch $(BUILD_DIR)/.dev-built

$(BUILD_DIR)/.test-built: $(BUILD_DIR)/.deps-installed $(shell find tests -type f) $(shell find src -type f)
	@echo "🧪 Building test image..."
	@docker build --target test --tag $(APP_NAME):test .
	@touch $(BUILD_DIR)/.test-built

$(BUILD_DIR)/.prod-built: $(BUILD_DIR)/.deps-installed $(shell find src -type f)
	@echo "📦 Building production image..."
	@docker build --target production --tag $(APP_NAME):$(VERSION) .
	@docker tag $(APP_NAME):$(VERSION) $(APP_NAME):latest
	@touch $(BUILD_DIR)/.prod-built

# Public targets that depend on build artifacts
build-dev: $(BUILD_DIR)/.dev-built ## 🔨 Build development image (incremental)

build-test: $(BUILD_DIR)/.test-built ## 🧪 Build test image (incremental)

build-prod: $(BUILD_DIR)/.prod-built ## 📦 Build production image (incremental)

build-all: build-dev build-test build-prod ## 🔨 Build all images

# Force clean builds
build-clean: ## 🧹 Clean build and rebuild all images
	@echo "🧹 Cleaning build artifacts..."
	@rm -rf $(BUILD_DIR)
	@docker rmi $(APP_NAME):base $(APP_NAME):deps $(APP_NAME):dev $(APP_NAME):test 2>/dev/null || true
	@$(MAKE) build-all

# Build with caching from registry
build-with-cache: ## 🔨 Build with registry cache
	@echo "🔨 Building with registry cache..."
	@docker build \
		--cache-from $(REGISTRY)/$(APP_NAME):base \
		--cache-from $(REGISTRY)/$(APP_NAME):deps \
		--cache-from $(REGISTRY)/$(APP_NAME):dev \
		--target development \
		--tag $(APP_NAME):dev \
		.

# Push intermediate layers for caching
push-cache: ## 📤 Push build cache to registry
	@echo "📤 Pushing build cache..."
	@docker tag $(APP_NAME):base $(REGISTRY)/$(APP_NAME):base
	@docker tag $(APP_NAME):deps $(REGISTRY)/$(APP_NAME):deps
	@docker tag $(APP_NAME):dev $(REGISTRY)/$(APP_NAME):dev
	@docker push $(REGISTRY)/$(APP_NAME):base
	@docker push $(REGISTRY)/$(APP_NAME):deps
	@docker push $(REGISTRY)/$(APP_NAME):dev
```

### BuildKit and Advanced Build Features

Modern Docker BuildKit provides advanced features like multi-platform builds and improved caching. Make can orchestrate these features:

```makefile
# =============================================================================
# Advanced BuildKit Features
# =============================================================================

# Enable BuildKit
export DOCKER_BUILDKIT=1
export BUILDKIT_PROGRESS=plain

# Multi-platform builds
build-multiplatform: ## 🌍 Build for multiple platforms
	@echo "🌍 Building for multiple platforms..."
	@docker buildx create --name multiplatform --use || true
	@docker buildx build \
		--platform linux/amd64,linux/arm64 \
		--target production \
		--tag $(REGISTRY)/$(APP_NAME):$(VERSION) \
		--push \
		.

# Build with advanced cache mounting
build-with-mounts: ## 🔨 Build with cache mounts
	@echo "🔨 Building with cache mounts..."
	@docker build \
		--target production \
		--tag $(APP_NAME):$(VERSION) \
		--build-arg BUILDKIT_INLINE_CACHE=1 \
		.

# Build with secrets
build-with-secrets: ## 🔐 Build with secrets (for private dependencies)
	@echo "🔐 Building with secrets..."
	@docker build \
		--secret id=npm,src=.npmrc \
		--secret id=ssh,src=$(HOME)/.ssh/id_rsa \
		--tag $(APP_NAME):$(VERSION) \
		.

# Parallel multi-stage builds
build-parallel: ## ⚡ Build multiple stages in parallel
	@echo "⚡ Building stages in parallel..."
	@$(MAKE) -j3 build-dev build-test build-stage-docs

build-stage-docs: ## 📚 Build documentation stage
	@docker build --target docs --tag $(APP_NAME):docs .
```

## Container Registry Management and Versioning

### Registry Authentication and Management

Managing container registries involves authentication, tagging strategies, and cleanup policies:

```makefile
# =============================================================================
# Container Registry Management
# =============================================================================

# Registry configuration
REGISTRY ?= registry.company.com
REGISTRY_PROJECT ?= $(APP_NAME)
REGISTRY_NAMESPACE ?= $(REGISTRY)/$(REGISTRY_PROJECT)

# Version and tag management
VERSION ?= $(shell git describe --tags --always --dirty)
GIT_COMMIT = $(shell git rev-parse --short HEAD)
BUILD_DATE = $(shell date -u +%Y%m%d-%H%M%S)

# Image tags
DEV_TAG = $(REGISTRY_NAMESPACE):dev-$(GIT_COMMIT)
TEST_TAG = $(REGISTRY_NAMESPACE):test-$(GIT_COMMIT)
PROD_TAG = $(REGISTRY_NAMESPACE):$(VERSION)
LATEST_TAG = $(REGISTRY_NAMESPACE):latest

.PHONY: login push push-all push-dev push-test push-prod tag-all cleanup-tags

# Registry authentication
login: ## 🔑 Login to container registry
	@echo "🔑 Logging into registry..."
	@if [ -n "$(REGISTRY_USER)" ] && [ -n "$(REGISTRY_PASS)" ]; then \
		echo "$(REGISTRY_PASS)" | docker login $(REGISTRY) -u "$(REGISTRY_USER)" --password-stdin; \
	else \
		echo "⚠️ REGISTRY_USER and REGISTRY_PASS not set, using existing credentials"; \
	fi

# Tagging strategy
tag-all: build-all ## 🏷️ Tag all images for registry
	@echo "🏷️ Tagging images..."
	@docker tag $(APP_NAME):dev $(DEV_TAG)
	@docker tag $(APP_NAME):test $(TEST_TAG)
	@docker tag $(APP_NAME):$(VERSION) $(PROD_TAG)
	@docker tag $(APP_NAME):$(VERSION) $(LATEST_TAG)
	@echo "✅ All images tagged"

# Selective pushing
push-dev: build-dev tag-all login ## 📤 Push development image
	@echo "📤 Pushing development image..."
	@docker push $(DEV_TAG)

push-test: build-test tag-all login ## 📤 Push test image
	@echo "📤 Pushing test image..."
	@docker push $(TEST_TAG)

push-prod: build-prod tag-all login ## 📤 Push production image
	@echo "📤 Pushing production image..."
	@docker push $(PROD_TAG)
	@docker push $(LATEST_TAG)

push-all: push-dev push-test push-prod ## 📤 Push all images

# Push with metadata
push-with-metadata: tag-all login ## 📤 Push with build metadata
	@echo "📤 Pushing with build metadata..."
	@docker push $(PROD_TAG)
	@docker push $(LATEST_TAG)
	@echo "📝 Recording build metadata..."
	@echo "version=$(VERSION)" > build-metadata.txt
	@echo "commit=$(GIT_COMMIT)" >> build-metadata.txt
	@echo "build_date=$(BUILD_DATE)" >> build-metadata.txt
	@echo "registry=$(REGISTRY_NAMESPACE)" >> build-metadata.txt

# Registry cleanup
list-tags: ## 📋 List all tags in registry
	@echo "📋 Tags in registry:"
	@docker run --rm quay.io/skopeo/skopeo list-tags docker://$(REGISTRY_NAMESPACE) | jq -r '.Tags[]' | sort

cleanup-old-tags: ## 🧹 Clean up old tags from registry
	@echo "🧹 Cleaning up old tags..."
	@TAGS=$$(docker run --rm quay.io/skopeo/skopeo list-tags docker://$(REGISTRY_NAMESPACE) | jq -r '.Tags[]' | grep -E '^dev-|^test-' | head -n -10); \
	for tag in $$TAGS; do \
		echo "Deleting tag: $$tag"; \
		docker run --rm quay.io/skopeo/skopeo delete docker://$(REGISTRY_NAMESPACE):$$tag; \
	done

# Registry health check
check-registry: ## 🏥 Check registry health
	@echo "🏥 Checking registry health..."
	@docker run --rm quay.io/skopeo/skopeo inspect docker://$(REGISTRY_NAMESPACE):latest >/dev/null && \
		echo "✅ Registry is accessible" || \
		echo "❌ Registry is not accessible"
```

### Semantic Versioning and Release Management

Implement sophisticated versioning strategies:

```makefile
# =============================================================================
# Semantic Versioning and Release Management
# =============================================================================

# Version detection and manipulation
CURRENT_VERSION = $(shell git describe --tags --abbrev=0 2>/dev/null || echo "v0.0.0")
NEXT_PATCH = $(shell echo $(CURRENT_VERSION) | awk -F. -v OFS=. '{$$NF = $$NF + 1; print}')
NEXT_MINOR = $(shell echo $(CURRENT_VERSION) | awk -F. -v OFS=. '{$$(NF-1) = $$(NF-1) + 1; $$NF = 0; print}')
NEXT_MAJOR = $(shell echo $(CURRENT_VERSION) | awk -F. -v OFS=. '{$$1 = substr($$1,2) + 1; $$2 = 0; $$NF = 0; print "v" $$0}')

# Release management
.PHONY: release-patch release-minor release-major release-check

release-check: ## ✅ Check release readiness
	@echo "🔍 Checking release readiness..."
	@git diff --quiet || (echo "❌ Uncommitted changes" && exit 1)
	@git diff --cached --quiet || (echo "❌ Uncommitted staged changes" && exit 1)
	@$(MAKE) test
	@$(MAKE) security-scan
	@echo "✅ Release checks passed"

release-patch: release-check ## 🏷️ Create patch release
	@echo "🏷️ Creating patch release: $(NEXT_PATCH)"
	@git tag $(NEXT_PATCH)
	@$(MAKE) build-prod VERSION=$(NEXT_PATCH)
	@$(MAKE) push-prod VERSION=$(NEXT_PATCH)
	@git push origin $(NEXT_PATCH)
	@echo "✅ Patch release $(NEXT_PATCH) created and pushed"

release-minor: release-check ## 🏷️ Create minor release
	@echo "🏷️ Creating minor release: $(NEXT_MINOR)"
	@git tag $(NEXT_MINOR)
	@$(MAKE) build-prod VERSION=$(NEXT_MINOR)
	@$(MAKE) push-prod VERSION=$(NEXT_MINOR)
	@git push origin $(NEXT_MINOR)
	@echo "✅ Minor release $(NEXT_MINOR) created and pushed"

release-major: release-check ## 🏷️ Create major release
	@echo "🚨 Creating MAJOR release: $(NEXT_MAJOR)"
	@echo "⚠️ This is a major version bump. Continue? [y/N]" && read ans && [ $$ans = y ]
	@git tag $(NEXT_MAJOR)
	@$(MAKE) build-prod VERSION=$(NEXT_MAJOR)
	@$(MAKE) push-prod VERSION=$(NEXT_MAJOR)
	@git push origin $(NEXT_MAJOR)
	@echo "✅ Major release $(NEXT_MAJOR) created and pushed"

# Release candidates
release-candidate: ## 🧪 Create release candidate
	@RC_VERSION="$(NEXT_MINOR)-rc.$(shell date +%Y%m%d%H%M%S)"; \
	echo "🧪 Creating release candidate: $$RC_VERSION"; \
	git tag $$RC_VERSION; \
	$(MAKE) build-prod VERSION=$$RC_VERSION; \
	$(MAKE) push-prod VERSION=$$RC_VERSION; \
	git push origin $$RC_VERSION; \
	echo "✅ Release candidate $$RC_VERSION created"

# Show version information
version-info: ## ℹ️ Show version information
	@echo "Version Information:"
	@echo "  Current: $(CURRENT_VERSION)"
	@echo "  Next patch: $(NEXT_PATCH)"
	@echo "  Next minor: $(NEXT_MINOR)"
	@echo "  Next major: $(NEXT_MAJOR)"
	@echo "  Git commit: $(GIT_COMMIT)"
	@echo "  Git branch: $(shell git rev-parse --abbrev-ref HEAD)"
```

## Local Development with Docker Compose Integration

### Orchestrating Development Services

Complex applications require multiple services during development. Make can elegantly orchestrate docker-compose workflows:

```makefile
# =============================================================================
# Docker Compose Development Orchestration
# =============================================================================

# Compose file configuration
COMPOSE_FILE_DEV = docker-compose.dev.yml
COMPOSE_FILE_SERVICES = docker-compose.services.yml
COMPOSE_PROJECT_NAME = $(APP_NAME)-dev

# Set compose project name
export COMPOSE_PROJECT_NAME

.PHONY: dev-up dev-down dev-restart dev-build dev-logs dev-ps dev-exec

# Complete development environment
dev-up: ## 🚀 Start complete development environment
	@echo "🚀 Starting complete development environment..."
	@$(MAKE) dev-services-up
	@$(MAKE) dev-app-up
	@$(MAKE) dev-status
	@echo ""
	@echo "💡 Development environment ready!"
	@echo "   App: http://localhost:8080"
	@echo "   Docs: http://localhost:8081"
	@echo "   Logs: make dev-logs"

dev-services-up: ## 🛠️ Start supporting services
	@echo "🛠️ Starting supporting services..."
	@docker-compose -f $(COMPOSE_FILE_SERVICES) up -d
	@echo "⏳ Waiting for services to be ready..."
	@$(MAKE) wait-for-db
	@$(MAKE) wait-for-redis
	@$(MAKE) run-migrations
	@echo "✅ Supporting services ready"

dev-app-up: ## 🚀 Start application services
	@echo "🚀 Starting application services..."
	@docker-compose -f $(COMPOSE_FILE_DEV) up -d
	@echo "⏳ Waiting for application to be ready..."
	@timeout 60 bash -c 'until curl -f http://localhost:8080/health; do sleep 2; done'
	@echo "✅ Application ready"

dev-down: ## ⏹️ Stop development environment
	@echo "⏹️ Stopping development environment..."
	@docker-compose -f $(COMPOSE_FILE_DEV) down
	@docker-compose -f $(COMPOSE_FILE_SERVICES) down
	@echo "✅ Development environment stopped"

dev-restart: dev-down dev-up ## 🔄 Restart development environment

dev-build: ## 🔨 Build development services
	@echo "🔨 Building development services..."
	@docker-compose -f $(COMPOSE_FILE_DEV) build --parallel
	@echo "✅ Development services built"

dev-logs: ## 📋 Show development environment logs
	@docker-compose -f $(COMPOSE_FILE_DEV) -f $(COMPOSE_FILE_SERVICES) logs -f --tail=100

dev-ps: ## 📊 Show running development services
	@echo "Running Development Services:"
	@docker-compose -f $(COMPOSE_FILE_DEV) -f $(COMPOSE_FILE_SERVICES) ps

# Individual service management
dev-db-up: ## 🗄️ Start database only
	@docker-compose -f $(COMPOSE_FILE_SERVICES) up -d postgres
	@$(MAKE) wait-for-db

dev-redis-up: ## 📊 Start Redis only
	@docker-compose -f $(COMPOSE_FILE_SERVICES) up -d redis
	@$(MAKE) wait-for-redis

dev-app-only: ## 🚀 Start app without rebuilding services
	@docker-compose -f $(COMPOSE_FILE_DEV) up -d app

# Service health checks
wait-for-db: ## ⏳ Wait for database to be ready
	@echo "⏳ Waiting for database..."
	@timeout 30 bash -c 'until docker-compose -f $(COMPOSE_FILE_SERVICES) exec -T postgres pg_isready -U postgres; do sleep 1; done'
	@echo "✅ Database ready"

wait-for-redis: ## ⏳ Wait for Redis to be ready
	@echo "⏳ Waiting for Redis..."
	@timeout 30 bash -c 'until docker-compose -f $(COMPOSE_FILE_SERVICES) exec -T redis redis-cli ping | grep -q PONG; do sleep 1; done'
	@echo "✅ Redis ready"

# Database operations
run-migrations: wait-for-db ## 📈 Run database migrations
	@echo "📈 Running database migrations..."
	@docker-compose -f $(COMPOSE_FILE_SERVICES) exec -T postgres createdb -U postgres $(APP_NAME)_dev 2>/dev/null || echo "Database exists"
	@docker-compose -f $(COMPOSE_FILE_DEV) run --rm app alembic upgrade head
	@echo "✅ Migrations completed"

reset-db: ## 🔄 Reset development database
	@echo "⚠️ This will destroy all data in the development database. Continue? [y/N]" && read ans && [ $$ans = y ]
	@docker-compose -f $(COMPOSE_FILE_SERVICES) exec -T postgres dropdb -U postgres $(APP_NAME)_dev || true
	@$(MAKE) run-migrations
	@echo "✅ Database reset completed"

# Development utilities
dev-exec: ## 🐚 Execute command in app container
	@read -p "Command: " cmd; \
	docker-compose -f $(COMPOSE_FILE_DEV) exec app $$cmd

dev-shell: ## 🐚 Get shell in app container
	@docker-compose -f $(COMPOSE_FILE_DEV) exec app bash

dev-test: ## 🧪 Run tests in development environment
	@echo "🧪 Running tests in development environment..."
	@docker-compose -f $(COMPOSE_FILE_DEV) exec -T app pytest tests/ -v

dev-status: ## 📊 Show development environment status
	@echo "Development Environment Status:"
	@echo "================================"
	@docker-compose -f $(COMPOSE_FILE_DEV) -f $(COMPOSE_FILE_SERVICES) ps
	@echo ""
	@echo "Health Checks:"
	@curl -s http://localhost:8080/health | jq '.' 2>/dev/null && echo "✅ App healthy" || echo "❌ App unhealthy"
	@docker-compose -f $(COMPOSE_FILE_SERVICES) exec -T postgres pg_isready -U postgres >/dev/null 2>&1 && echo "✅ Database healthy" || echo "❌ Database unhealthy"
	@docker-compose -f $(COMPOSE_FILE_SERVICES) exec -T redis redis-cli ping | grep -q PONG && echo "✅ Redis healthy" || echo "❌ Redis unhealthy"

# Clean development environment
dev-clean: dev-down ## 🧹 Clean development environment
	@echo "🧹 Cleaning development environment..."
	@docker-compose -f $(COMPOSE_FILE_DEV) -f $(COMPOSE_FILE_SERVICES) down -v --remove-orphans
	@docker system prune -f --filter "label=com.docker.compose.project=$(COMPOSE_PROJECT_NAME)"
	@echo "✅ Development environment cleaned"
```

### Hot Reloading and Development Workflows

Enable efficient development workflows with hot reloading and file watching:

```makefile
# =============================================================================
# Hot Reloading Development Workflows
# =============================================================================

# Development modes
dev-watch: ## 👁️ Start development with file watching
	@echo "👁️ Starting development with file watching..."
	@$(MAKE) dev-services-up
	@docker-compose -f $(COMPOSE_FILE_DEV) -f docker-compose.watch.yml up --build
	@echo "💡 File watching active - changes will trigger rebuilds"

dev-debug: ## 🐛 Start development in debug mode
	@echo "🐛 Starting development in debug mode..."
	@$(MAKE) dev-services-up
	@COMPOSE_FILE_DEV=docker-compose.debug.yml $(MAKE) dev-app-up
	@echo "🐛 Debug server started on port 5678"
	@echo "💡 Attach your debugger to localhost:5678"

dev-profile: ## 📊 Start development with profiling
	@echo "📊 Starting development with profiling..."
	@$(MAKE) dev-services-up  
	@COMPOSE_FILE_DEV=docker-compose.profile.yml $(MAKE) dev-app-up
	@echo "📊 Profiler available at http://localhost:8080/profile"

# File synchronization options
dev-sync: ## 🔄 Start with file synchronization (for better performance)
	@echo "🔄 Starting with file synchronization..."
	@docker volume create $(APP_NAME)-sync-volume
	@$(MAKE) dev-services-up
	@docker-compose -f $(COMPOSE_FILE_DEV) -f docker-compose.sync.yml up -d
	@echo "🔄 File sync active - better performance on non-Linux hosts"

# Testing in development
dev-test-watch: ## 🧪 Run tests with file watching
	@echo "🧪 Running tests with file watching..."
	@docker-compose -f $(COMPOSE_FILE_DEV) exec app pytest tests/ --testmon --looponfail

dev-test-coverage: ## 📊 Run tests with coverage in development
	@echo "📊 Running tests with coverage..."
	@docker-compose -f $(COMPOSE_FILE_DEV) exec app pytest tests/ --cov=src --cov-report=html --cov-report=term
	@echo "📊 Coverage report available at htmlcov/index.html"

# Performance monitoring in development
dev-monitor: ## 📈 Start performance monitoring
	@echo "📈 Starting performance monitoring..."
	@docker-compose -f $(COMPOSE_FILE_SERVICES) -f docker-compose.monitoring.yml up -d
	@echo "📈 Monitoring available:"
	@echo "   Grafana: http://localhost:3000 (admin/admin)"
	@echo "   Prometheus: http://localhost:9090"
```

## Container Security Scanning and Compliance Checks

### Multi-Layer Security Scanning

Implement comprehensive security scanning for container images:

```makefile
# =============================================================================
# Container Security Scanning
# =============================================================================

# Security scanning tools configuration
TRIVY_CACHE_DIR = .trivy-cache
SECURITY_REPORTS_DIR = security-reports

.PHONY: security-scan security-scan-all security-report security-compliance

# Comprehensive security scanning
security-scan: build-prod ## 🔒 Run comprehensive security scan
	@echo "🔒 Running comprehensive security scan..."
	@mkdir -p $(SECURITY_REPORTS_DIR)
	@$(MAKE) scan-vulnerabilities
	@$(MAKE) scan-secrets
	@$(MAKE) scan-configuration
	@$(MAKE) scan-compliance
	@echo "✅ Security scan completed - check $(SECURITY_REPORTS_DIR)/"

# Vulnerability scanning with Trivy
scan-vulnerabilities: ## 🕳️ Scan for vulnerabilities
	@echo "🕳️ Scanning for vulnerabilities..."
	@mkdir -p $(TRIVY_CACHE_DIR) $(SECURITY_REPORTS_DIR)
	@docker run --rm \
		-v $(TRIVY_CACHE_DIR):/root/.cache/ \
		-v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image \
		--format json \
		--output /dev/stdout \
		$(APP_NAME):$(VERSION) > $(SECURITY_REPORTS_DIR)/vulnerabilities.json
	@docker run --rm \
		-v $(TRIVY_CACHE_DIR):/root/.cache/ \
		-v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image \
		--format table \
		$(APP_NAME):$(VERSION)

# Secrets scanning
scan-secrets: ## 🕵️ Scan for secrets in image
	@echo "🕵️ Scanning for secrets..."
	@docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		trufflesecurity/trufflehog docker \
		--image $(APP_NAME):$(VERSION) \
		--json > $(SECURITY_REPORTS_DIR)/secrets.json || true

# Configuration scanning
scan-configuration: ## ⚙️ Scan container configuration
	@echo "⚙️ Scanning container configuration..."
	@docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy config \
		--format json \
		--output $(SECURITY_REPORTS_DIR)/config.json \
		.

# Compliance scanning
scan-compliance: ## 📋 Run compliance checks
	@echo "📋 Running compliance checks..."
	@docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-v $(PWD):/workspace \
		aquasec/dockle \
		--format json \
		--output /workspace/$(SECURITY_REPORTS_DIR)/compliance.json \
		$(APP_NAME):$(VERSION) || true

# Generate security report
security-report: ## 📊 Generate comprehensive security report
	@echo "📊 Generating security report..."
	@python3 scripts/generate-security-report.py \
		--vulnerabilities $(SECURITY_REPORTS_DIR)/vulnerabilities.json \
		--secrets $(SECURITY_REPORTS_DIR)/secrets.json \
		--config $(SECURITY_REPORTS_DIR)/config.json \
		--compliance $(SECURITY_REPORTS_DIR)/compliance.json \
		--output $(SECURITY_REPORTS_DIR)/security-report.html
	@echo "✅ Security report generated: $(SECURITY_REPORTS_DIR)/security-report.html"

# Security gates for CI/CD
security-gate: ## 🚪 Security gate for CI/CD pipeline
	@echo "🚪 Running security gate..."
	@$(MAKE) scan-vulnerabilities
	@CRITICAL_VULNS=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "CRITICAL")] | length' $(SECURITY_REPORTS_DIR)/vulnerabilities.json); \
	HIGH_VULNS=$(jq '[.Results[]?.Vulnerabilities[]? | select(.Severity == "HIGH")] | length' $(SECURITY_REPORTS_DIR)/vulnerabilities.json); \
	if [ $CRITICAL_VULNS -gt 0 ]; then \
		echo "❌ Security gate failed: $CRITICAL_VULNS critical vulnerabilities found"; \
		exit 1; \
	elif [ $HIGH_VULNS -gt 10 ]; then \
		echo "❌ Security gate failed: $HIGH_VULNS high vulnerabilities found (limit: 10)"; \
		exit 1; \
	else \
		echo "✅ Security gate passed"; \
	fi

# Continuous security monitoring
security-monitor: ## 🔍 Set up continuous security monitoring
	@echo "🔍 Setting up security monitoring..."
	@docker run -d \
		--name $(APP_NAME)-security-monitor \
		--restart unless-stopped \
		-v /var/run/docker.sock:/var/run/docker.sock \
		-e SCAN_INTERVAL=3600 \
		-e TARGET_IMAGE=$(APP_NAME):latest \
		aquasec/harbor-scanner-trivy:latest

# Security scan for multiple images
security-scan-all: ## 🔒 Scan all project images
	@echo "🔒 Scanning all project images..."
	@for image in dev test $(VERSION) latest; do \
		echo "Scanning $(APP_NAME):$image..."; \
		$(MAKE) scan-vulnerabilities APP_NAME=$(APP_NAME) VERSION=$image; \
	done
```

### Dockerfile Security Best Practices

Implement Dockerfile linting and security best practices:

```makefile
# =============================================================================
# Dockerfile Security and Best Practices
# =============================================================================

# Dockerfile linting and security
dockerfile-lint: ## 📝 Lint Dockerfile for best practices
	@echo "📝 Linting Dockerfile..."
	@docker run --rm -i hadolint/hadolint < Dockerfile || true

dockerfile-security: ## 🔒 Check Dockerfile security
	@echo "🔒 Checking Dockerfile security..."
	@docker run --rm \
		-v $(PWD):/workspace \
		aquasec/trivy config \
		--format table \
		/workspace/Dockerfile

# Generate secure Dockerfile template
generate-secure-dockerfile: ## 📝 Generate secure Dockerfile template
	@echo "📝 Generating secure Dockerfile template..."
	@cat > Dockerfile.secure << 'EOF'
# Use specific version tags, not latest
FROM node:18.17.0-alpine3.18 AS base

# Create non-root user
RUN addgroup -g 1001 -S nodejs && \
    adduser -S nodeuser -u 1001

# Install security updates
RUN apk update && \
    apk upgrade && \
    apk add --no-cache dumb-init && \
    rm -rf /var/cache/apk/*

# Set working directory
WORKDIR /app

# Copy package files and install dependencies
COPY package*.json ./
RUN npm ci --only=production && \
    npm cache clean --force

# Copy application code
COPY --chown=nodeuser:nodejs . .

# Switch to non-root user
USER nodeuser

# Use dumb-init for proper signal handling
ENTRYPOINT ["dumb-init", "--"]

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Expose port
EXPOSE 3000

# Start application
CMD ["npm", "start"]
EOF
	@echo "✅ Secure Dockerfile template created: Dockerfile.secure"

# Validate Dockerfile security practices
validate-dockerfile-security: ## ✅ Validate Dockerfile follows security best practices
	@echo "✅ Validating Dockerfile security practices..."
	@ERRORS=0; \
	if ! grep -q "FROM.*:" Dockerfile; then echo "❌ Use specific image tags"; ERRORS=$((ERRORS+1)); fi; \
	if grep -q "FROM.*latest" Dockerfile; then echo "❌ Avoid 'latest' tag"; ERRORS=$((ERRORS+1)); fi; \
	if ! grep -q "USER" Dockerfile; then echo "❌ Set non-root user"; ERRORS=$((ERRORS+1)); fi; \
	if ! grep -q "HEALTHCHECK" Dockerfile; then echo "⚠️ Consider adding health check"; fi; \
	if grep -q "ADD " Dockerfile; then echo "⚠️ Prefer COPY over ADD"; fi; \
	if [ $ERRORS -eq 0 ]; then \
		echo "✅ Dockerfile security validation passed"; \
	else \
		echo "❌ Dockerfile security validation failed ($ERRORS errors)"; \
		exit 1; \
	fi

# SBOM (Software Bill of Materials) generation
generate-sbom: build-prod ## 📋 Generate Software Bill of Materials
	@echo "📋 Generating SBOM..."
	@docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		anchore/syft $(APP_NAME):$(VERSION) \
		-o json > $(SECURITY_REPORTS_DIR)/sbom.json
	@docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		anchore/syft $(APP_NAME):$(VERSION) \
		-o table
	@echo "✅ SBOM generated: $(SECURITY_REPORTS_DIR)/sbom.json"

# Sign images for supply chain security
sign-image: push-prod ## ✍️ Sign container image
	@echo "✍️ Signing container image..."
	@cosign sign --yes $(PROD_TAG)
	@echo "✅ Image signed: $(PROD_TAG)"

verify-signature: ## ✅ Verify container image signature
	@echo "✅ Verifying image signature..."
	@cosign verify $(PROD_TAG)
	@echo "✅ Signature verified"
```

## Advanced Docker Workflows

### Multi-Architecture Builds

Support multiple CPU architectures:

```makefile
# =============================================================================
# Multi-Architecture Container Builds
# =============================================================================

# Architecture configuration
PLATFORMS ?= linux/amd64,linux/arm64,linux/arm/v7
BUILDER_NAME = $(APP_NAME)-builder

# Set up buildx for multi-arch
setup-buildx: ## 🏗️ Set up Docker Buildx for multi-architecture builds
	@echo "🏗️ Setting up Docker Buildx..."
	@docker buildx create --name $(BUILDER_NAME) --use || true
	@docker buildx inspect --bootstrap
	@echo "✅ Buildx ready for platforms: $(PLATFORMS)"

# Multi-architecture build
build-multiarch: setup-buildx ## 🌍 Build for multiple architectures
	@echo "🌍 Building for multiple architectures..."
	@docker buildx build \
		--platform $(PLATFORMS) \
		--target production \
		--tag $(PROD_TAG) \
		--tag $(LATEST_TAG) \
		--push \
		--cache-from type=registry,ref=$(REGISTRY_NAMESPACE):buildcache \
		--cache-to type=registry,ref=$(REGISTRY_NAMESPACE):buildcache,mode=max \
		.
	@echo "✅ Multi-architecture build completed"

# Architecture-specific builds
build-amd64: ## 🔧 Build for AMD64 only
	@docker buildx build --platform linux/amd64 --tag $(APP_NAME):amd64 --load .

build-arm64: ## 🔧 Build for ARM64 only
	@docker buildx build --platform linux/arm64 --tag $(APP_NAME):arm64 --load .

# Test multi-arch images
test-multiarch: build-multiarch ## 🧪 Test multi-architecture images
	@echo "🧪 Testing multi-architecture images..."
	@for platform in linux/amd64 linux/arm64; do \
		echo "Testing $platform..."; \
		docker run --rm --platform $platform $(PROD_TAG) echo "✅ $platform works"; \
	done

# Clean up buildx
cleanup-buildx: ## 🧹 Clean up Buildx builder
	@docker buildx rm $(BUILDER_NAME) || true
```

### Container Resource Management

Optimize container resource usage:

```makefile
# =============================================================================
# Container Resource Management
# =============================================================================

# Resource monitoring
monitor-resources: ## 📊 Monitor container resource usage
	@echo "📊 Container resource usage:"
	@docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"

# Resource-constrained builds
build-low-memory: ## 🔨 Build with memory constraints
	@echo "🔨 Building with memory constraints..."
	@docker build \
		--memory=1g \
		--memory-swap=2g \
		--tag $(APP_NAME):low-memory \
		.

# Optimize image size
optimize-image-size: ## 📦 Optimize image size
	@echo "📦 Optimizing image size..."
	@echo "Current size:"
	@docker images $(APP_NAME):$(VERSION) --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}"
	@docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		wagoodman/dive:latest $(APP_NAME):$(VERSION) --ci --highestUserWastedPercent=0.1

# Image analysis
analyze-layers: ## 🔍 Analyze image layers
	@echo "🔍 Analyzing image layers..."
	@docker history $(APP_NAME):$(VERSION) --human --format "table {{.CreatedBy}}\t{{.Size}}"

# Clean unused resources
clean-docker: ## 🧹 Clean unused Docker resources
	@echo "🧹 Cleaning unused Docker resources..."
	@docker system df
	@docker system prune -f
	@docker image prune -f
	@echo "✅ Docker cleanup completed"
	@docker system df
```

## Integration with CI/CD Pipelines

### Pipeline-Optimized Workflows

Create Make targets optimized for CI/CD execution:

```makefile
# =============================================================================
# CI/CD Pipeline Integration
# =============================================================================

# CI pipeline target
ci-pipeline: ## 🤖 Complete CI pipeline
	@echo "🤖 Starting CI pipeline..."
	@$(MAKE) dockerfile-lint
	@$(MAKE) build-test
	@$(MAKE) build-prod  
	@$(MAKE) security-gate
	@$(MAKE) push-prod
	@echo "✅ CI pipeline completed successfully"

# Parallel CI pipeline
ci-pipeline-parallel: ## ⚡ Parallel CI pipeline
	@echo "⚡ Starting parallel CI pipeline..."
	@$(MAKE) -j4 dockerfile-lint validate-dockerfile-security build-test build-prod
	@$(MAKE) security-gate
	@$(MAKE) push-prod
	@echo "✅ Parallel CI pipeline completed"

# CD pipeline target
cd-pipeline: ## 🚀 Complete CD pipeline  
	@echo "🚀 Starting CD pipeline..."
	@$(MAKE) verify-signature || echo "⚠️ No signature found"
	@$(MAKE) deploy-staging
	@$(MAKE) smoke-test ENVIRONMENT=staging
	@$(MAKE) deploy-production
	@$(MAKE) smoke-test ENVIRONMENT=production
	@echo "✅ CD pipeline completed successfully"

# Environment-specific CI/CD
ci-branch-main: ## 🤖 CI pipeline for main branch
	@$(MAKE) ci-pipeline
	@$(MAKE) sign-image

ci-branch-develop: ## 🤖 CI pipeline for develop branch
	@$(MAKE) build-test
	@$(MAKE) build-prod
	@$(MAKE) security-scan
	@$(MAKE) push-dev

ci-pull-request: ## 🤖 CI pipeline for pull requests
	@$(MAKE) dockerfile-lint
	@$(MAKE) build-test
	@$(MAKE) security-scan

# Cache management for CI
ci-cache-pull: ## 📥 Pull build cache in CI
	@echo "📥 Pulling build cache..."
	@docker pull $(REGISTRY_NAMESPACE):buildcache || true
	@docker pull $(REGISTRY_NAMESPACE):base || true
	@docker pull $(REGISTRY_NAMESPACE):deps || true

ci-cache-push: ## 📤 Push build cache in CI
	@echo "📤 Pushing build cache..."
	@$(MAKE) push-cache

# CI cleanup
ci-cleanup: ## 🧹 Cleanup after CI run
	@echo "🧹 CI cleanup..."
	@docker system prune -f
	@rm -rf $(BUILD_DIR) $(SECURITY_REPORTS_DIR)
```

## Complete Example: Production-Ready Docker Makefile

Here's how all these concepts come together in a comprehensive, production-ready Makefile:

```makefile
# =============================================================================
# Production-Ready Docker Makefile
# =============================================================================

# Configuration
APP_NAME ?= myapp
VERSION ?= $(shell git describe --tags --always --dirty)
REGISTRY ?= registry.company.com
REGISTRY_NAMESPACE = $(REGISTRY)/$(APP_NAME)

# Image tags
DEV_TAG = $(REGISTRY_NAMESPACE):dev-$(shell git rev-parse --short HEAD)
PROD_TAG = $(REGISTRY_NAMESPACE):$(VERSION)
LATEST_TAG = $(REGISTRY_NAMESPACE):latest

# Build configuration
DOCKERFILE ?= Dockerfile
DOCKER_CONTEXT ?= .
PLATFORMS = linux/amd64,linux/arm64

# Compose configuration
COMPOSE_FILE_DEV = docker-compose.dev.yml
COMPOSE_PROJECT_NAME = $(APP_NAME)-dev

.DEFAULT_GOAL := help

# =============================================================================
# Help and Information
# =============================================================================

help: ## 📋 Show available commands
	@echo "$(APP_NAME) Docker Workflow"
	@echo "============================"
	@echo ""
	@echo "🚀 Quick Start:"
	@echo "  make dev         # Start development environment"
	@echo "  make build       # Build production image"
	@echo "  make test        # Run tests"
	@echo "  make push        # Push to registry"
	@echo ""
	@echo "📖 All Commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $1, $2 }' $(MAKEFILE_LIST)

status: ## 📊 Show Docker environment status
	@echo "Docker Environment Status:"
	@echo "=========================="
	@echo "App: $(APP_NAME) v$(VERSION)"
	@echo "Registry: $(REGISTRY_NAMESPACE)"
	@echo ""
	@echo "Images:"
	@docker images $(APP_NAME) --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}" 2>/dev/null || echo "  No local images"
	@echo ""
	@echo "Development environment:"
	@docker-compose -f $(COMPOSE_FILE_DEV) ps 2>/dev/null || echo "  Not running"

# =============================================================================
# Development Workflow
# =============================================================================

.PHONY: dev dev-build dev-stop dev-clean dev-logs dev-shell dev-test

dev: dev-build ## 🚀 Start development environment
	@$(MAKE) dev-services
	@docker-compose -f $(COMPOSE_FILE_DEV) up -d
	@echo "✅ Development environment started"
	@echo "   App: http://localhost:8080"
	@echo "   Logs: make dev-logs"

dev-build: ## 🔨 Build development image
	@docker build --target development -t $(APP_NAME):dev .

dev-stop: ## ⏹️ Stop development environment
	@docker-compose -f $(COMPOSE_FILE_DEV) down

dev-clean: dev-stop ## 🧹 Clean development environment
	@docker-compose -f $(COMPOSE_FILE_DEV) down -v --remove-orphans
	@docker rmi $(APP_NAME):dev 2>/dev/null || true

dev-logs: ## 📋 Show development logs
	@docker-compose -f $(COMPOSE_FILE_DEV) logs -f --tail=100

dev-shell: ## 🐚 Get shell in development container
	@docker-compose -f $(COMPOSE_FILE_DEV) exec app bash

dev-test: ## 🧪 Run tests in development environment
	@docker-compose -f $(COMPOSE_FILE_DEV) exec -T app pytest tests/ -v

# =============================================================================
# Build Workflow  
# =============================================================================

.PHONY: build build-prod build-test clean-build

build: build-prod ## 🔨 Build production image

build-prod: ## 📦 Build production image
	@echo "📦 Building production image..."
	@docker build \
		--target production \
		--tag $(APP_NAME):$(VERSION) \
		--tag $(APP_NAME):latest \
		--build-arg VERSION=$(VERSION) \
		--build-arg BUILD_DATE=$(shell date -u +%Y-%m-%dT%H:%M:%SZ) \
		--build-arg GIT_COMMIT=$(shell git rev-parse HEAD) \
		$(DOCKER_CONTEXT)

build-test: ## 🧪 Build test image
	@docker build --target test -t $(APP_NAME):test .

clean-build: ## 🧹 Clean build artifacts
	@docker rmi $(APP_NAME):$(VERSION) $(APP_NAME):latest $(APP_NAME):test 2>/dev/null || true

# =============================================================================
# Testing and Security
# =============================================================================

.PHONY: test security-scan dockerfile-lint

test: build-test ## 🧪 Run tests
	@echo "✅ Tests already run during build"

security-scan: build-prod ## 🔒 Run security scan
	@echo "🔒 Running security scan..."
	@docker run --rm \
		-v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image $(APP_NAME):$(VERSION)

dockerfile-lint: ## 📝 Lint Dockerfile
	@docker run --rm -i hadolint/hadolint < $(DOCKERFILE)

# =============================================================================
# Registry Operations
# =============================================================================

.PHONY: push push-dev push-prod login tag-all

login: ## 🔑 Login to container registry
	@echo "$(REGISTRY_PASS)" | docker login $(REGISTRY) -u "$(REGISTRY_USER)" --password-stdin

tag-all: build-prod ## 🏷️ Tag images for registry
	@docker tag $(APP_NAME):$(VERSION) $(PROD_TAG)
	@docker tag $(APP_NAME):$(VERSION) $(LATEST_TAG)
	@docker tag $(APP_NAME):dev $(DEV_TAG)

push: push-prod ## 📤 Push production image

push-prod: tag-all login ## 📤 Push production image to registry
	@echo "📤 Pushing production image..."
	@docker push $(PROD_TAG)
	@docker push $(LATEST_TAG)

push-dev: tag-all login ## 📤 Push development image
	@docker push $(DEV_TAG)

# =============================================================================
# CI/CD Integration
# =============================================================================

.PHONY: ci-pipeline cd-pipeline

ci-pipeline: ## 🤖 Complete CI pipeline
	@echo "🤖 Starting CI pipeline..."
	@$(MAKE) dockerfile-lint
	@$(MAKE) build-test
	@$(MAKE) build-prod
	@$(MAKE) security-scan
	@$(MAKE) push-prod
	@echo "✅ CI pipeline completed"

cd-pipeline: ## 🚀 Complete CD pipeline
	@echo "🚀 CD pipeline not implemented - see Chapter 11"

# =============================================================================
# Utilities
# =============================================================================

.PHONY: clean version-info

clean: dev-clean clean-build ## 🧹 Clean everything
	@docker system prune -f

version-info: ## ℹ️ Show version information
	@echo "Version: $(VERSION)"
	@echo "Git commit: $(shell git rev-parse HEAD)"
	@echo "Git branch: $(shell git rev-parse --abbrev-ref HEAD)"
	@echo "Build date: $(shell date -u +%Y-%m-%dT%H:%M:%SZ)"

# Supporting targets
dev-services:
	@docker-compose -f docker-compose.services.yml up -d
	@echo "⏳ Waiting for services..."
	@sleep 5
```

## Key Takeaways

Make transforms Docker workflows from scattered scripts and hard-to-remember commands into discoverable, maintainable workflows. The key principles to remember:

1. **Standardize Interfaces**: Use consistent target names (`dev`, `build`, `test`, `push`) across all projects
    
2. **Layer Orchestration**: Build complex workflows from simple, composable targets that can be tested independently
    
3. **Environment Awareness**: Create different workflows for development, testing, and production without duplicating logic
    
4. **Security by Default**: Integrate security scanning, compliance checks, and best practices into standard workflows
    
5. **Performance Optimization**: Use file-based dependencies, multi-stage coordination, and intelligent caching
    
6. **CI/CD Integration**: Design targets that work efficiently in both local development and automated pipelines
    
7. **Discoverability**: Make workflows self-documenting through help systems and clear target organization
    

Well-designed Docker workflows with Make eliminate the "works on my machine" problem not just at the container level, but at the workflow level. Team members can confidently build, test, and deploy applications using standard, reliable commands that work consistently across different environments and team members.

In the next chapter, we'll explore how to apply these same principles to Kubernetes orchestration, creating discoverable workflows that tame the complexity of cloud-native deployments.