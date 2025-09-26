# Chapter 10: Make and Kubernetes - Orchestrating Cloud-Native Deployments

*Simplifying Kubernetes complexity through Make-based deployment workflows that any team member can understand and execute.*

Kubernetes has become the foundation of modern cloud-native infrastructure, but its power comes with overwhelming complexity. YAML manifests, kubectl commands, namespace management, resource dependencies, health checks, rollback procedures—the cognitive load can be crushing. Teams often resort to complex shell scripts, struggle with inconsistent deployments, or rely on heavyweight platforms that obscure the underlying operations.

Make provides an elegant solution by creating a discoverable orchestration layer over Kubernetes operations. Instead of memorizing intricate kubectl incantations or navigating maze-like deployment scripts, team members can simply run `make deploy`, `make status`, or `make rollback`. The Makefile becomes both the documentation and the implementation of your Kubernetes deployment strategy.

This chapter demonstrates how to create maintainable, reliable Kubernetes workflows using Make. We'll explore patterns for manifest generation, environment-specific deployments, health checks, and Helm chart management. Advanced topics like database migrations, comprehensive monitoring setup, and CI/CD integration are covered in dedicated chapters (12, 13, and 11 respectively).

> ** Start Simple: Essential Kubernetes + Make Patterns**
> 
> Master these fundamental patterns before exploring advanced Kubernetes orchestration:
> 
> 1. **Basic deployment**: `deploy: build push apply` ensures images are ready before Kubernetes updates
> 2. **Environment isolation**: Use separate namespaces and target patterns for different environments
> 3. **Health verification**: Always check rollout status after deployments
> 4. **Configuration management**: Generate manifests from templates rather than maintaining static YAML
> 5. **Rollback capability**: Provide simple commands for when deployments go wrong
> 
> These patterns handle 80% of Kubernetes deployment scenarios. Advanced techniques like service mesh integration, complex deployment strategies, and comprehensive monitoring are covered in later chapters (11, 12, and 13).

## Kubernetes Manifest Generation and Validation

### The Challenge of Static YAML Manifests

Static Kubernetes YAML manifests become maintenance nightmares as applications grow. Different environments need different configurations, resource limits vary based on deployment targets, and keeping manifests synchronized with application changes requires constant manual updates.

Make enables **dynamic manifest generation** that adapts to different environments while maintaining consistency:

```makefile
# =============================================================================
# Dynamic Kubernetes Manifest Generation
# =============================================================================

# Configuration
APP_NAME ?= myapp
VERSION ?= $(shell git describe --tags --always --dirty)
ENVIRONMENT ?= development
NAMESPACE = $(APP_NAME)-$(ENVIRONMENT)

# Registry and image configuration
REGISTRY ?= registry.company.com
IMAGE_TAG = $(REGISTRY)/$(APP_NAME):$(VERSION)

# Environment-specific configuration
ifeq ($(ENVIRONMENT),production)
  REPLICAS ?= 3
  CPU_REQUEST ?= 200m
  MEMORY_REQUEST ?= 256Mi
  CPU_LIMIT ?= 500m
  MEMORY_LIMIT ?= 512Mi
else ifeq ($(ENVIRONMENT),staging)
  REPLICAS ?= 2
  CPU_REQUEST ?= 100m
  MEMORY_REQUEST ?= 128Mi
  CPU_LIMIT ?= 300m
  MEMORY_LIMIT ?= 256Mi
else
  REPLICAS ?= 1
  CPU_REQUEST ?= 50m
  MEMORY_REQUEST ?= 64Mi
  CPU_LIMIT ?= 200m
  MEMORY_LIMIT ?= 128Mi
endif

# Directories
TEMPLATES_DIR = k8s/templates
MANIFESTS_DIR = k8s/manifests

.PHONY: generate-manifests validate-manifests clean-manifests

# Generate manifests from templates
generate-manifests: ##  Generate Kubernetes manifests
	@echo " Generating Kubernetes manifests for $(ENVIRONMENT)..."
	@mkdir -p $(MANIFESTS_DIR)
	@$(MAKE) generate-deployment
	@$(MAKE) generate-service  
	@$(MAKE) generate-ingress
	@$(MAKE) generate-configmap
	@$(MAKE) generate-secrets
	@echo " Manifests generated in $(MANIFESTS_DIR)/"

# Generate individual manifest types
generate-deployment: ## Generate deployment manifest
	@echo "Generating deployment manifest..."
	@envsubst < $(TEMPLATES_DIR)/deployment.yaml.template > $(MANIFESTS_DIR)/deployment.yaml
	@echo " Deployment: $(REPLICAS) replicas, $(IMAGE_TAG)"

generate-service: ## Generate service manifest
	@echo "Generating service manifest..."
	@envsubst < $(TEMPLATES_DIR)/service.yaml.template > $(MANIFESTS_DIR)/service.yaml

generate-ingress: ## Generate ingress manifest
	@echo "Generating ingress manifest..."
	@envsubst < $(TEMPLATES_DIR)/ingress.yaml.template > $(MANIFESTS_DIR)/ingress.yaml

generate-configmap: ## Generate configmap manifest
	@echo "Generating configmap manifest..."
	@envsubst < $(TEMPLATES_DIR)/configmap.yaml.template > $(MANIFESTS_DIR)/configmap.yaml

generate-secrets: ## Generate secrets manifest
	@echo "Generating secrets manifest..."
	@kubectl create secret generic $(APP_NAME)-secrets \
		--from-env-file=config/$(ENVIRONMENT).env \
		--dry-run=client -o yaml > $(MANIFESTS_DIR)/secrets.yaml

# Validate generated manifests
validate-manifests: generate-manifests ##  Validate Kubernetes manifests
	@echo " Validating Kubernetes manifests..."
	@for manifest in $(MANIFESTS_DIR)/*.yaml; do \
		echo "Validating $$manifest..."; \
		kubectl apply --dry-run=client --validate=true -f $$manifest >/dev/null || exit 1; \
	done
	@echo " All manifests are valid"

# Advanced validation with kubeval
validate-with-kubeval: generate-manifests ##  Validate with kubeval
	@echo " Validating with kubeval..."
	@for manifest in $(MANIFESTS_DIR)/*.yaml; do \
		kubeval $$manifest || exit 1; \
	done

# Clean generated manifests
clean-manifests: ##  Clean generated manifests
	@rm -rf $(MANIFESTS_DIR)
	@echo " Generated manifests cleaned"
```

### Template-Based Configuration Management

Create flexible templates that adapt to different environments and configurations:

**k8s/templates/deployment.yaml.template:**
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ${APP_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
    version: ${VERSION}
    environment: ${ENVIRONMENT}
spec:
  replicas: ${REPLICAS}
  selector:
    matchLabels:
      app: ${APP_NAME}
  template:
    metadata:
      labels:
        app: ${APP_NAME}
        version: ${VERSION}
        environment: ${ENVIRONMENT}
    spec:
      containers:
      - name: app
        image: ${IMAGE_TAG}
        ports:
        - containerPort: 8080
        resources:
          requests:
            cpu: ${CPU_REQUEST}
            memory: ${MEMORY_REQUEST}
          limits:
            cpu: ${CPU_LIMIT}
            memory: ${MEMORY_LIMIT}
        env:
        - name: ENVIRONMENT
          value: ${ENVIRONMENT}
        - name: VERSION
          value: ${VERSION}
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
```

**k8s/templates/service.yaml.template:**
```yaml
apiVersion: v1
kind: Service
metadata:
  name: ${APP_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
spec:
  selector:
    app: ${APP_NAME}
  ports:
  - port: 80
    targetPort: 8080
    protocol: TCP
    name: http
  type: ClusterIP
```

**k8s/templates/ingress.yaml.template:**
```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: ${APP_NAME}
  namespace: ${NAMESPACE}
  labels:
    app: ${APP_NAME}
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: ${APP_NAME}-${ENVIRONMENT}.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: ${APP_NAME}
            port:
              number: 80
```

## Environment-Specific Deployment Strategies

### Multi-Environment Orchestration

Create sophisticated deployment strategies that adapt to different environments:

```makefile
# =============================================================================
# Environment-Specific Deployment Strategies
# =============================================================================

# Environment validation
validate-environment: ##  Validate environment configuration
	@echo " Validating $(ENVIRONMENT) environment..."
	@case "$(ENVIRONMENT)" in \
		development|staging|production) ;; \
		*) echo " Invalid environment: $(ENVIRONMENT)" && exit 1 ;; \
	esac
	@$(MAKE) validate-cluster-access
	@$(MAKE) validate-namespace-exists
	@$(MAKE) validate-secrets-available

