# Appendix B - Migration Strategies

This appendix provides step-by-step guides for migrating existing workflows to Make-based approaches. Each strategy addresses a common starting point and provides a gradual, low-risk path to adoption.

## General Migration Principles

Before diving into specific scenarios, keep these principles in mind:

**Start Small**: Begin with high-value, low-risk targets (like `help`, `test`, `build`)

**Run in Parallel**: Keep existing workflows while introducing Make targets that call them

**Iterate Gradually**: Add complexity over time as team comfort grows

**Document as You Go**: Each Make target becomes documentation

**Validate Continuously**: Ensure Make workflows produce identical results to existing processes

**Get Feedback**: Involve the team early and incorporate their input

## Migration 1: From README Instructions to Executable Targets

**Starting Point**: Traditional README with manual setup instructions

**Goal**: Create executable `make setup` and `make dev` targets

### Step 1: Inventory Current Process

Document what developers currently do:

```markdown
# Current README.md
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

### Step 2: Create Basic Makefile

Start with a simple help target and one setup target:

```makefile
.DEFAULT_GOAL := help

help: ## Show available commands
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

setup: ## Set up development environment (run once)
	@echo "Setting up development environment..."
	@$(MAKE) _check-prerequisites
	@$(MAKE) _install-dependencies
	@$(MAKE) _setup-configuration
	@$(MAKE) _setup-database
	@echo "✅ Setup complete! Run 'make dev' to start."

_check-prerequisites:
	@echo "Checking prerequisites..."
	@command -v node >/dev/null || \
		(echo "❌ Node.js required. Install from nodejs.org" && exit 1)
	@command -v python3 >/dev/null || \
		(echo "❌ Python 3 required" && exit 1)
	@command -v docker >/dev/null || \
		(echo "❌ Docker required" && exit 1)
	@echo "✅ All prerequisites found"

_install-dependencies:
	@echo "Installing dependencies..."
	@npm install --silent
	@pip install -r requirements.txt --quiet

_setup-configuration:
	@if [ ! -f .env ]; then \
		cp .env.example .env; \
		echo "✅ Created .env file"; \
		echo "⚠️  Please edit .env with your configuration"; \
	else \
		echo "✅ .env already exists"; \
	fi

_setup-database:
	@echo "Starting database..."
	@docker run -d --name myapp-db \
		-e POSTGRES_DB=myapp \
		-e POSTGRES_PASSWORD=dev \
		-p 5432:5432 \
		postgres:14 2>/dev/null || echo "Database already running"
	@echo "Running migrations..."
	@sleep 3
	@python manage.py migrate
```

### Step 3: Add Development Target

```makefile
dev: ## Start development environment
	@echo "Starting development environment..."
	@$(MAKE) _ensure-database-running
	@echo "Starting API and frontend..."
	@echo "Press Ctrl+C to stop all services"
	@trap 'kill %1 %2 2>/dev/null' INT; \
		python app.py & \
		npm start & \
		wait

_ensure-database-running:
	@docker ps | grep -q myapp-db || \
		(echo "Starting database..." && $(MAKE) _setup-database)
```

### Step 4: Update README

```markdown
# Updated README.md
## Quick Start

```bash
make setup    # One-time setup
make dev      # Start development
```

For all available commands, run `make help`.

### Detailed Documentation
See our [detailed setup guide](docs/setup.md) for manual setup instructions.
```

### Step 5: Gather Feedback and Iterate

- Ask team members to try `make setup` and `make dev`
- Add targets for common pain points they mention
- Gradually expand to cover more workflows

## Migration 2: From Shell Scripts to Make Targets

**Starting Point**: Collection of bash scripts in `scripts/` directory

**Goal**: Make targets that wrap and enhance existing scripts

### Step 1: Audit Existing Scripts

```bash
scripts/
├── deploy.sh
├── run-tests.sh
├── build-docker.sh
├── backup-db.sh
└── cleanup.sh
```

### Step 2: Create Wrapper Targets

Don't rewrite scripts immediately—wrap them with Make targets:

```makefile
.PHONY: deploy test build backup clean

