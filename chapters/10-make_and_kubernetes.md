# Chapter 10 - Make and Kubernetes - Orchestrating Cloud-Native Deployments
_Simplifying Kubernetes complexity through Make-based deployment workflows that any team member can understand and execute._

Kubernetes has become the foundation of modern cloud-native infrastructure, but its power comes with overwhelming complexity. YAML manifests, kubectl commands, namespace management, resource dependencies, health checks, rollback procedures—the cognitive load can be crushing. Teams often resort to complex shell scripts, struggle with inconsistent deployments, or rely on heavyweight platforms that obscure the underlying operations.

Make provides an elegant solution by creating a discoverable orchestration layer over Kubernetes operations. Instead of memorizing intricate kubectl incantations or navigating maze-like deployment scripts, team members can simply run `make deploy`, `make status`, or `make rollback`. The Makefile becomes both the documentation and the implementation of your Kubernetes deployment strategy.

This chapter demonstrates how to create maintainable, reliable Kubernetes workflows using Make. We'll explore patterns for manifest generation, environment-specific deployments, Helm chart management, service mesh integration, and database migrations. By the end, your Kubernetes operations will be as discoverable and reliable as any other aspect of your DevOps infrastructure.

> **   Start Simple: Essential Kubernetes + Make Patterns**
> 
> Master these fundamental patterns before exploring advanced Kubernetes orchestration:
> 
> 1. **Basic deployment**: `deploy: build push apply` ensures images are ready before Kubernetes updates
> 2. **Environment isolation**: Use separate namespaces and target patterns for different environments
> 3. **Health verification**: Always check rollout status after deployments
> 4. **Configuration management**: Generate manifests from templates rather than maintaining static YAML
> 5. **Rollback capability**: Provide simple commands for when deployments go wrong
> 
> These patterns handle 80% of Kubernetes deployment scenarios. Advanced techniques become valuable when managing complex multi-service applications or sophisticated GitOps workflows.

## Kubernetes Manifest Generation and Validation

### The Challenge of Static YAML Manifests

Static Kubernetes YAML manifests become maintenance nightmares as applications grow. Different environments need different configurations, resource limits vary based on deployment targets, and keeping manifests synchronized with application changes requires constant manual updates.

Make enables **dynamic manifest generation** that adapts to different environments while maintaining consistency:

makefile

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
OVERLAYS_DIR = k8s/overlays

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
	@echo "  Manifests generated in $(MANIFESTS_DIR)/"