validate-cluster-access: ##  Validate cluster access
	@kubectl cluster-info >/dev/null || (echo " Cannot access Kubernetes cluster" && exit 1)
	@echo " Cluster access verified"

validate-namespace-exists: ##  Ensure namespace exists
	@kubectl get namespace $(NAMESPACE) >/dev/null 2>&1 || \
		(echo " Creating namespace $(NAMESPACE)" && kubectl create namespace $(NAMESPACE))

validate-secrets-available: ##  Validate required secrets exist
	@if [ "$(ENVIRONMENT)" != "development" ]; then \
		kubectl get secret $(APP_NAME)-secrets -n $(NAMESPACE) >/dev/null 2>&1 || \
		(echo " Required secrets not found in $(NAMESPACE)" && exit 1); \
	fi

# Environment-specific deployment strategies
deploy: validate-environment deploy-$(ENVIRONMENT) ##  Deploy to configured environment

deploy-development: build push generate-manifests ##  Development deployment (fast, minimal checks)
	@echo " Development deployment..."
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@$(MAKE) wait-for-rollout-fast
	@echo " Development deployment completed"

deploy-staging: build push generate-manifests validate-manifests ##  Staging deployment (full validation)
	@echo " Staging deployment..."
	@$(MAKE) pre-deployment-checks
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@$(MAKE) wait-for-rollout
	@$(MAKE) smoke-test
	@echo " Staging deployment completed"

deploy-production: build push generate-manifests validate-manifests ##  Production deployment (maximum safety)
	@echo " Production deployment..."
	@$(MAKE) pre-production-checks
	@$(MAKE) backup-current-state
	@echo " Type 'production' to confirm deployment: " && read confirm && [ "$$confirm" = "production" ]
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@$(MAKE) wait-for-rollout-production
	@$(MAKE) verify-production-deployment
	@echo " Production deployment completed"

# Pre-deployment checks
pre-deployment-checks: ##  Run pre-deployment checks
	@echo " Running pre-deployment checks..."
	@$(MAKE) validate-manifests
	@$(MAKE) check-resource-requirements
	@$(MAKE) verify-image-exists

pre-production-checks: pre-deployment-checks ##  Additional production checks
	@echo " Running production-specific checks..."
	@$(MAKE) security-scan-image
	@$(MAKE) validate-backup-systems
	@echo " Production checks completed"

# Utility checks
check-resource-requirements: ##  Validate cluster has sufficient resources
	@echo " Checking resource requirements..."
	@kubectl top nodes >/dev/null 2>&1 || echo " Cannot verify resource usage (metrics-server not available)"

verify-image-exists: ##  Verify Docker image exists in registry
	@echo " Verifying image exists: $(IMAGE_TAG)"
	@docker manifest inspect $(IMAGE_TAG) >/dev/null 2>&1 || \
		(echo " Image not found: $(IMAGE_TAG)" && exit 1)
	@echo " Image verified"

security-scan-image: ##  Run security scan on image
	@echo " Running security scan..."
	@command -v trivy >/dev/null && trivy image $(IMAGE_TAG) || echo " Trivy not available, skipping scan"