deploy: ## Deploy to environment (ENVIRONMENT=dev|staging|prod)
	@test -n "$(ENVIRONMENT)" || \
		(echo "Usage: make deploy ENVIRONMENT=dev|staging|prod" && exit 1)
	@echo "Deploying to $(ENVIRONMENT)..."
	@./scripts/deploy.sh $(ENVIRONMENT)

test: ## Run all tests
	@echo "Running test suite..."
	@./scripts/run-tests.sh

build: ## Build Docker image
	@echo "Building Docker image..."
	@./scripts/build-docker.sh

backup: ## Backup database
	@echo "Backing up database..."
	@./scripts/backup-db.sh

clean: ## Clean up resources
	@echo "Cleaning up..."
	@./scripts/cleanup.sh
```

### Step 3: Add Validation and Safety

Enhance scripts with pre-flight checks:

```makefile
deploy: _check-environment _check-tests ## Deploy to environment
	@echo "⚠️  Deploying to $(ENVIRONMENT)"
	@$(MAKE) _confirm-deploy
	@./scripts/deploy.sh $(ENVIRONMENT)
	@echo "✅ Deployment complete"

_check-environment:
	@test -n "$(ENVIRONMENT)" || \
		(echo "Set ENVIRONMENT: make deploy ENVIRONMENT=staging" && exit 1)
	@echo "$(ENVIRONMENT)" | grep -qE '^(dev|staging|prod)$$' || \
		(echo "ENVIRONMENT must be dev, staging, or prod" && exit 1)

_check-tests:
	@echo "Checking if tests pass..."
	@./scripts/run-tests.sh >/dev/null || \
		(echo "❌ Tests must pass before deployment" && exit 1)

_confirm-deploy:
	@if [ "$(ENVIRONMENT)" = "prod" ]; then \
		echo "Deploying to PRODUCTION"; \
		echo -n "Type 'production' to confirm: "; \
		read ans && [ "$$ans" = "production" ]; \
	fi
```

### Step 4: Add Convenience Targets

```makefile
# Convenience aliases for common operations
deploy-dev: ## Deploy to development
	@$(MAKE) deploy ENVIRONMENT=dev

deploy-staging: ## Deploy to staging
	@$(MAKE) deploy ENVIRONMENT=staging

deploy-prod: ## Deploy to production
	@$(MAKE) deploy ENVIRONMENT=prod

# Composite workflows
full-deploy: test build deploy-staging ## Full staging deployment
	@echo "✅ Complete staging deployment finished"
```

### Step 5: Gradually Internalize Scripts

Over time, move script logic into Makefile:

```makefile
# Before: wrapper
backup:
	@./scripts/backup-db.sh

# After: internalized
backup: ## Backup database
	@echo "📦 Backing up database..."
	@timestamp=$$(date +%Y%m%d_%H%M%S); \
	backup_file="backups/db_$$timestamp.sql"; \
	mkdir -p backups; \
	pg_dump $(DATABASE_URL) > $$backup_file; \
	gzip $$backup_file; \
	echo "✅ Backup saved: $$backup_file.gz"
```

## Migration 3: From CI/CD Platform Scripts to Make

**Starting Point**: CI/CD logic embedded in `.gitlab-ci.yml` or `.github/workflows/`

**Goal**: CI/CD files that call Make targets, making workflows locally reproducible

### Step 1: Identify Duplicated Logic

Current state - logic in CI config:

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    steps:
      - name: Build
        run: docker build -t myapp:${{ github.sha }} .
      
      - name: Test
        run: |
          docker run myapp:${{ github.sha }} pytest
      
      - name: Push
        run: |
          docker tag myapp:${{ github.sha }} myapp:latest
          docker push myapp:${{ github.sha }}
          docker push myapp:latest
      
      - name: Deploy
        run: |
          kubectl set image deployment/myapp app=myapp:${{ github.sha }}
          kubectl rollout status deployment/myapp
```

### Step 2: Extract to Make Targets

