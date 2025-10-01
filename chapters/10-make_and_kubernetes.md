# Chapter 10: Make and Kubernetes - Discoverable Deployments

\chaptersubtitle{Simplifying Kubernetes complexity through discoverable deployment workflows that any team member can understand and execute.}

Kubernetes has become the foundation of modern cloud-native infrastructure, but its power comes with overwhelming complexity. YAML manifests, kubectl commands, namespace management, resource dependencies, health checks, rollback procedures—the cognitive load can be crushing. Teams often resort to complex shell scripts, struggle with inconsistent deployments, or rely on heavyweight platforms that obscure the underlying operations.

Make provides an elegant solution by creating a discoverable orchestration layer over Kubernetes operations. Instead of memorizing intricate kubectl incantations or navigating maze-like deployment scripts, team members can simply run `make deploy`, `make status`, or `make rollback`. The Makefile becomes both the documentation and the implementation of your Kubernetes deployment strategy.

This chapter demonstrates how to create maintainable, reliable Kubernetes workflows using Make. We'll explore patterns for manifest generation, environment-specific deployments, health checks, and Helm chart management.

\newpage
## Discovering Kubernetes Operations

The traditional approach to Kubernetes involves remembering complex commands:

```bash
# Development deployment
kubectl apply -f k8s/development/ --namespace myapp-dev
kubectl set image deployment/myapp app=myapp:v1.2.3-dev --namespace myapp-dev
kubectl rollout status deployment/myapp --namespace myapp-dev

# Production deployment
kubectl apply -f k8s/production/ --namespace myapp-prod
kubectl set image deployment/myapp app=myapp:v1.2.3 --namespace myapp-prod
kubectl rollout status deployment/myapp --namespace myapp-prod --timeout=600s
kubectl port-forward service/myapp 8080:80 --namespace myapp-prod &
curl http://localhost:8080/health
```

Each command requires remembering namespace names, image tags, timeout values, and verification steps. Different engineers follow different procedures. Documentation drifts.

\newpage
Here's the discovery-based approach:

```makefile
.DEFAULT_GOAL := help

APP_NAME := myapp
VERSION := $(shell git describe --tags --always --dirty)
ENVIRONMENT ?= development
NAMESPACE := $(APP_NAME)-$(ENVIRONMENT)

help: ## Show Kubernetes operations
	@echo "Kubernetes Operations"
	@echo "====================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; \
		{printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "Current: $(APP_NAME) v$(VERSION) → $(ENVIRONMENT)"

deploy: ## Deploy to configured environment
	@echo "Deploying to $(ENVIRONMENT)..."
	@./scripts/k8s-deploy.sh $(ENVIRONMENT) $(VERSION)

status: ## Show deployment status
	@./scripts/k8s-status.sh $(ENVIRONMENT)

logs: ## Show application logs
	@./scripts/k8s-logs.sh $(ENVIRONMENT)

rollback: ## Rollback to previous version
	@./scripts/k8s-rollback.sh $(ENVIRONMENT)
```

Running `make help` shows available operations. The workflow reveals itself, and complexity lives in scripts rather than documentation.

\newpage
## Discovering Environment-Specific Deployments

Different environments need different deployment strategies. Make this discoverable:

```makefile
deploy: ## Show deployment options
	@echo "Deployment Options"
	@echo "=================="
	@echo "  make deploy-dev        - Development (fast)"
	@echo "  make deploy-staging    - Staging (validated)"
	@echo "  make deploy-prod       - Production (safe)"
	@echo ""
	@echo "Or set ENVIRONMENT:"
	@echo "  make deploy ENVIRONMENT=staging"

deploy-dev: ## Deploy to development
	@echo "Deploying to development..."
	@./scripts/deploy-dev.sh $(VERSION)

deploy-staging: ## Deploy to staging
	@echo "Deploying to staging..."
	@./scripts/deploy-staging.sh $(VERSION)

deploy-prod: ## Deploy to production
	@echo "Deploying to PRODUCTION"
	@echo -n "Type 'production' to confirm: "
	@read confirm && [ "$$confirm" = "production" ]
	@./scripts/deploy-production.sh $(VERSION)
```

Each environment has appropriate safety checks built in. The workflow is discoverable but implementations can differ.

\newpage
## Discovering Manifest Generation

Static YAML becomes maintenance nightmares. Make manifest generation discoverable:

```makefile
manifests: ## Show manifest operations
	@echo "Manifest Operations"
	@echo "==================="
	@echo "  make manifests-generate    - Generate from templates"
	@echo "  make manifests-validate    - Validate manifests"
	@echo "  make manifests-diff        - Show differences"
	@echo ""
	@echo "Target: $(ENVIRONMENT)"

manifests-generate: ## Generate Kubernetes manifests
	@echo "Generating manifests for $(ENVIRONMENT)..."
	@./scripts/generate-manifests.sh $(ENVIRONMENT) $(VERSION)

manifests-validate: ## Validate manifests
	@echo "Validating manifests..."
	@./scripts/validate-manifests.sh $(ENVIRONMENT)

manifests-diff: ## Show manifest differences
	@echo "Comparing with deployed manifests..."
	@./scripts/diff-manifests.sh $(ENVIRONMENT)
```

The manifest workflow is discoverable. Developers can generate, validate, and compare before deploying.

\newpage
## Discovering Rollout Management

Deployments need careful monitoring and rollback capabilities:

```makefile
rollout: ## Show rollout operations
	@echo "Rollout Operations"
	@echo "=================="
	@echo "  make rollout-status     - Check rollout status"
	@echo "  make rollout-history    - Show history"
	@echo "  make rollback           - Rollback deployment"
	@echo "  make rollback-to        - Rollback to revision"

rollout-status: ## Check rollout status
	@echo "Checking rollout status..."
	@./scripts/rollout-status.sh $(ENVIRONMENT)

rollout-history: ## Show rollout history
	@./scripts/rollout-history.sh $(ENVIRONMENT)

rollback: ## Rollback to previous version
	@echo "Rolling back $(ENVIRONMENT)..."
	@./scripts/rollback.sh $(ENVIRONMENT)

rollback-to: ## Rollback to specific revision
	@echo "Available revisions:"
	@$(MAKE) rollout-history
	@echo -n "Revision: "
	@read rev && ./scripts/rollback-to.sh $(ENVIRONMENT) $$rev
```

Rollback operations are discoverable and safe. Each command explains what it does.

\newpage
## Discovering Helm Operations

Helm adds another layer of complexity. Make it discoverable:

```makefile
helm: ## Show Helm operations
	@echo "Helm Operations"
	@echo "==============="
	@echo "  make helm-install      - Install release"
	@echo "  make helm-upgrade      - Upgrade release"
	@echo "  make helm-rollback     - Rollback release"
	@echo "  make helm-status       - Show status"
	@echo ""
	@echo "Release: $(APP_NAME)-$(ENVIRONMENT)"

helm-install: ## Install Helm release
	@echo "Installing Helm release..."
	@./scripts/helm-install.sh $(ENVIRONMENT) $(VERSION)

helm-upgrade: ## Upgrade Helm release
	@echo "Upgrading Helm release..."
	@./scripts/helm-upgrade.sh $(ENVIRONMENT) $(VERSION)

helm-rollback: ## Rollback Helm release
	@echo "Rolling back Helm release..."
	@./scripts/helm-rollback.sh $(ENVIRONMENT)

helm-status: ## Show Helm status
	@./scripts/helm-status.sh $(ENVIRONMENT)
```

Helm operations follow the same discovery pattern. Running `make helm` shows what's available.

\newpage
## Discovering Troubleshooting Operations

When things go wrong, troubleshooting needs to be discoverable:

```makefile
debug: ## Show debugging operations
	@echo "Debug Operations"
	@echo "================"
	@echo "  make logs              - Show logs"
	@echo "  make logs-previous     - Previous pod logs"
	@echo "  make shell             - Get pod shell"
	@echo "  make debug-describe    - Describe resources"
	@echo "  make debug-events      - Show events"

logs: ## Show application logs
	@./scripts/show-logs.sh $(ENVIRONMENT)

logs-previous: ## Show previous pod logs
	@./scripts/show-logs-previous.sh $(ENVIRONMENT)

shell: ## Get shell in pod
	@./scripts/get-shell.sh $(ENVIRONMENT)

debug-describe: ## Describe Kubernetes resources
	@./scripts/debug-describe.sh $(ENVIRONMENT)

debug-events: ## Show recent events
	@./scripts/debug-events.sh $(ENVIRONMENT)
```

Debugging operations are organized and discoverable. Engineers can find the right tool quickly.

\newpage
## Discovering Resource Management

Kubernetes resources need management:

```makefile
resources: ## Show resource operations
	@echo "Resource Operations"
	@echo "==================="
	@echo "  make scale             - Scale replicas"
	@echo "  make restart           - Restart deployment"
	@echo "  make resource-usage    - Show resource usage"
	@echo "  make port-forward      - Port forward to local"

scale: ## Scale deployment
	@echo "Current replicas:"
	@./scripts/show-replicas.sh $(ENVIRONMENT)
	@echo -n "New count: "
	@read count && ./scripts/scale.sh $(ENVIRONMENT) $$count

restart: ## Restart deployment
	@echo "Restarting $(ENVIRONMENT)..."
	@./scripts/restart.sh $(ENVIRONMENT)

resource-usage: ## Show resource usage
	@./scripts/resource-usage.sh $(ENVIRONMENT)

port-forward: ## Port forward to application
	@echo "Port forwarding to localhost:8080..."
	@./scripts/port-forward.sh $(ENVIRONMENT)
```

Resource management is discoverable. Each operation is independently runnable.

\newpage
## Discovering Environment Management

Creating and destroying environments should be explicit:

```makefile
environments: ## Show environment operations
	@echo "Environment Operations"
	@echo "======================"
	@echo "  make env-create        - Create environment"
	@echo "  make env-destroy       - Destroy environment"
	@echo "  make env-list          - List environments"
	@echo "  make env-status        - Environment status"

env-create: ## Create new environment
	@echo "Creating $(ENVIRONMENT)..."
	@./scripts/env-create.sh $(ENVIRONMENT)

env-destroy: ## Destroy environment
	@echo "Destroying $(ENVIRONMENT)"
	@echo -n "Type environment name to confirm: "
	@read confirm && [ "$$confirm" = "$(ENVIRONMENT)" ]
	@./scripts/env-destroy.sh $(ENVIRONMENT)

env-list: ## List all environments
	@./scripts/env-list.sh

env-status: ## Show environment status
	@./scripts/env-status.sh $(ENVIRONMENT)
```

Environment lifecycle is discoverable and protected.

\newpage
## Real-World Example

### Before: Complex kubectl Commands

```
README.md:
  "To deploy to staging:
   1. kubectl apply -f k8s/staging/
   2. kubectl set image deployment/myapp app=myapp:$(git describe --tags)
   3. Wait for rollout: kubectl rollout status...
   4. Check health: kubectl port-forward...
   5. If problems, rollback: kubectl rollout undo..."

.gitlab-ci.yml:
  "Different commands with different flags..."

Result: Inconsistency, errors, confusion
```

\newpage
### After: Discoverable Workflow

```makefile
help: ## Show available operations
	@echo "Kubernetes Operations"
	@echo "  make deploy          - Deploy to environment"
	@echo "  make status          - Check status"
	@echo "  make logs            - Show logs"
	@echo "  make rollback        - Rollback deployment"

deploy: ## Deploy to configured environment
	@./scripts/k8s-deploy.sh $(ENVIRONMENT) $(VERSION)
	@echo "Deployed to $(ENVIRONMENT)"
	@echo "  Check status: make status"

status: ## Show deployment status
	@./scripts/k8s-status.sh $(ENVIRONMENT)

logs: ## Show logs
	@./scripts/k8s-logs.sh $(ENVIRONMENT)

rollback: ## Rollback deployment
	@./scripts/k8s-rollback.sh $(ENVIRONMENT)
```

One interface, works everywhere. CI and local use identical commands. New team members discover the workflow through `make help`.

\newpage
## Key Patterns

Make Kubernetes workflows discoverable through:

1. **Progressive menus** - `make deploy` shows deployment options, `make debug` shows debugging tools
2. **Environment awareness** - Same interface adapts to dev/staging/prod
3. **Built-in safety** - Production requires confirmation, dangerous operations are explicit
4. **Script extraction** - Complex kubectl commands live in scripts
5. **Clear guidance** - Each operation suggests next steps

## Key Takeaways

Make transforms Kubernetes operations from scattered commands into discoverable workflows:

1. **Discoverability**: `make help` reveals operations
2. **Consistency**: Same commands work across environments
3. **Safety**: Built-in validation and confirmation
4. **Composability**: Complex workflows from simple targets
5. **Teachability**: New team members learn by discovering

The goal isn't to hide Kubernetes complexity—it's to make it discoverable. Engineers can see available operations, understand environment-specific behaviors, and follow guided workflows.

Most importantly, Kubernetes operations become team knowledge rather than individual expertise. That complex deployment procedure? It's `make deploy`. The multi-step rollback process? It's `make rollback`. The workflow is captured, discoverable, and improvable by anyone on the team.

The pattern is consistent across all infrastructure: create discovery menus, extract complexity to scripts, provide clear interfaces, suggest next steps. Whether it's Docker, Kubernetes, Terraform, or any other tool, the discovery approach makes workflows accessible to everyone.