validate-backup-systems: ##  Validate backup systems are ready
	@echo " Checking backup systems..."
	@echo " Backup validation not implemented - see Chapter 12 for database backup patterns"
```

### Pattern Rules for Multiple Environments

Use Make's pattern rules to handle multiple environments elegantly:

```makefile
# =============================================================================
# Pattern Rules for Environment Management
# =============================================================================

# Deploy to specific environment using pattern rule
deploy-%: ##  Deploy to specific environment
	@echo " Deploying to $* environment..."
	@ENVIRONMENT=$* $(MAKE) deploy

# Show status for specific environment
status-%: ##  Show status for specific environment
	@ENVIRONMENT=$* $(MAKE) status

# Get logs for specific environment
logs-%: ##  Show logs for specific environment
	@ENVIRONMENT=$* $(MAKE) logs

# Rollback specific environment
rollback-%: ##  Rollback specific environment
	@ENVIRONMENT=$* $(MAKE) rollback

# Example usage:
# make deploy-staging
# make status-production
# make logs-development
```

## Rollout Management and Health Checks

### Comprehensive Rollout Monitoring

Implement robust rollout management with appropriate monitoring for each environment:

```makefile
# =============================================================================
# Rollout Management and Health Checks
# =============================================================================

# Rollout monitoring
wait-for-rollout: ##  Wait for rollout to complete
	@echo " Waiting for rollout to complete..."
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s
	@$(MAKE) verify-deployment-health
	@echo " Rollout completed successfully"

wait-for-rollout-fast: ##  Quick rollout wait (development)
	@echo " Quick rollout check..."
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=60s
	@echo " Development rollout completed"

wait-for-rollout-production: ##  Production rollout with extended monitoring
	@echo " Production rollout monitoring..."
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=600s
	@$(MAKE) verify-deployment-health
	@$(MAKE) extended-health-monitoring
	@echo " Production rollout completed"

# Health verification
verify-deployment-health: ##  Verify deployment health
	@echo " Verifying deployment health..."
	@READY_REPLICAS=$$(kubectl get deployment $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.status.readyReplicas}'); \
	DESIRED_REPLICAS=$$(kubectl get deployment $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.replicas}'); \
	if [ "$$READY_REPLICAS" != "$$DESIRED_REPLICAS" ]; then \
		echo " Health check failed: $$READY_REPLICAS/$$DESIRED_REPLICAS replicas ready"; \
		exit 1; \
	fi; \
	echo " All $$READY_REPLICAS replicas are healthy"

extended-health-monitoring: ##  Extended health monitoring for production
	@echo " Extended health monitoring..."
	@for i in $$(seq 1 6); do \
		echo "Health check $$i/6..."; \
		$(MAKE) app-health-check || (echo " Application health check failed" && exit 1); \
		sleep 10; \
	done
	@echo " Extended health monitoring passed"

app-health-check: ##  Application-specific health check
	@echo " Checking application health..."
	@kubectl port-forward service/$(APP_NAME) 8080:80 -n $(NAMESPACE) >/dev/null 2>&1 &
	@PF_PID=$$!; \
	sleep 2; \
	curl -f -m 10 http://localhost:8080/health >/dev/null && \
		echo " Application health check passed" || \
		echo " Application health check failed"; \
	kill $$PF_PID 2>/dev/null || true

# Smoke testing
smoke-test: ##  Run smoke tests
	@echo " Running smoke tests..."
	@$(MAKE) app-health-check
	@echo " Smoke tests completed"

verify-production-deployment: ##  Comprehensive production verification
	@echo " Running production verification..."
	@$(MAKE) verify-deployment-health
	@$(MAKE) smoke-test
	@echo " Production verification completed"

# Rollback operations
rollback: ##  Rollback to previous version
	@echo " Rolling back to previous version..."
	@kubectl rollout undo deployment/$(APP_NAME) -n $(NAMESPACE)
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s
	@$(MAKE) verify-deployment-health
	@echo " Rollback completed"