```makefile
# Makefile
VERSION ?= $(shell git rev-parse --short HEAD)
IMAGE := myapp:$(VERSION)

build: ## Build Docker image
	@echo "Building $(IMAGE)..."
	@docker build -t $(IMAGE) .
	@docker tag $(IMAGE) myapp:latest

test: ## Run tests
	@echo "Running tests..."
	@docker run --rm $(IMAGE) pytest

push: ## Push image to registry
	@echo "Pushing $(IMAGE)..."
	@docker push $(IMAGE)
	@docker push myapp:latest

deploy: ## Deploy to Kubernetes
	@echo "Deploying $(IMAGE)..."
	@kubectl set image deployment/myapp app=$(IMAGE)
	@kubectl rollout status deployment/myapp
	@echo "✅ Deployed $(VERSION)"

ci-deploy: build test push deploy ## Complete CI deployment
	@echo "✅ CI deployment complete"
```

### Step 3: Simplify CI Configuration

```yaml
# .github/workflows/deploy.yml
jobs:
  deploy:
    steps:
      - name: Deploy
        run: make ci-deploy VERSION=${{ github.sha }}
```

### Step 4: Make CI-Specific Adaptations

```makefile
# Detect CI environment
ifdef CI
  # CI-specific behavior
  DOCKER_BUILD_ARGS := --no-cache --progress=plain
  TEST_ARGS := --verbose
else
  # Local development behavior
  DOCKER_BUILD_ARGS := 
  TEST_ARGS := 
endif

build:
	@docker build $(DOCKER_BUILD_ARGS) -t $(IMAGE) .

test:
	@docker run --rm $(IMAGE) pytest $(TEST_ARGS)
```

### Step 5: Enable Local Testing

Now developers can test CI workflows locally:

```bash
# Exactly what runs in CI
make ci-deploy

# Test individual steps
make build
make test
make push
make deploy
```

## Migration 4: From Docker Compose to Make

**Starting Point**: `docker-compose.yml` for orchestration

**Goal**: Make targets that complement Docker Compose

### Step 1: Keep Docker Compose, Add Make Interface

```makefile
# Don't replace docker-compose, enhance it with Make
.PHONY: up down logs restart

up: ## Start all services
	@echo "Starting services..."
	@docker-compose up -d
	@echo "✅ Services started"
	@echo "Logs: make logs"
	@echo "Stop: make down"

down: ## Stop all services
	@echo "Stopping services..."
	@docker-compose down

logs: ## Show logs (SERVICE=name for specific service)
	@if [ -n "$(SERVICE)" ]; then \
		docker-compose logs -f $(SERVICE); \
	else \
		docker-compose logs -f; \
	fi

restart: ## Restart services (SERVICE=name for specific service)
	@if [ -n "$(SERVICE)" ]; then \
		docker-compose restart $(SERVICE); \
	else \
		docker-compose restart; \
	fi
```

### Step 2: Add Development Workflow Helpers

```makefile
dev: up ## Start development environment with logs
	@docker-compose logs -f

shell: ## Get shell in service (make shell SERVICE=api)
	@test -n "$(SERVICE)" || \
		(echo "Usage: make shell SERVICE=api|worker|db" && exit 1)
	@docker-compose exec $(SERVICE) /bin/sh

db-migrate: ## Run database migrations
	@docker-compose exec api python manage.py migrate

db-reset: ## Reset database (WARNING: destroys data)
	@echo "⚠️  This will destroy all data!"
	@echo -n "Continue? [y/N] " && read ans && [ $${ans:-N} = y ]
	@docker-compose down -v
	@$(MAKE) up
	@$(MAKE) db-migrate

test-integration: up ## Run integration tests
	@docker-compose exec api pytest tests/integration/
```

### Step 3: Add Production-Like Workflows

```makefile
# Production deployment (not docker-compose)
deploy-prod: ## Deploy to production Kubernetes
	@$(MAKE) build-prod
	@$(MAKE) push-prod
	@$(MAKE) k8s-deploy

build-prod: ## Build production image
	@docker build -t $(IMAGE):$(VERSION) \
		-f Dockerfile.prod .

push-prod: ## Push to production registry
	@docker push $(IMAGE):$(VERSION)

k8s-deploy: ## Deploy to Kubernetes
	@kubectl apply -f k8s/production/
	@kubectl set image deployment/myapp app=$(IMAGE):$(VERSION)
```

## Migration 5: From Multiple Tools to Unified Interface

**Starting Point**: Multiple tools (Terraform, Helm, kubectl, etc.) with different interfaces

**Goal**: Consistent Make interface across all tools

### Step 1: Create Tool-Specific Targets