# Generate individual manifest types
generate-deployment: ## Generate deployment manifest
	@echo "Generating deployment manifest..."
	@envsubst < $(TEMPLATES_DIR)/deployment.yaml.template > $(MANIFESTS_DIR)/deployment.yaml
	@echo "  Deployment: $(REPLICAS) replicas, $(IMAGE_TAG)"

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
validate-manifests: generate-manifests ##   Validate Kubernetes manifests
	@echo "  Validating Kubernetes manifests..."
	@for manifest in $(MANIFESTS_DIR)/*.yaml; do \
		echo "Validating $$manifest..."; \
		kubectl apply --dry-run=client --validate=true -f $$manifest >/dev/null || exit 1; \
	done
	@echo "  All manifests are valid"

# Advanced validation with kubeval
validate-with-kubeval: generate-manifests ##   Validate with kubeval
	@echo "  Validating with kubeval..."
	@for manifest in $(MANIFESTS_DIR)/*.yaml; do \
		kubeval $$manifest || exit 1; \
	done

# Clean generated manifests
clean-manifests: ##   Clean generated manifests
	@rm -rf $(MANIFESTS_DIR)
	@echo "  Generated manifests cleaned"
```

### Template-Based Configuration Management

Create flexible templates that adapt to different environments and configurations:

**k8s/templates/deployment.yaml.template:**

yaml

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

## Environment-Specific Deployment Strategies

### Multi-Environment Orchestration

Create sophisticated deployment strategies that adapt to different environments:

makefile

```makefile
# =============================================================================
# Environment-Specific Deployment Strategies
# =============================================================================

# Environment validation
validate-environment: ##   Validate environment configuration
	@echo "  Validating $(ENVIRONMENT) environment..."
	@case "$(ENVIRONMENT)" in \
		development|staging|production) ;; \
		*) echo "  Invalid environment: $(ENVIRONMENT)" && exit 1 ;; \
	esac
	@$(MAKE) validate-cluster-access
	@$(MAKE) validate-namespace-exists
	@$(MAKE) validate-secrets-available

validate-cluster-access: ##   Validate cluster access
	@kubectl cluster-info >/dev/null || (echo "  Cannot access Kubernetes cluster" && exit 1)
	@echo "  Cluster access verified"

validate-namespace-exists: ##   Ensure namespace exists
	@kubectl get namespace $(NAMESPACE) >/dev/null 2>&1 || \
		(echo " Creating namespace $(NAMESPACE)" && kubectl create namespace $(NAMESPACE))

validate-secrets-available: ##   Validate required secrets exist
	@if [ "$(ENVIRONMENT)" != "development" ]; then \
		kubectl get secret $(APP_NAME)-secrets -n $(NAMESPACE) >/dev/null 2>&1 || \
		(echo "  Required secrets not found in $(NAMESPACE)" && exit 1); \
	fi

# Environment-specific deployment strategies
deploy: validate-environment deploy-$(ENVIRONMENT) ##   Deploy to configured environment

deploy-development: build push generate-manifests ##   Development deployment (fast, minimal checks)
	@echo "  Development deployment..."
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@$(MAKE) wait-for-rollout-fast
	@echo "  Development deployment completed"

deploy-staging: build push generate-manifests validate-manifests ##   Staging deployment (full validation)
	@echo "  Staging deployment..."
	@$(MAKE) pre-deployment-checks
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@$(MAKE) wait-for-rollout
	@$(MAKE) smoke-test
	@echo "  Staging deployment completed"

deploy-production: build push generate-manifests validate-manifests ##   Production deployment (maximum safety)
	@echo " Production deployment..."
	@$(MAKE) pre-production-checks
	@$(MAKE) backup-current-state
	@echo "   Deploy to PRODUCTION? [y/N]" && read ans && [ $$ans = y ]
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@$(MAKE) wait-for-rollout-production
	@$(MAKE) verify-production-deployment
	@$(MAKE) notify-deployment-success
	@echo "  Production deployment completed"

# Pre-deployment checks
pre-deployment-checks: ##   Run pre-deployment checks
	@echo "  Running pre-deployment checks..."
	@$(MAKE) validate-manifests
	@$(MAKE) check-resource-requirements
	@$(MAKE) verify-image-exists

pre-production-checks: pre-deployment-checks ##   Additional production checks
	@echo "  Running production-specific checks..."
	@$(MAKE) security-scan-image
	@$(MAKE) validate-backup-systems
	@$(MAKE) check-monitoring-alerts

# Resource requirement validation
check-resource-requirements: ##   Validate cluster has sufficient resources
	@echo "  Checking resource requirements..."
	@REQUIRED_CPU=$$(echo $(REPLICAS) \* $(CPU_REQUEST) | bc -l | cut -d. -f1)m; \
	REQUIRED_MEMORY=$$(echo $(REPLICAS) \* $(MEMORY_REQUEST) | sed 's/Mi//' | bc)Mi; \
	echo "Required resources: $${REQUIRED_CPU} CPU, $${REQUIRED_MEMORY} memory"; \
	kubectl top nodes >/dev/null 2>&1 || echo "   Cannot verify resource usage (metrics-server not available)"

verify-image-exists: ##   Verify Docker image exists in registry
	@echo "  Verifying image exists: $(IMAGE_TAG)"
	@docker manifest inspect $(IMAGE_TAG) >/dev/null 2>&1 || \
		(echo "  Image not found: $(IMAGE_TAG)" && exit 1)
	@echo "  Image verified"
```

### Rollout Management and Health Checks

Implement comprehensive rollout management:

makefile

```makefile
# =============================================================================
# Rollout Management and Health Checks
# =============================================================================

# Rollout monitoring
wait-for-rollout: ##   Wait for rollout to complete
	@echo "  Waiting for rollout to complete..."
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s
	@$(MAKE) verify-deployment-health
	@echo "  Rollout completed successfully"

wait-for-rollout-fast: ##   Quick rollout wait (development)
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=60s

wait-for-rollout-production: ##   Production rollout with extended monitoring
	@echo "  Production rollout monitoring..."
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=600s
	@$(MAKE) verify-deployment-health
	@$(MAKE) extended-health-monitoring
	@echo "  Production rollout completed"

# Health verification
verify-deployment-health: ##   Verify deployment health
	@echo "  Verifying deployment health..."
	@READY_REPLICAS=$$(kubectl get deployment $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.status.readyReplicas}'); \
	DESIRED_REPLICAS=$$(kubectl get deployment $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.replicas}'); \
	if [ "$$READY_REPLICAS" != "$$DESIRED_REPLICAS" ]; then \
		echo "  Health check failed: $$READY_REPLICAS/$$DESIRED_REPLICAS replicas ready"; \
		exit 1; \
	fi; \
	echo "  All $$READY_REPLICAS replicas are healthy"

extended-health-monitoring: ##   Extended health monitoring
	@echo "  Extended health monitoring..."
	@for i in $$(seq 1 12); do \
		echo "Health check $$i/12..."; \
		$(MAKE) app-health-check || (echo "  Application health check failed" && exit 1); \
		sleep 10; \
	done
	@echo "  Extended health monitoring passed"

app-health-check: ##   Application-specific health check
	@APP_URL=$$(kubectl get ingress $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "localhost"); \
	APP_PORT=$$(kubectl get service $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "8080"); \
	if kubectl get ingress $(APP_NAME) -n $(NAMESPACE) >/dev/null 2>&1; then \
		curl -f -m 10 http://$$APP_URL/health >/dev/null; \
	else \
		kubectl port-forward service/$(APP_NAME) $$APP_PORT:8080 -n $(NAMESPACE) & \
		PF_PID=$$!; \
		sleep 2; \
		curl -f -m 10 http://localhost:$$APP_PORT/health >/dev/null; \
		kill $$PF_PID 2>/dev/null || true; \
	fi

# Rollback operations
rollback: ##   Rollback to previous version
	@echo "  Rolling back to previous version..."
	@kubectl rollout undo deployment/$(APP_NAME) -n $(NAMESPACE)
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s
	@$(MAKE) verify-deployment-health
	@echo "  Rollback completed"

rollback-to-revision: ##   Rollback to specific revision
	@read -p "Revision number: " REVISION; \
	echo "  Rolling back to revision $$REVISION..."; \
	kubectl rollout undo deployment/$(APP_NAME) -n $(NAMESPACE) --to-revision=$$REVISION; \
	kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s; \
	$(MAKE) verify-deployment-health

# Deployment history
rollout-history: ##   Show rollout history
	@kubectl rollout history deployment/$(APP_NAME) -n $(NAMESPACE)
```

## Helm Chart Management and Customization

### Basic Helm Integration

Integrate Helm charts with Make for better orchestration:

makefile

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
	@echo "  Helm chart is valid"

helm-template: ##  Generate templates from Helm chart
	@echo " Generating templates from Helm chart..."
	@mkdir -p $(MANIFESTS_DIR)
	@helm template $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--output-dir $(MANIFESTS_DIR)
	@echo "  Templates generated in $(MANIFESTS_DIR)/"

helm-install: build push ##   Install with Helm
	@echo "  Installing with Helm..."
	@$(MAKE) validate-environment
	@helm install $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--wait --timeout=300s
	@$(MAKE) verify-helm-deployment
	@echo "  Helm installation completed"

helm-upgrade: build push ##   Upgrade with Helm
	@echo "  Upgrading with Helm..."
	@helm upgrade $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--wait --timeout=300s
	@$(MAKE) verify-helm-deployment
	@echo "  Helm upgrade completed"

verify-helm-deployment: ##   Verify Helm deployment
	@echo "  Verifying Helm deployment..."
	@helm status $(HELM_RELEASE_NAME) -n $(NAMESPACE) | grep -q "STATUS: deployed" || \
		(echo "  Helm deployment not in deployed state" && exit 1)
	@$(MAKE) verify-deployment-health
	@echo "  Helm deployment verification completed"
```

## Service Mesh Configuration and Monitoring Setup

### Istio Service Mesh Integration

Integrate service mesh configuration with Make workflows:

makefile

```makefile
# =============================================================================
# Istio Service Mesh Integration
# =============================================================================

# Istio configuration
ISTIO_NAMESPACE = istio-system
ISTIO_GATEWAY = $(APP_NAME)-gateway
ISTIO_VS = $(APP_NAME)-virtualservice

.PHONY: istio-install istio-enable istio-configure istio-status

# Istio installation and setup
istio-install: ##    Install Istio
	@echo "   Installing Istio..."
	@istioctl install --set values.defaultRevision=default -y
	@kubectl label namespace $(NAMESPACE) istio-injection=enabled --overwrite
	@echo "  Istio installed and namespace labeled"

istio-enable: ##  Enable Istio for application
	@echo " Enabling Istio for $(APP_NAME)..."
	@$(MAKE) generate-istio-manifests
	@kubectl apply -f k8s/istio/ -n $(NAMESPACE)
	@echo "  Istio enabled for $(APP_NAME)"

# Generate Istio configuration
generate-istio-manifests: ##  Generate Istio manifests
	@echo " Generating Istio manifests..."
	@mkdir -p k8s/istio
	@$(MAKE) generate-gateway
	@$(MAKE) generate-virtual-service
	@$(MAKE) generate-destination-rule

generate-gateway: ## Generate Istio Gateway
	@cat > k8s/istio/gateway.yaml << EOF
apiVersion: networking.istio.io/v1beta1
kind: Gateway
metadata:
  name: $(ISTIO_GATEWAY)
  namespace: $(NAMESPACE)
spec:
  selector:
    istio: ingressgateway
  servers:
  - port:
      number: 80
      name: http
      protocol: HTTP
    hosts:
    - "$(APP_NAME)-$(ENVIRONMENT).example.com"
EOF

generate-virtual-service: ## Generate Istio VirtualService
	@cat > k8s/istio/virtualservice.yaml << EOF
apiVersion: networking.istio.io/v1beta1
kind: VirtualService
metadata:
  name: $(ISTIO_VS)
  namespace: $(NAMESPACE)
spec:
  hosts:
  - "$(APP_NAME)-$(ENVIRONMENT).example.com"
  gateways:
  - $(ISTIO_GATEWAY)
  http:
  - match:
    - uri:
        prefix: /
    route:
    - destination:
        host: $(APP_NAME)
        port:
          number: 8080
    timeout: 30s
    retries:
      attempts: 3
      perTryTimeout: 10s
EOF
```

### Prometheus and Grafana Integration

Set up comprehensive monitoring with Make workflows:

makefile

```makefile
# =============================================================================
# Monitoring and Observability Setup
# =============================================================================

# Monitoring configuration
MONITORING_NAMESPACE = monitoring
PROMETHEUS_RELEASE = prometheus-stack
GRAFANA_ADMIN_PASSWORD ?= admin123

.PHONY: monitoring-install monitoring-configure monitoring-status

# Install monitoring stack
monitoring-install: ##   Install monitoring stack
	@echo "  Installing monitoring stack..."
	@kubectl create namespace $(MONITORING_NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
	@helm repo update
	@helm install $(PROMETHEUS_RELEASE) prometheus-community/kube-prometheus-stack \
		--namespace $(MONITORING_NAMESPACE) \
		--set grafana.adminPassword=$(GRAFANA_ADMIN_PASSWORD) \
		--wait --timeout=600s
	@echo "  Monitoring stack installed"

# Configure monitoring for application
monitoring-configure: ##   Configure monitoring for application
	@echo "  Configuring monitoring for $(APP_NAME)..."
	@$(MAKE) create-service-monitor
	@$(MAKE) create-alerts
	@echo "  Monitoring configured"

create-service-monitor: ## Create Prometheus ServiceMonitor
	@cat > k8s/monitoring/servicemonitor.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: $(APP_NAME)-metrics
  namespace: $(NAMESPACE)
  labels:
    app: $(APP_NAME)
spec:
  selector:
    matchLabels:
      app: $(APP_NAME)
  endpoints:
  - port: metrics
    interval: 30s
    path: /metrics
EOF
	@kubectl apply -f k8s/monitoring/servicemonitor.yaml

create-alerts: ## Create Prometheus alerts
	@cat > k8s/monitoring/alerts.yaml << EOF
apiVersion: monitoring.coreos.com/v1
kind: PrometheusRule
metadata:
  name: $(APP_NAME)-alerts
  namespace: $(NAMESPACE)
  labels:
    app: $(APP_NAME)
spec:
  groups:
  - name: $(APP_NAME).rules
    rules:
    - alert: $(APP_NAME)HighErrorRate
      expr: rate(http_requests_total{job="$(APP_NAME)",status=~"5.."}[5m]) > 0.1
      for: 5m
      labels:
        severity: warning
      annotations:
        summary: "High error rate detected"
        description: "$(APP_NAME) has error rate above 10% for 5 minutes"
    
    - alert: $(APP_NAME)Down
      expr: up{job="$(APP_NAME)"} == 0
      for: 1m
      labels:
        severity: critical
      annotations:
        summary: "$(APP_NAME) is down"
        description: "$(APP_NAME) has been down for more than 1 minute"
EOF
	@kubectl apply -f k8s/monitoring/alerts.yaml

monitoring-access: ##  Access monitoring UIs
	@echo " Setting up access to monitoring UIs..."
	@kubectl port-forward -n $(MONITORING_NAMESPACE) svc/$(PROMETHEUS_RELEASE)-grafana 3000:80 > /dev/null 2>&1 &
	@kubectl port-forward -n $(MONITORING_NAMESPACE) svc/$(PROMETHEUS_RELEASE)-kube-prom-prometheus 9090:9090 > /dev/null 2>&1 &
	@sleep 2
	@echo "  Monitoring UIs available:"
	@echo "   Grafana: http://localhost:3000 (admin/$(GRAFANA_ADMIN_PASSWORD))"
	@echo "   Prometheus: http://localhost:9090"
```

## Database Migrations and State Management

### Database Migration Workflows

Handle database migrations safely in Kubernetes:

makefile

```makefile
# =============================================================================
# Database Migration Management
# =============================================================================

# Database configuration
DB_NAMESPACE = $(NAMESPACE)
DB_SECRET = $(APP_NAME)-db-secret
DB_MIGRATION_JOB = $(APP_NAME)-migration

.PHONY: db-migrate db-rollback db-backup db-status

# Database migration
db-migrate: ##   Run database migrations
	@echo "  Running database migrations..."
	@$(MAKE) validate-db-connection
	@$(MAKE) create-migration-job
	@$(MAKE) wait-for-migration
	@$(MAKE) cleanup-migration-job
	@echo "  Database migrations completed"

create-migration-job: ## Create migration job
	@cat > k8s/jobs/migration-job.yaml << EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: $(DB_MIGRATION_JOB)-$(shell date +%Y%m%d-%H%M%S)
  namespace: $(DB_NAMESPACE)
spec:
  template:
    spec:
      restartPolicy: Never
      containers:
      - name: migrate
        image: $(IMAGE_TAG)
        command: ["python", "manage.py", "migrate"]
        envFrom:
        - secretRef:
            name: $(DB_SECRET)
        env:
        - name: ENVIRONMENT
          value: $(ENVIRONMENT)
      backoffLimit: 3
EOF
	@kubectl apply -f k8s/jobs/migration-job.yaml

wait-for-migration: ## Wait for migration to complete
	@echo "  Waiting for migration to complete..."
	@JOB_NAME=$$(kubectl get jobs -n $(DB_NAMESPACE) --sort-by=.metadata.creationTimestamp | grep $(DB_MIGRATION_JOB) | tail -1 | awk '{print $$1}'); \
	kubectl wait --for=condition=complete --timeout=300s job/$$JOB_NAME -n $(DB_NAMESPACE) || \
	(echo "  Migration failed" && kubectl logs job/$$JOB_NAME -n $(DB_NAMESPACE) && exit 1)

cleanup-migration-job: ## Clean up completed migration jobs
	@echo "  Cleaning up migration jobs..."
	@kubectl delete jobs -n $(DB_NAMESPACE) -l app=$(DB_MIGRATION_JOB) --field-selector=status.successful=1 || true

validate-db-connection: ##   Validate database connection
	@echo "  Validating database connection..."
	@kubectl run db-test-$(shell date +%s) --rm -i --restart=Never \
		--image=postgres:13 --env-from=secret/$(DB_SECRET) -- \
		psql -h $$DB_HOST -U $$DB_USER -d $$DB_NAME -c "SELECT 1;" >/dev/null
	@echo "  Database connection validated"
```

## Complete Production Workflow Integration

### Comprehensive Deployment Pipeline

Put it all together in a production-ready Kubernetes deployment workflow:

makefile

````makefile
# =============================================================================
# Production-Ready Kubernetes Deployment Workflow
# =============================================================================

# Configuration
APP_NAME ?= myapp
VERSION ?= $(shell git describe --tags --always --dirty)
ENVIRONMENT ?= development
NAMESPACE = $(APP_NAME)-$(ENVIRONMENT)
REGISTRY ?= registry.company.com
IMAGE_TAG = $(REGISTRY)/$(APP_NAME):$(VERSION)

# Deployment strategy
DEPLOYMENT_STRATEGY ?= rolling
USE_HELM ?= false
USE_ISTIO ?= false
ENABLE_MONITORING ?= true

.DEFAULT_GOAL := help

# =============================================================================
# Main Workflow Targets
# =============================================================================

help: ##   Show available commands
	@echo "$(APP_NAME) Kubernetes Workflow"
	@echo "==============================="
	@echo ""
	@echo "  Quick Start:"
	@echo "  make deploy         # Deploy to development"
	@echo "  make status         # Check deployment status"
	@echo "  make logs           # Show application logs"
	@echo "  make rollback       # Rollback to previous version"
	@echo ""
	@echo "  All Commands:"
	@awk 'BEGIN {FS = ":.*##"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-20s\033[0m %s\n", $1, $2 }' $(MAKEFILE_LIST)

# Comprehensive deployment workflow
deploy: ##   Deploy application to Kubernetes
	@echo "  Deploying $(APP_NAME) v$(VERSION) to $(ENVIRONMENT)"
	@$(MAKE) pre-deploy-validation
	@$(MAKE) prepare-deployment
	@$(MAKE) execute-deployment
	@$(MAKE) post-deploy-verification
	@$(MAKE) post-deploy-setup
	@echo "  Deployment completed successfully"

# Pre-deployment validation
pre-deploy-validation: ##   Comprehensive pre-deployment validation
	@echo "  Running pre-deployment validation..."
	@$(MAKE) validate-environment
	@$(MAKE) verify-image-exists
	@$(MAKE) validate-cluster-resources
	@$(MAKE) security-check
	@echo "  Pre-deployment validation passed"

# Prepare deployment artifacts
prepare-deployment: ##  Prepare deployment artifacts
	@echo " Preparing deployment artifacts..."
ifeq ($(USE_HELM),true)
	@$(MAKE) helm-template
else
	@$(MAKE) generate-manifests
	@$(MAKE) validate-manifests
endif
ifeq ($(USE_ISTIO),true)
	@$(MAKE) generate-istio-manifests
endif
ifeq ($(ENABLE_MONITORING),true)
	@$(MAKE) prepare-monitoring-config
endif
	@echo "  Deployment artifacts ready"

# Execute deployment based on strategy
execute-deployment: ##   Execute deployment
	@echo "  Executing $(DEPLOYMENT_STRATEGY) deployment..."
	@case "$(DEPLOYMENT_STRATEGY)" in \
		rolling) $(MAKE) deploy-rolling ;; \
		blue-green) $(MAKE) deploy-blue-green ;; \
		canary) $(MAKE) deploy-canary ;; \
		*) echo "  Unknown deployment strategy: $(DEPLOYMENT_STRATEGY)" && exit 1 ;; \
	esac

# Post-deployment verification
post-deploy-verification: ##   Post-deployment verification
	@echo "  Running post-deployment verification..."
	@$(MAKE) wait-for-rollout
	@$(MAKE) health-check-comprehensive
	@$(MAKE) smoke-test
	@echo "  Post-deployment verification passed"

# Post-deployment setup
post-deploy-setup: ##   Post-deployment setup
	@echo "  Running post-deployment setup..."
ifeq ($(USE_ISTIO),true)
	@$(MAKE) istio-enable
endif
ifeq ($(ENABLE_MONITORING),true)
	@$(MAKE) monitoring-configure
endif
	@$(MAKE) notify-deployment-success
	@echo "  Post-deployment setup completed"

# =============================================================================
# Environment Management
# =============================================================================

create-environment: ##    Create new environment
	@echo "   Creating environment: $(ENVIRONMENT)"
	@kubectl create namespace $(NAMESPACE) --dry-run=client -o yaml | kubectl apply -f -
	@kubectl label namespace $(NAMESPACE) environment=$(ENVIRONMENT) --overwrite
	@$(MAKE) setup-rbac
	@$(MAKE) setup-secrets
	@$(MAKE) setup-monitoring-namespace
	@echo "  Environment $(ENVIRONMENT) created"

destroy-environment: ##  Destroy environment
	@echo "   This will destroy the $(ENVIRONMENT) environment. Continue? [y/N]" && read ans && [ $ans = y ]
	@echo " Destroying environment: $(ENVIRONMENT)"
	@kubectl delete namespace $(NAMESPACE) --wait=true
	@echo "  Environment $(ENVIRONMENT) destroyed"

setup-rbac: ##   Set up RBAC for environment
	@echo "  Setting up RBAC..."
	@cat > k8s/rbac/serviceaccount.yaml << EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: $(APP_NAME)
  namespace: $(NAMESPACE)
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: $(APP_NAME)-role
  namespace: $(NAMESPACE)
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: $(APP_NAME)-binding
  namespace: $(NAMESPACE)
subjects:
- kind: ServiceAccount
  name: $(APP_NAME)
  namespace: $(NAMESPACE)
roleRef:
  kind: Role
  name: $(APP_NAME)-role
  apiGroup: rbac.authorization.k8s.io
EOF
	@kubectl apply -f k8s/rbac/serviceaccount.yaml

# =============================================================================
# Operations and Maintenance
# =============================================================================

status: ##   Show comprehensive deployment status
	@echo "  Deployment Status for $(APP_NAME) in $(ENVIRONMENT)"
	@echo "================================================="
	@echo ""
	@echo "Namespace:"
	@kubectl get namespace $(NAMESPACE) 2>/dev/null || echo "  Namespace not found"
	@echo ""
	@echo "Deployments:"
	@kubectl get deployments -n $(NAMESPACE) -o wide 2>/dev/null || echo "  No deployments found"
	@echo ""
	@echo "Pods:"
	@kubectl get pods -n $(NAMESPACE) -o wide 2>/dev/null || echo "  No pods found"
	@echo ""
	@echo "Services:"
	@kubectl get services -n $(NAMESPACE) 2>/dev/null || echo "  No services found"
	@echo ""
	@echo "Ingress:"
	@kubectl get ingress -n $(NAMESPACE) 2>/dev/null || echo "  No ingress found"

logs: ##   Show application logs
	@kubectl logs -f deployment/$(APP_NAME) -n $(NAMESPACE) --tail=100

shell: ##   Get shell in application pod
	@kubectl exec -it deployment/$(APP_NAME) -n $(NAMESPACE) -- /bin/bash

debug: ##   Debug deployment issues
	@echo "  Debugging deployment issues..."
	@echo ""
	@echo "=== Deployment Status ==="
	@kubectl describe deployment $(APP_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "=== Pod Status ==="
	@kubectl describe pods -l app=$(APP_NAME) -n $(NAMESPACE)
	@echo ""
	@echo "=== Recent Events ==="
	@kubectl get events -n $(NAMESPACE) --sort-by=.metadata.creationTimestamp | tail -10

# =============================================================================
# Cleanup and Maintenance
# =============================================================================

clean: ##   Clean up development resources
	@echo "  Cleaning up resources..."
	@kubectl delete jobs -n $(NAMESPACE) --field-selector=status.successful=1 || true
	@$(MAKE) clean-manifests
	@echo "  Cleanup completed"

uninstall: ##   Uninstall application
	@echo "   This will uninstall $(APP_NAME) from $(ENVIRONMENT). Continue? [y/N]" && read ans && [ $ans = y ]
	@echo "  Uninstalling application..."
ifeq ($(USE_HELM),true)
	@$(MAKE) helm-uninstall
else
	@kubectl delete -f $(MANIFESTS_DIR)/ -n $(NAMESPACE) || true
endif
	@echo "  Application uninstalled"

# Utility targets (internal)
security-check:
	@echo "  Running security checks..."
	@command -v trivy >/dev/null && trivy image $(IMAGE_TAG) || echo "   Trivy not available, skipping image scan"

validate-cluster-resources:
	@kubectl top nodes >/dev/null 2>&1 || echo "   Cannot verify cluster resources (metrics-server not available)"

prepare-monitoring-config:
	@mkdir -p k8s/monitoring
	@$(MAKE) create-service-monitor

health-check-comprehensive:
	@$(MAKE) verify-deployment-health
	@$(# Chapter 10: Make and Kubernetes - Orchestrating Cloud-Native Deployments

*Simplifying Kubernetes complexity through Make-based deployment workflows that any team member can understand and execute.*

Kubernetes has become the foundation of modern cloud-native infrastructure, but its power comes with overwhelming complexity. YAML manifests, kubectl commands, namespace management, resource dependencies, health checks, rollback procedures—the cognitive load can be crushing. Teams often resort to complex shell scripts, struggle with inconsistent deployments, or rely on heavyweight platforms that obscure the underlying operations.

Make provides an elegant solution by creating a discoverable orchestration layer over Kubernetes operations. Instead of memorizing intricate kubectl incantations or navigating maze-like deployment scripts, team members can simply run `make deploy`, `make status`, or `make rollback`. The Makefile becomes both the documentation and the implementation of your Kubernetes deployment strategy.

This chapter demonstrates how to create maintainable, reliable Kubernetes workflows using Make. We'll explore patterns for manifest generation, environment-specific deployments, Helm chart management, service mesh integration, and database migrations. By the end, your Kubernetes operations will be as discoverable and reliable as any other aspect of your DevOps infrastructure.

> **   Start Simple: Essential Kubernetes + Make Patterns**
> 
> Master these fundamental patterns before exploring advanced Kubernetes orchestration:
> 
> 1. **Basic deployment**: `deploy: build push apply` ensures images are ready before Kubernetes updates
> 2. **Environment isolation**: Use separate namespaces and target patterns for different environments
> 3. **Health verification**: Always check rollout status after deployments
> 4. **Configuration management**: Generate manifests from templates rather than maintaining static YAML
> 5. **Rollback capability**: Provide simple commands for when deployments go wrong
> 
> These patterns handle 80% of Kubernetes deployment scenarios. Advanced techniques become valuable when managing complex multi-service applications or sophisticated GitOps workflows.

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
OVERLAYS_DIR = k8s/overlays

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
	@echo "  Manifests generated in $(MANIFESTS_DIR)/"

# Generate individual manifest types
generate-deployment: ## Generate deployment manifest
	@echo "Generating deployment manifest..."
	@envsubst < $(TEMPLATES_DIR)/deployment.yaml.template > $(MANIFESTS_DIR)/deployment.yaml
	@echo "  Deployment: $(REPLICAS) replicas, $(IMAGE_TAG)"

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
validate-manifests: generate-manifests ##   Validate Kubernetes manifests
	@echo "  Validating Kubernetes manifests..."
	@for manifest in $(MANIFESTS_DIR)/*.yaml; do \
		echo "Validating $$manifest..."; \
		kubectl apply --dry-run=client --validate=true -f $$manifest >/dev/null || exit 1; \
	done
	@echo "  All manifests are valid"

# Advanced validation with kubeval
validate-with-kubeval: generate-manifests ##   Validate with kubeval
	@echo "  Validating with kubeval..."
	@for manifest in $(MANIFESTS_DIR)/*.yaml; do \
		kubeval $$manifest || exit 1; \
	done

# Clean generated manifests
clean-manifests: ##   Clean generated manifests
	@rm -rf $(MANIFESTS_DIR)
	@echo "  Generated manifests cleaned"
````

### Template-Based Configuration Management

Create flexible templates that adapt to different environments and configurations:

**k8s/templates/deployment.yaml.template:**

yaml

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

**Advanced templating with environment-specific overlays:**

makefile

```makefile
# =============================================================================
# Advanced Templating with Kustomize Integration
# =============================================================================

# Generate Kustomize overlays
generate-kustomize-overlay: ##  Generate Kustomize overlay
	@echo " Generating Kustomize overlay for $(ENVIRONMENT)..."
	@mkdir -p $(OVERLAYS_DIR)/$(ENVIRONMENT)
	@cat > $(OVERLAYS_DIR)/$(ENVIRONMENT)/kustomization.yaml << EOF
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

namespace: $(NAMESPACE)

resources:
- ../../base

images:
- name: $(APP_NAME)
  newTag: $(VERSION)

replicas:
- name: $(APP_NAME)
  count: $(REPLICAS)

patchesStrategicMerge:
- resource-patch.yaml
EOF
	@$(MAKE) generate-resource-patch

generate-resource-patch: ## Generate environment-specific resource patch
	@cat > $(OVERLAYS_DIR)/$(ENVIRONMENT)/resource-patch.yaml << EOF
apiVersion: apps/v1
kind: Deployment
metadata:
  name: $(APP_NAME)
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          requests:
            cpu: $(CPU_REQUEST)
            memory: $(MEMORY_REQUEST)
          limits:
            cpu: $(CPU_LIMIT)
            memory: $(MEMORY_LIMIT)
EOF

# Deploy with Kustomize
deploy-kustomize: generate-kustomize-overlay ##   Deploy using Kustomize
	@echo "  Deploying with Kustomize..."
	@kubectl apply -k $(OVERLAYS_DIR)/$(ENVIRONMENT)
	@$(MAKE) wait-for-rollout
```

## Environment-Specific Deployment Strategies

### Multi-Environment Orchestration

Create sophisticated deployment strategies that adapt to different environments:

makefile

```makefile
# =============================================================================
# Environment-Specific Deployment Strategies
# =============================================================================

# Environment validation
validate-environment: ##   Validate environment configuration
	@echo "  Validating $(ENVIRONMENT) environment..."
	@case "$(ENVIRONMENT)" in \
		development|staging|production) ;; \
		*) echo "  Invalid environment: $(ENVIRONMENT)" && exit 1 ;; \
	esac
	@$(MAKE) validate-cluster-access
	@$(MAKE) validate-namespace-exists
	@$(MAKE) validate-secrets-available

validate-cluster-access: ##   Validate cluster access
	@kubectl cluster-info >/dev/null || (echo "  Cannot access Kubernetes cluster" && exit 1)
	@echo "  Cluster access verified"

validate-namespace-exists: ##   Ensure namespace exists
	@kubectl get namespace $(NAMESPACE) >/dev/null 2>&1 || \
		(echo " Creating namespace $(NAMESPACE)" && kubectl create namespace $(NAMESPACE))

validate-secrets-available: ##   Validate required secrets exist
	@if [ "$(ENVIRONMENT)" != "development" ]; then \
		kubectl get secret $(APP_NAME)-secrets -n $(NAMESPACE) >/dev/null 2>&1 || \
		(echo "  Required secrets not found in $(NAMESPACE)" && exit 1); \
	fi

# Environment-specific deployment strategies
deploy: validate-environment deploy-$(ENVIRONMENT) ##   Deploy to configured environment

deploy-development: build push generate-manifests ##   Development deployment (fast, minimal checks)
	@echo "  Development deployment..."
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@$(MAKE) wait-for-rollout-fast
	@echo "  Development deployment completed"

deploy-staging: build push generate-manifests validate-manifests ##   Staging deployment (full validation)
	@echo "  Staging deployment..."
	@$(MAKE) pre-deployment-checks
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@$(MAKE) wait-for-rollout
	@$(MAKE) smoke-test
	@echo "  Staging deployment completed"

deploy-production: build push generate-manifests validate-manifests ##   Production deployment (maximum safety)
	@echo " Production deployment..."
	@$(MAKE) pre-production-checks
	@$(MAKE) backup-current-state
	@echo "   Deploy to PRODUCTION? [y/N]" && read ans && [ $$ans = y ]
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@$(MAKE) wait-for-rollout-production
	@$(MAKE) verify-production-deployment
	@$(MAKE) notify-deployment-success
	@echo "  Production deployment completed"

# Pre-deployment checks
pre-deployment-checks: ##   Run pre-deployment checks
	@echo "  Running pre-deployment checks..."
	@$(MAKE) validate-manifests
	@$(MAKE) check-resource-requirements
	@$(MAKE) verify-image-exists

pre-production-checks: pre-deployment-checks ##   Additional production checks
	@echo "  Running production-specific checks..."
	@$(MAKE) security-scan-image
	@$(MAKE) validate-backup-systems
	@$(MAKE) check-monitoring-alerts

# Resource requirement validation
check-resource-requirements: ##   Validate cluster has sufficient resources
	@echo "  Checking resource requirements..."
	@REQUIRED_CPU=$$(echo $(REPLICAS) \* $(CPU_REQUEST) | bc -l | cut -d. -f1)m; \
	REQUIRED_MEMORY=$$(echo $(REPLICAS) \* $(MEMORY_REQUEST) | sed 's/Mi//' | bc)Mi; \
	echo "Required resources: $${REQUIRED_CPU} CPU, $${REQUIRED_MEMORY} memory"; \
	kubectl top nodes >/dev/null 2>&1 || echo "   Cannot verify resource usage (metrics-server not available)"

verify-image-exists: ##   Verify Docker image exists in registry
	@echo "  Verifying image exists: $(IMAGE_TAG)"
	@docker manifest inspect $(IMAGE_TAG) >/dev/null 2>&1 || \
		(echo "  Image not found: $(IMAGE_TAG)" && exit 1)
	@echo "  Image verified"
```

### Deployment Patterns and Strategies

Implement various deployment patterns based on environment needs:

makefile

```makefile
# =============================================================================
# Advanced Deployment Patterns
# =============================================================================

# Rolling deployment (default)
deploy-rolling: generate-manifests ##   Rolling deployment
	@echo "  Rolling deployment..."
	@kubectl apply -f $(MANIFESTS_DIR)/ -n $(NAMESPACE)
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s

# Blue-green deployment
deploy-blue-green: ##    Blue-green deployment
	@echo "   Blue-green deployment..."
	@CURRENT_COLOR=$$(kubectl get service $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.selector.color}' 2>/dev/null || echo "blue"); \
	NEW_COLOR=$$([ "$$CURRENT_COLOR" = "blue" ] && echo "green" || echo "blue"); \
	echo "Current: $$CURRENT_COLOR, Deploying: $$NEW_COLOR"; \
	$(MAKE) deploy-color COLOR=$$NEW_COLOR; \
	$(MAKE) test-color COLOR=$$NEW_COLOR; \
	$(MAKE) switch-traffic COLOR=$$NEW_COLOR; \
	$(MAKE) cleanup-old-color COLOR=$$CURRENT_COLOR

deploy-color: generate-manifests ## Deploy specific color version
	@echo "Deploying $(COLOR) version..."
	@sed 's/name: $(APP_NAME)/name: $(APP_NAME)-$(COLOR)/g; s/app: $(APP_NAME)/app: $(APP_NAME)\n    color: $(COLOR)/g' \
		$(MANIFESTS_DIR)/deployment.yaml | kubectl apply -n $(NAMESPACE) -f -

switch-traffic: ## Switch traffic to new color
	@echo "Switching traffic to $(COLOR)..."
	@kubectl patch service $(APP_NAME) -n $(NAMESPACE) -p '{"spec":{"selector":{"color":"$(COLOR)"}}}'

# Canary deployment
deploy-canary: ##   Canary deployment
	@echo "  Canary deployment..."
	@$(MAKE) deploy-canary-version
	@$(MAKE) monitor-canary
	@$(MAKE) promote-canary || $(MAKE) rollback-canary

deploy-canary-version: generate-manifests ## Deploy canary version
	@echo "Deploying canary version..."
	@CANARY_REPLICAS=1; \
	sed 's/name: $(APP_NAME)/name: $(APP_NAME)-canary/g; s/replicas: $(REPLICAS)/replicas: '$$CANARY_REPLICAS'/g' \
		$(MANIFESTS_DIR)/deployment.yaml | kubectl apply -n $(NAMESPACE) -f -
	@$(MAKE) update-service-for-canary

monitor-canary: ## Monitor canary deployment
	@echo "Monitoring canary deployment for 5 minutes..."
	@for i in $$(seq 1 30); do \
		echo "Canary check $$i/30..."; \
		$(MAKE) health-check-canary || (echo "  Canary health check failed" && exit 1); \
		sleep 10; \
	done
	@echo "  Canary monitoring completed"

promote-canary: ## Promote canary to full deployment
	@echo "  Promoting canary to full deployment..."
	@kubectl scale deployment/$(APP_NAME) -n $(NAMESPACE) --replicas=0
	@kubectl scale deployment/$(APP_NAME)-canary -n $(NAMESPACE) --replicas=$(REPLICAS)
	@kubectl patch service $(APP_NAME) -n $(NAMESPACE) -p '{"spec":{"selector":{"app":"$(APP_NAME)-canary"}}}'

# A/B testing deployment
deploy-ab-test: ##   A/B testing deployment
	@echo "  A/B testing deployment..."
	@$(MAKE) deploy-version-a
	@$(MAKE) deploy-version-b
	@$(MAKE) setup-ab-routing
	@echo "  A/B test deployment ready"
```

### Rollout Management and Health Checks

Implement comprehensive rollout management:

makefile

```makefile
# =============================================================================
# Rollout Management and Health Checks
# =============================================================================

# Rollout monitoring
wait-for-rollout: ##   Wait for rollout to complete
	@echo "  Waiting for rollout to complete..."
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s
	@$(MAKE) verify-deployment-health
	@echo "  Rollout completed successfully"

wait-for-rollout-fast: ##   Quick rollout wait (development)
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=60s

wait-for-rollout-production: ##   Production rollout with extended monitoring
	@echo "  Production rollout monitoring..."
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=600s
	@$(MAKE) verify-deployment-health
	@$(MAKE) extended-health-monitoring
	@echo "  Production rollout completed"

# Health verification
verify-deployment-health: ##   Verify deployment health
	@echo "  Verifying deployment health..."
	@READY_REPLICAS=$$(kubectl get deployment $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.status.readyReplicas}'); \
	DESIRED_REPLICAS=$$(kubectl get deployment $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.replicas}'); \
	if [ "$$READY_REPLICAS" != "$$DESIRED_REPLICAS" ]; then \
		echo "  Health check failed: $$READY_REPLICAS/$$DESIRED_REPLICAS replicas ready"; \
		exit 1; \
	fi; \
	echo "  All $$READY_REPLICAS replicas are healthy"

extended-health-monitoring: ##   Extended health monitoring
	@echo "  Extended health monitoring..."
	@for i in $$(seq 1 12); do \
		echo "Health check $$i/12..."; \
		$(MAKE) app-health-check || (echo "  Application health check failed" && exit 1); \
		sleep 10; \
	done
	@echo "  Extended health monitoring passed"

app-health-check: ##   Application-specific health check
	@APP_URL=$$(kubectl get ingress $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.rules[0].host}' 2>/dev/null || echo "localhost"); \
	APP_PORT=$$(kubectl get service $(APP_NAME) -n $(NAMESPACE) -o jsonpath='{.spec.ports[0].nodePort}' 2>/dev/null || echo "8080"); \
	if kubectl get ingress $(APP_NAME) -n $(NAMESPACE) >/dev/null 2>&1; then \
		curl -f -m 10 http://$$APP_URL/health >/dev/null; \
	else \
		kubectl port-forward service/$(APP_NAME) $$APP_PORT:8080 -n $(NAMESPACE) & \
		PF_PID=$$!; \
		sleep 2; \
		curl -f -m 10 http://localhost:$$APP_PORT/health >/dev/null; \
		kill $$PF_PID 2>/dev/null || true; \
	fi

# Rollback operations
rollback: ##   Rollback to previous version
	@echo "  Rolling back to previous version..."
	@kubectl rollout undo deployment/$(APP_NAME) -n $(NAMESPACE)
	@kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s
	@$(MAKE) verify-deployment-health
	@echo "  Rollback completed"

rollback-to-revision: ##   Rollback to specific revision
	@read -p "Revision number: " REVISION; \
	echo "  Rolling back to revision $$REVISION..."; \
	kubectl rollout undo deployment/$(APP_NAME) -n $(NAMESPACE) --to-revision=$$REVISION; \
	kubectl rollout status deployment/$(APP_NAME) -n $(NAMESPACE) --timeout=300s; \
	$(MAKE) verify-deployment-health

# Deployment history
rollout-history: ##   Show rollout history
	@kubectl rollout history deployment/$(APP_NAME) -n $(NAMESPACE)

rollout-pause: ##    Pause rollout
	@kubectl rollout pause deployment/$(APP_NAME) -n $(NAMESPACE)
	@echo "   Rollout paused"

rollout-resume: ## ▶  Resume rollout
	@kubectl rollout resume deployment/$(APP_NAME) -n $(NAMESPACE)
	@echo "▶  Rollout resumed"
```

## Helm Chart Management and Customization

### Basic Helm Integration

Integrate Helm charts with Make for better orchestration:

makefile

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
	@echo "  Helm chart is valid"

helm-template: ##  Generate templates from Helm chart
	@echo " Generating templates from Helm chart..."
	@mkdir -p $(MANIFESTS_DIR)
	@helm template $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--output-dir $(MANIFESTS_DIR)
	@echo "  Templates generated in $(MANIFESTS_DIR)/"

helm-dry-run: ##   Dry run Helm installation
	@echo "  Helm dry run..."
	@helm install $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--dry-run --debug

helm-install: build push ##   Install with Helm
	@echo "  Installing with Helm..."
	@$(MAKE) validate-environment
	@helm install $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--wait --timeout=300s
	@$(MAKE) verify-helm-deployment
	@echo "  Helm installation completed"

helm-upgrade: build push ##   Upgrade with Helm
	@echo "  Upgrading with Helm..."
	@helm upgrade $(HELM_RELEASE_NAME) $(HELM_CHART) \
		--values $(HELM_VALUES_FILE) \
		--set image.tag=$(VERSION) \
		--set image.repository=$(REGISTRY)/$(APP_NAME) \
		--namespace $(NAMESPACE) \
		--wait --timeout=300s
	@$(MAKE) verify-helm-deployment
	@echo "  Helm upgrade completed"

helm-uninstall: ##   Uninstall Helm release
	@echo "   This will uninstall $(HELM_RELEASE_NAME). Continue? [y/N]" && read ans && [ $$ans = y ]
	@helm uninstall $(HELM_RELEASE_NAME) -n $(NAMESPACE)
	@echo "  Helm release uninstalled"

# Helm utilities
helm-status: ##   Show Helm release status
	@helm status $(HELM_RELEASE_NAME) -n $(NAMESPACE)

helm-get-values: ##   Show Helm values
	@helm get values $(HELM_RELEASE_NAME) -n $(NAMESPACE)

helm-history: ##   Show Helm release history
	@helm history $(HELM_RELEASE_NAME) -n $(NAMESPACE)

helm-rollback: ##   Rollback Helm release
	@read -p "Revision (or 'previous'): " REVISION; \
	if [ "$$REVISION" = "previous" ]; then \
		helm rollback $(HELM_RELEASE_NAME) -n $(NAMESPACE); \
	else \
		helm rollback $(HELM_RELEASE_NAME) $$REVISION -n $(NAMESPACE); \
	fi; \
	$(MAKE) verify-helm-deployment

verify-helm-deployment: ##   Verify Helm deployment
	@echo "  Verifying Helm deployment..."
	@helm status $(HELM_RELEASE_NAME) -n $(NAMESPACE) | grep -q "STATUS: deployed" || \
		(echo "  Helm deployment not in deployed state" && exit 1)
	@$(MAKE) verify-deployment-health
	@echo "  Helm deployment verification completed"
```

### Advanced Helm Workflows

Create sophisticated Helm workflows with dependency management:

makefile

```makefile
# =============================================================================
# Advanced Helm Workflows
# =============================================================================

# Helm dependencies
helm-dep-update: ##   Update Helm dependencies
	@echo "  Updating Helm dependencies..."
	@helm dependency update $(HELM_CHART)
	@echo "  Helm dependencies updated"

# Multi-chart deployment
deploy-full-stack: ##   Deploy full application stack with Helm
	@echo "  Deploying full application stack..."
	@$(MAKE) helm-install-database
	@$(MAKE) helm-install-cache
	@$(MAKE) helm-install-app
	@$(MAKE) helm-install-monitoring
	@echo "  Full stack deployment completed"

helm-install-database: ##    Install database chart
	@echo "   Installing database..."
	@helm install $(APP_NAME)-db charts/postgresql \
		--values helm/values-database-$(ENVIRONMENT).yaml \
		--namespace $(NAMESPACE) \
		--wait --timeout=300s

helm-install-cache: ##   Install cache chart
	@echo "  Installing cache..."
	@helm install $(APP_NAME)-cache charts/redis \
		--values helm/values-cache-$(ENVIRONMENT).yaml \
		--namespace $(NAMESPACE) \
		--wait --timeout=300s

helm-install-app: helm-install-database helm-install-cache ##   Install application chart
	@$(MAKE) helm-install

helm-install-monitoring: helm-install-app ##   Install monitoring stack
	@echo "  Installing monitoring..."
	@helm install $(APP_NAME)-monitoring charts/prometheus-stack \
		--values helm/values-monitoring-$(ENVIRONMENT).yaml \
		--namespace $(NAMESPACE)-monitoring \
		--create-namespace \
		--wait --timeout=600s

# Helm testing
helm-test: ##   Run Helm tests
	@echo "  Running Helm tests..."
	@helm test $(HELM_RELEASE_NAME) -n $(NAMESPACE)

# Environment-specific Helm workflows
helm-deploy: helm-deploy-$(ENVIRONMENT) ##   Environment-specific Helm deployment

helm-deploy-development: helm-lint helm-install ##   Development Helm deployment

helm-deploy-staging: helm-lint helm-dry-run helm-upgrade ##   Staging Helm deployment

helm-deploy-production: helm-lint helm-dry-run backup-current-state helm-upgrade ##   Production Helm deployment
	@$(MAKE) extended-health-monitoring
	@$(MAKE) helm-test
```

## Service Mesh Configuration and Monitoring Setup

🚧 WORK IN PROGRESS 🚧 
We will trim this chapter down a bit, it's getting too long. Some content will
move to other chapters, some will get tossed out completely.