rollback-to-revision: ##  Rollback to specific revision
	@echo "Available revisions:"
	@kubectl rollout history deployment/$(APP_NAME) -n $(NAMESPACE)
	@echo ""
	@read -p "Revision number: " REVISION; \
	echo " Rolling back to revision $$REVISION..."; \
	kubectl rollout undo deployment/$(APP_NAME) -n $(NAMESPACE) --to-revision=$$REVISION; \
	kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s; \
	$(MAKE) verify-deployment-health

# Deployment history and status
rollout-history: ##  Show rollout history
	@kubectl rollout history deployment/$(APP_NAME) -n $(NAMESPACE)

rollout-pause: ##  Pause rollout
	@kubectl rollout pause deployment/$(APP_NAME) -n $(NAMESPACE)
	@echo " Rollout paused"

rollout-resume: ## ▶ Resume rollout
	@kubectl rollout resume deployment/$(APP_NAME) -n $(NAMESPACE)
	@echo "▶ Rollout resumed"
```

## Helm Chart Management and Customization

### Basic Helm Integration

Integrate Helm charts with Make for better orchestration:

```makefile
# =============================================================================
# Helm Chart Management
# =============================================================================

# Helm configuration
HELM_CHART ?= ./helm/$(APP_NAME)
HELM_RELEASE_NAME ?= $(APP_NAME)-$(ENVIRONMENT)
HELM_VALUES_FILE ?= helm/values-$(ENVIRONMENT).yaml

.PHONY: helm-lint helm-template helm-install helm-upgrade helm-uninstall

# Helm chart operations
helm-lint: ##  Lint Helm chart
	@echo " Linting Helm chart..."
	@helm lint $(HELM_CHART)
	@echo " Helm chart is valid"

helm-template: ##  Generate templates from Helm chart
	@echo " Generating templates from Helm chart..."
	@mkdir -p $(MANIFESTS_DIR)
	@helm template $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--output-dir $(MANIFESTS_DIR)
	@echo " Templates generated in $(MANIFESTS_DIR)/"

helm-dry-run: ##  Dry run Helm installation
	@echo " Helm dry run..."
	@helm install $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--dry-run --debug

helm-install: build push ##  Install with Helm
	@echo " Installing with Helm..."
	@$(MAKE) validate-environment
	@helm install $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--create-namespace \
		--wait --timeout=300s
	@$(MAKE) verify-helm-deployment
	@echo " Helm installation completed"

helm-upgrade: build push ##  Upgrade with Helm
	@echo " Upgrading with Helm..."
	@helm upgrade $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--wait --timeout=300s
	@$(MAKE) verify-helm-deployment
	@echo " Helm upgrade completed"

helm-uninstall: ##  Uninstall Helm release
	@echo " Type the release name '$(HELM_RELEASE_NAME)' to confirm uninstall: " && read confirm && [ "$$confirm" = "$(HELM_RELEASE_NAME)" ]
	@helm uninstall $(HELM_RELEASE_NAME) -n $(NAMESPACE)
	@echo " Helm release uninstalled"

# Helm utilities
helm-status: ##  Show Helm release status
	@helm status $(HELM_RELEASE_NAME) -n $(NAMESPACE)

helm-get-values: ##  Show Helm values
	@helm get values $(HELM_RELEASE_NAME) -n $(NAMESPACE)

helm-history: ##  Show Helm release history
	@helm history $(HELM_RELEASE_NAME) -n $(NAMESPACE)

helm-rollback: ##  Rollback Helm release
	@echo "Available revisions:"
	@helm history $(HELM_RELEASE_NAME) -n $(NAMESPACE)
	@echo ""
	@read -p "Revision (or 'previous' for last): " REVISION; \
	if [ "$$REVISION" = "previous" ]; then \
		helm rollback $(HELM_RELEASE_NAME) -n $(NAMESPACE); \
	else \
		helm rollback $(HELM_RELEASE_NAME) $$REVISION -n $(NAMESPACE); \
	fi; \
	$(MAKE) verify-helm-deployment