```makefile
##@ Infrastructure (Terraform)

infra-plan: ## Plan infrastructure changes
	@cd terraform && terraform plan -var-file=$(ENVIRONMENT).tfvars

infra-apply: ## Apply infrastructure changes
	@cd terraform && terraform apply -var-file=$(ENVIRONMENT).tfvars

infra-destroy: ## Destroy infrastructure
	@cd terraform && terraform destroy -var-file=$(ENVIRONMENT).tfvars

##@ Application (Helm)

app-install: ## Install application with Helm
	@helm install myapp ./charts/myapp \
		-f charts/myapp/values-$(ENVIRONMENT).yaml

app-upgrade: ## Upgrade application
	@helm upgrade myapp ./charts/myapp \
		-f charts/myapp/values-$(ENVIRONMENT).yaml

app-uninstall: ## Uninstall application
	@helm uninstall myapp

##@ Database (kubectl + psql)

db-status: ## Check database status
	@kubectl get statefulset -l app=postgres

db-backup: ## Backup database
	@kubectl exec postgres-0 -- pg_dump $(DB_NAME) > backup.sql

db-restore: ## Restore database from backup
	@kubectl exec -i postgres-0 -- psql $(DB_NAME) < backup.sql
```

### Step 2: Create Composite Workflows

```makefile
##@ Complete Workflows

deploy-all: ## Complete deployment (infra + app)
	@echo "🚀 Complete deployment to $(ENVIRONMENT)"
	@$(MAKE) infra-apply
	@$(MAKE) app-upgrade
	@$(MAKE) db-migrate
	@echo "✅ Deployment complete"

teardown-all: ## Teardown everything
	@echo "⚠️  Destroying all resources in $(ENVIRONMENT)"
	@$(MAKE) _confirm-teardown
	@$(MAKE) app-uninstall
	@$(MAKE) infra-destroy

_confirm-teardown:
	@echo -n "Type '$(ENVIRONMENT)' to confirm: " && \
		read ans && [ "$$ans" = "$(ENVIRONMENT)" ]
```

### Step 3: Add Cross-Tool Validations

```makefile
validate-all: ## Validate all configurations
	@echo "Validating configurations..."
	@$(MAKE) validate-terraform
	@$(MAKE) validate-helm
	@$(MAKE) validate-k8s
	@echo "✅ All validations passed"

validate-terraform:
	@cd terraform && terraform validate

validate-helm:
	@helm lint charts/myapp

validate-k8s:
	@kubectl apply --dry-run=client -f k8s/
```

## Migration 6: From Team Lore to Runbooks

**Starting Point**: Incident response procedures exist only in team members' heads or old Slack threads

**Goal**: Executable runbooks as Make targets

### Step 1: Document One Common Incident

Pick the most common incident and create a runbook:

```makefile
##@ Incident Response

incident-help: ## Show incident runbooks
	@echo "Available Incident Runbooks:"
	@echo "  make incident-high-cpu      # High CPU usage"
	@echo "  make incident-db-slow       # Slow database queries"
	@echo "  make incident-disk-full     # Disk space issues"

incident-high-cpu: ## Diagnose high CPU usage
	@echo "🔍 Investigating high CPU usage..."
	@echo ""
	@echo "1. Top CPU-consuming pods:"
	@kubectl top pods --sort-by=cpu | head -10
	@echo ""
	@echo "2. Container resource limits:"
	@kubectl get pods -o json | \
		jq '.items[] | {name: .metadata.name, cpu: .spec.containers[].resources.limits.cpu}'
	@echo ""
	@echo "💡 Next steps:"
	@echo "   - Check logs: make logs POD=<pod-name>"
	@echo "   - Scale up: make scale REPLICAS=5"
	@echo "   - Restart: make restart-pod POD=<pod-name>"
```

### Step 2: Add More Runbooks Over Time