verify-helm-deployment: ##  Verify Helm deployment
	@echo " Verifying Helm deployment..."
	@helm status $(HELM_RELEASE_NAME) -n $(NAMESPACE) | grep -q "STATUS: deployed" || \
		(echo " Helm deployment not in deployed state" && exit 1)
	@$(MAKE) verify-deployment-health
	@echo " Helm deployment verification completed"
```

### Advanced Helm Workflows

Create sophisticated Helm workflows with dependency management and multi-chart deployments:

```makefile
# =============================================================================
# Advanced Helm Workflows
# =============================================================================

# Helm dependencies
helm-dep-update: ##  Update Helm dependencies
	@echo " Updating Helm dependencies..."
	@helm dependency update $(HELM_CHART)
	@echo " Helm dependencies updated"

# Multi-chart deployment for complex applications
deploy-full-stack: ##  Deploy full application stack with Helm
	@echo " Deploying full application stack..."
	@$(MAKE) helm-install-infrastructure
	@$(MAKE) helm-install-database
	@$(MAKE) helm-install-app
	@echo " Full stack deployment completed"

helm-install-infrastructure: ##  Install infrastructure components
	@echo " Installing infrastructure components..."
	@if [ -d "helm/infrastructure" ]; then \
		helm upgrade --install $(APP_NAME)-infra helm/infrastructure \
			--namespace $(NAMESPACE)-infra \
			--create-namespace \
			--values helm/infrastructure/values-$(ENVIRONMENT).yaml \
			--wait --timeout=600s; \
	else \
		echo " No infrastructure chart found, skipping"; \
	fi

helm-install-database: ##  Install database components
	@echo " Installing database components..."
	@if [ -d "helm/database" ]; then \
		helm upgrade --install $(APP_NAME)-db helm/database \
			--namespace $(NAMESPACE) \
			--create-namespace \
			--values helm/database/values-$(ENVIRONMENT).yaml \
			--wait --timeout=300s; \
	else \
		echo " No database chart found, skipping"; \
	fi

helm-install-app: helm-install-database ##  Install application (depends on database)
	@$(MAKE) helm-upgrade

# Helm testing
helm-test: ##  Run Helm tests
	@echo " Running Helm tests..."
	@helm test $(HELM_RELEASE_NAME) -n $(NAMESPACE) --timeout=300s

# Environment-specific Helm workflows
helm-deploy: helm-deploy-$(ENVIRONMENT) ##  Environment-specific Helm deployment

helm-deploy-development: helm-lint helm-install ##  Development Helm deployment

helm-deploy-staging: helm-lint helm-dry-run helm-upgrade helm-test ##  Staging Helm deployment

helm-deploy-production: helm-lint helm-dry-run backup-current-state helm-upgrade helm-test ##  Production Helm deployment
	@$(MAKE) extended-health-monitoring
	@echo " Production Helm deployment completed"

# Backup current state before deployment
backup-current-state: ##  Backup current Kubernetes state
	@echo " Backing up current state..."
	@mkdir -p backups/$(ENVIRONMENT)
	@kubectl get all -n $(NAMESPACE) -o yaml > backups/$(ENVIRONMENT)/backup-$(shell date +%Y%m%d-%H%M%S).yaml 2>/dev/null || echo " Namespace $(NAMESPACE) not found"
	@echo " Backup completed"
```

## Basic Operations and Troubleshooting

### Essential Kubernetes Operations

Provide essential operations that every team member needs:

```makefile
# =============================================================================
# Essential Kubernetes Operations
# =============================================================================

.PHONY: status logs shell debug restart scale