```makefile
incident-db-slow: ## Diagnose slow database queries
	@echo "🔍 Checking database performance..."
	@echo ""
	@echo "Active queries (>1s):"
	@kubectl exec postgres-0 -- psql -c \
		"SELECT pid, now() - query_start AS duration, query \
		FROM pg_stat_activity \
		WHERE state = 'active' AND now() - query_start > interval '1 second'"
	@echo ""
	@echo "💡 Next steps:"
	@echo "   - Kill query: make db-kill-query PID=<pid>"
	@echo "   - Check connections: make db-connections"

incident-disk-full: ## Handle disk space issues
	@echo "🔍 Checking disk usage..."
	@echo ""
	@kubectl exec deploy/myapp -- df -h
	@echo ""
	@echo "Largest directories:"
	@kubectl exec deploy/myapp -- du -h /var/log | sort -rh | head -5
	@echo ""
	@echo "💡 Cleanup options:"
	@echo "   - Clear logs: make clean-logs"
	@echo "   - Clear cache: make clear-cache"
```

### Step 3: Create Helper Actions

```makefile
# Common remediation actions
scale: ## Scale deployment (make scale REPLICAS=3)
	@kubectl scale deployment/myapp --replicas=$(REPLICAS)

restart-pod: ## Restart specific pod
	@kubectl delete pod $(POD)

db-kill-query: ## Kill database query
	@kubectl exec postgres-0 -- psql -c \
		"SELECT pg_terminate_backend($(PID))"

clean-logs: ## Clean old logs
	@kubectl exec deploy/myapp -- find /var/log -name "*.log" -mtime +7 -delete
```

## General Migration Timeline

### Week 1: Foundation
- Add basic Makefile with `help` target
- Create 3-5 high-value targets (`setup`, `test`, `build`)
- Update README to mention Make
- Announce to team

### Week 2-4: Expansion
- Add targets as team requests them
- Wrap existing scripts
- Enhance with validation and safety checks
- Gather feedback

### Month 2: Integration
- Integrate with CI/CD
- Add environment-specific targets
- Create deployment workflows
- Document patterns

### Month 3+: Advanced
- Add incident runbooks
- Create shared libraries
- Establish conventions
- Scale across teams

## Common Pitfalls to Avoid

**Pitfall 1: Trying to do everything at once**
- Start with 5-10 targets, not 50
- Let complexity grow organically

**Pitfall 2: Breaking existing workflows**
- Run Make and old workflows in parallel initially
- Validate Make produces identical results
- Migrate gradually

**Pitfall 3: Over-abstracting too early**
- Start with simple, concrete targets
- Extract patterns after you see repetition
- Don't build frameworks prematurely

**Pitfall 4: Ignoring team feedback**
- Make is for the team, not just you
- Incorporate suggestions
- Make it easy for others to contribute targets

**Pitfall 5: Perfect is the enemy of good**
- A simple working Makefile is better than no Makefile
- Iterate and improve over time
- Don't wait for the "perfect" design

## Migration Checklist

Before you begin:
- [ ] Identify 3-5 high-value workflows to automate first
- [ ] Check team's Make knowledge level
- [ ] Decide on naming conventions
- [ ] Plan rollout communication

During migration:
- [ ] Start with `help` target
- [ ] Add targets incrementally
- [ ] Keep existing workflows running
- [ ] Validate Make produces same results
- [ ] Update documentation
- [ ] Train team members
- [ ] Gather feedback regularly

After initial migration:
- [ ] Measure adoption (who's using Make?)
- [ ] Track time savings
- [ ] Identify pain points
- [ ] Expand to more workflows
- [ ] Share patterns across teams
- [ ] Iterate based on usage

## Success Metrics

Track these to measure migration success:

**Adoption Metrics**:
- Number of developers using Make regularly
- Number of Make targets per project
- Make target invocations per day

**Impact Metrics**:
- Onboarding time (before/after)
- Time to first successful deployment
- Incident response time (MTTR)
- Documentation freshness

**Quality Metrics**:
- Number of "how do I...?" questions
- Deployment failures due to human error
- Consistency of environments across team

## Next Steps After Migration

Once your basic Makefile is working:

1. **Add More Workflows**: Expand to security scanning, compliance checks, monitoring
2. **Create Shared Libraries**: Extract common patterns for reuse
3. **Build Templates**: Create scaffolding for new projects
4. **Scale Across Teams**: Share patterns organization-wide
5. **Continuous Improvement**: Iterate based on team feedback

Remember: Migration to Make isn't a one-time project—it's an ongoing practice of making workflows more discoverable and executable. Start small, iterate continuously, and let your Makefile grow with your team's needs.