# Status and monitoring
status: ##  Show deployment status
	@echo " Deployment Status for $(APP_NAME) in $(ENVIRONMENT)"
	@echo "================================================="
	@echo ""
	@echo "Namespace:"
	@kubectl get namespace $(NAMESPACE) 2>/dev/null || echo " Namespace not found"
	@echo ""
	@echo "Deployments:"
	@kubectl get deployments -n $(NAMESPACE) -o wide 2>/dev/null || echo " No deployments found"
	@echo ""
	@echo "Pods:"
	@kubectl get pods -n $(NAMESPACE) -o wide 2>/dev/null || echo " No pods found"
	@echo ""
	@echo "Services:"
	@kubectl get services -n $(NAMESPACE) 2>/dev/null || echo " No services found"
	@echo ""
	@echo "Ingress:"
	@kubectl get ingress -n $(NAMESPACE) 2>/dev/null || echo " No ingress found"

logs: ##  Show application logs
	@echo " Showing logs for $(APP_NAME) in $(ENVIRONMENT)..."
	@kubectl logs -f deployment/$(APP_NAME) -n $(NAMESPACE) --tail=100

logs-previous: ##  Show previous pod logs
	@echo " Showing previous logs for $(APP_NAME)..."
	@kubectl logs deployment/$(APP_NAME) -n $(NAMESPACE) --previous --tail=100

# Interactive operations
shell: ##  Get shell in application pod
	@echo " Getting shell in $(APP_NAME) pod..."
	@kubectl exec -it deployment/$(APP_NAME) -n $(NAMESPACE) -- /bin/bash

debug: ##  Debug deployment issues
	@echo " Debugging deployment issues for $(APP_NAME)..."
	@echo ""
	@echo "=== Deployment Status ==="
	@kubectl describe deployment $(APP_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "=== Pod Status ==="
	@kubectl describe pods -l app=$(APP_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "=== Recent Events ==="
	@kubectl get events -n $(NAMESPACE) --sort-by=.metadata.creationTimestamp | tail -10

# Operational commands
restart: ##  Restart deployment
	@echo " Restarting $(APP_NAME) deployment..."
	@kubectl rollout restart deployment/$(APP_NAME) -n $(NAMESPACE)
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s
	@echo " Restart completed"

scale: ##  Scale deployment
	@echo "Current replicas: $$(kubectl get deployment $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.replicas}')"
	@read -p "New replica count: " NEW_REPLICAS; \
	echo " Scaling $(APP_NAME) to $$NEW_REPLICAS replicas..."; \
	kubectl scale deployment/$(APP_NAME) -n $(NAMESPACE) --replicas=$$NEW_REPLICAS; \
	kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s; \
	echo " Scaling completed"

# Port forwarding for local access
port-forward: ##  Port forward to application
	@echo " Port forwarding $(APP_NAME) to localhost:8080..."
	@kubectl port-forward service/$(APP_NAME) 8080:80 -n $(NAMESPACE)

# Resource usage
resource-usage: ##  Show resource usage
	@echo " Resource usage for $(APP_NAME):"
	@kubectl top pods -n $(NAMESPACE) -l app=$(APP_NAME) 2>/dev/null || echo " Metrics server not available"
```

### Environment Management

Create and manage environments easily:

```makefile
# =============================================================================
# Environment Management
# =============================================================================

create-environment: ##  Create new environment
	@echo " Creating environment: $(ENVIRONMENT)"
	@kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@kubectl label namespace $(NAMESPACE) environment=$(ENVIRONMENT) --overwrite
	@echo " Environment $(ENVIRONMENT) created"

destroy-environment: ##  Destroy environment
	@echo " Type the environment name '$(ENVIRONMENT)' to confirm destruction: " && read confirm && [ "$confirm" = "$(ENVIRONMENT)" ]
	@echo " Destroying environment: $(ENVIRONMENT)"
	@kubectl delete namespace $(NAMESPACE) --wait=true
	@echo " Environment $(ENVIRONMENT) destroyed"

list-environments: ##  List all environments for this app
	@echo " Environments for $(APP_NAME):"
	@kubectl get namespaces -l app=$(APP_NAME) -o custom-columns=NAME:.metadata.name,ENVIRONMENT:.metadata.labels.environment,AGE:.metadata.creationTimestamp 2>/dev/null || echo "No environments found"
```