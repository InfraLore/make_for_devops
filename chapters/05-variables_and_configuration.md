# Chapter 5 - Variables and Configuration Management
_Using Make's variable system to create flexible, environment-aware workflows that reduce configuration drift and improve consistency._

One of the most powerful aspects of Make is its sophisticated variable system. While many people think of Make variables as simple string substitution, they're actually a flexible configuration management system that can eliminate much of the complexity and inconsistency that plagues modern deployment workflows.

Consider a typical scenario: your application needs to be deployed to development, staging, and production environments. Each environment has different database URLs, different resource limits, different monitoring configurations, and different security requirements. Traditional approaches often involve maintaining separate scripts or configuration files for each environment, leading to drift, inconsistencies, and the inevitable "it works in staging but not production" problems.

Make's variable system offers a better way: **single workflow definitions with environment-aware configuration**. Instead of maintaining multiple deployment scripts, you maintain one Makefile that adapts its behavior based on clearly defined variables. This approach provides consistency, discoverability, and maintainability that scales from small teams to large organizations.

> [!IMPORTANT] Start Simple: Basic Variable Patterns
> Before exploring advanced configuration management, master these fundamental variable patterns:
> 
> 1. **Defaults with overrides**: `ENVIRONMENT ?= development` lets users override while providing sensible defaults
> 2. **Computed values**: `IMAGE_TAG = $(REGISTRY)/$(APP_NAME):$(VERSION)` builds complex values from simple inputs
> 3. **Environment detection**: `VERSION = $(shell git describe --tags --always)` pulls values from the system
> 4. **Validation**: Simple checks ensure required variables are set before execution
> 
> These patterns handle most configuration scenarios. Advanced techniques become valuable when managing complex, multi-environment deployments.
## Environment-Specific Configuration Patterns

### The Foundation: Default Values with Overrides

The most fundamental pattern in Make configuration management is providing sensible defaults while allowing easy overrides:

```makefile
# Application configuration with defaults
APP_NAME ?= myapp
VERSION ?= $(shell git describe --tags --always --dirty)
ENVIRONMENT ?= development

# Infrastructure configuration
REGISTRY ?= localhost:5000
NAMESPACE ?= $(APP_NAME)-$(ENVIRONMENT)
REPLICAS ?= 1

# Computed values that depend on base configuration
IMAGE_TAG = $(REGISTRY)/$(APP_NAME):$(VERSION)
DATABASE_NAME = $(APP_NAME)_$(ENVIRONMENT)
```

This pattern provides immediate value:

```bash
# Use defaults for quick development
make deploy

# Override for specific environments
make deploy ENVIRONMENT=staging REPLICAS=3

# Override for production deployment
make deploy ENVIRONMENT=production VERSION=v1.2.3 REPLICAS=5
```

### Environment-Specific Variable Files

For complex configurations, organize environment-specific variables in separate files:

```makefile
# Load environment-specific configuration
-include config/$(ENVIRONMENT).mk

# Fallback to development if environment file doesn't exist
ifeq ($(wildcard config/$(ENVIRONMENT).mk),)
  $(warning No configuration found for $(ENVIRONMENT), using development defaults)
  -include config/development.mk
endif
```

**config/development.mk:**

```makefile
REGISTRY = localhost:5000
REPLICAS = 1
DATABASE_URL = postgresql://localhost:5432/myapp_dev
LOG_LEVEL = DEBUG
ENABLE_DEBUG = true
```

**config/staging.mk:**

```makefile
REGISTRY = staging-registry.company.com
REPLICAS = 2
DATABASE_URL = postgresql://staging-db.company.com:5432/myapp_staging
LOG_LEVEL = INFO
ENABLE_DEBUG = false
MONITORING_ENABLED = true
```

**config/production.mk:**

```makefile
REGISTRY = registry.company.com
REPLICAS = 5
DATABASE_URL = postgresql://prod-db.company.com:5432/myapp_prod
LOG_LEVEL = WARN
ENABLE_DEBUG = false
MONITORING_ENABLED = true
BACKUP_ENABLED = true
```

### Dynamic Configuration Based on Environment

Create configuration that adapts intelligently to different environments:

```makefile
# Base configuration
APP_NAME = myapp
VERSION ?= $(shell git describe --tags --always)
ENVIRONMENT ?= development

# Environment-aware defaults
ifeq ($(ENVIRONMENT),production)
  REPLICAS ?= 5
  RESOURCE_LIMITS ?= high
  MONITORING_LEVEL ?= verbose
  BACKUP_SCHEDULE ?= daily
else ifeq ($(ENVIRONMENT),staging)
  REPLICAS ?= 2
  RESOURCE_LIMITS ?= medium
  MONITORING_LEVEL ?= standard
  BACKUP_SCHEDULE ?= weekly
else
  # Development defaults
  REPLICAS ?= 1
  RESOURCE_LIMITS ?= low
  MONITORING_LEVEL ?= basic
  BACKUP_SCHEDULE ?= none
endif

# Registry selection based on environment
ifeq ($(ENVIRONMENT),production)
  REGISTRY ?= prod-registry.company.com
else ifeq ($(ENVIRONMENT),staging)
  REGISTRY ?= staging-registry.company.com
else
  REGISTRY ?= localhost:5000
endif

# Computed values
IMAGE_TAG = $(REGISTRY)/$(APP_NAME):$(VERSION)
NAMESPACE = $(APP_NAME)-$(ENVIRONMENT)
```

### Configuration Validation and Safety Checks

Implement validation to prevent common configuration mistakes:

```makefile
# Validate required configuration
validate-config: ## Validate configuration before deployment
	@echo "Validating configuration for $(ENVIRONMENT)..."
	
	# Check required variables
	@test -n "$(VERSION)" || (echo " VERSION not set" && exit 1)
	@test -n "$(REGISTRY)" || (echo " REGISTRY not set" && exit 1)
	@test -n "$(DATABASE_URL)" || (echo " DATABASE_URL not set" && exit 1)
	
	# Validate environment values
	@case "$(ENVIRONMENT)" in \
		development|staging|production) ;; \
		*) echo " Invalid ENVIRONMENT: $(ENVIRONMENT)" && exit 1 ;; \
	esac
	
	# Environment-specific validations
	@if [ "$(ENVIRONMENT)" = "production" ]; then \
		test "$(REPLICAS)" -gt 1 || (echo " Production requires REPLICAS > 1" && exit 1); \
		test "$(BACKUP_ENABLED)" = "true" || (echo " Production requires BACKUP_ENABLED=true" && exit 1); \
	fi
	
	@echo " Configuration validation passed"

# Show current configuration
show-config: ## Display current configuration
	@echo "Current Configuration:"
	@echo " APP_NAME:     $(APP_NAME)"
	@echo " VERSION:      $(VERSION)"
	@echo " ENVIRONMENT:  $(ENVIRONMENT)"
	@echo " REGISTRY:     $(REGISTRY)"
	@echo " IMAGE_TAG:    $(IMAGE_TAG)"
	@echo " NAMESPACE:    $(NAMESPACE)"
	@echo " REPLICAS:     $(REPLICAS)"
	@echo " DATABASE_URL: $(shell echo '$(DATABASE_URL)' | sed 's/:[^@]*@/:***@/')"

# Always validate before deployment
deploy: validate-config
	@echo "Deploying $(APP_NAME) version $(VERSION) to $(ENVIRONMENT)..."
	# ... deployment commands
```

## Managing Secrets and Sensitive Data

Handling secrets in Make workflows requires special attention to avoid accidentally exposing sensitive data:

### Environment Variable Integration

The most secure approach is to rely on environment variables for sensitive data:

```makefile
# Never define secrets directly in Makefiles
# DATABASE_PASSWORD = mysecret  #   DON'T DO THIS

# Instead, require secrets to be provided via environment
check-secrets: ## Validate that required secrets are available
	@echo "Checking required secrets..."
	@test -n "$$DATABASE_PASSWORD" || (echo " DATABASE_PASSWORD environment variable required" && exit 1)
	@test -n "$$API_KEY" || (echo " API_KEY environment variable required" && exit 1)
	@echo " All required secrets are available"

# Use secrets in commands without exposing them
deploy: check-secrets
	@echo "Deploying with secrets..."
	kubectl create secret generic app-secrets \
		--from-literal=database-password="$$DATABASE_PASSWORD" \
		--from-literal=api-key="$$API_KEY" \
		--dry-run=client -o yaml | kubectl apply -f -
```

### Secret File Management

For development environments, you might need to load secrets from files:

```makefile
# Load secrets from environment file (for development only)
ifneq ($(ENVIRONMENT),production)
  # Only load .env in non-production environments
  ifneq ($(wildcard .env),)
    include .env
    export
  endif
endif

# Create development secrets file
create-dev-secrets: ## Create development .env file template
	@if [ ! -f .env ]; then \
		echo "Creating development .env file..."; \
		echo "# Development secrets - DO NOT COMMIT" > .env; \
		echo "DATABASE_PASSWORD=dev_password" >> .env; \
		echo "API_KEY=dev_api_key" >> .env; \
		echo "SECRET_KEY=$$(openssl rand -base64 32)" >> .env; \
		echo " Please edit .env with appropriate development values"; \
	else \
		echo ".env file already exists"; \
	fi

# Production secrets should come from secure systems
load-production-secrets: ## Load secrets from secure store (production)
ifeq ($(ENVIRONMENT),production)
	@echo "Loading production secrets from vault..."
	$(eval DATABASE_PASSWORD := $(shell vault kv get -field=password secret/myapp/database))
	$(eval API_KEY := $(shell vault kv get -field=api-key secret/myapp/external))
else
	@echo " load-production-secrets only works in production environment"
endif
```

### Secret Validation Without Exposure

Validate secrets without exposing their values in logs:

```makefile
# Validate secrets without printing them
validate-secrets: ## Validate secret format and availability
	@echo "Validating secrets..."
	
	# Check that secrets exist and have minimum length
	@test $${#DATABASE_PASSWORD} -ge 8 || (echo " DATABASE_PASSWORD too short" && exit 1)
	@test $${#API_KEY} -ge 16 || (echo " API_KEY too short" && exit 1)
	
	# Validate secret format without exposing values
	@echo "$$DATABASE_PASSWORD" | grep -q '[A-Za-z]' || (echo " DATABASE_PASSWORD should contain letters" && exit 1)
	@echo "$$API_KEY" | grep -q '^[A-Za-z0-9_-]*$$' || (echo " API_KEY contains invalid characters" && exit 1)
	
	@echo " Secret validation passed"

# Show secret status without values
show-secret-status: ## Show status of secrets without exposing values
	@echo "Secret Status:"
	@echo " DATABASE_PASSWORD: $$(test -n "$$DATABASE_PASSWORD" && echo "Set (length: $${#DATABASE_PASSWORD})" || echo "Not set")"
	@echo " API_KEY: $$(test -n "$$API_KEY" && echo "Set (length: $${#API_KEY})" || echo "Not set")"
	@echo " SECRET_KEY: $$(test -n "$$SECRET_KEY" && echo "Set (length: $${#SECRET_KEY})" || echo "Not set")"
```

## Creating Reusable Variable Libraries

As your Make-based workflows grow, you'll want to create reusable variable libraries that can be shared across projects:

### Common Variable Libraries

Create shared configuration files for common patterns:

**lib/common.mk:**

```makefile
# Common variable patterns for all projects

# Git-based versioning
GIT_COMMIT = $(shell git rev-parse --short HEAD)
GIT_BRANCH = $(shell git rev-parse --abbrev-ref HEAD)
GIT_TAG = $(shell git describe --tags --exact-match 2>/dev/null)
VERSION ?= $(if $(GIT_TAG),$(GIT_TAG),$(GIT_BRANCH)-$(GIT_COMMIT))

# Clean branch name for use in resource names
CLEAN_BRANCH = $(shell echo $(GIT_BRANCH) | sed 's/[^a-zA-Z0-9-]/-/g' | tr '[:upper:]' '[:lower:]')

# Common registry patterns
REGISTRY_HOST ?= registry.company.com
REGISTRY_PROJECT ?= $(shell basename `git rev-parse --show-toplevel`)
REGISTRY = $(REGISTRY_HOST)/$(REGISTRY_PROJECT)

# Kubernetes namespace patterns
BASE_NAMESPACE ?= $(shell basename `git rev-parse --show-toplevel`)
NAMESPACE = $(BASE_NAMESPACE)-$(ENVIRONMENT)

# Build timestamp
BUILD_TIME = $(shell date -u +%Y%m%d-%H%M%S)
BUILD_USER = $(shell whoami)

# Common resource tagging
COMMON_LABELS = app=$(APP_NAME),version=$(VERSION),environment=$(ENVIRONMENT),built-by=$(BUILD_USER)
```

**lib/docker.mk:**

```makefile
# Docker-specific variable patterns

# Image naming conventions
DOCKER_ORG ?= mycompany
IMAGE_NAME ?= $(DOCKER_ORG)/$(APP_NAME)
IMAGE_TAG ?= $(IMAGE_NAME):$(VERSION)
LATEST_TAG ?= $(IMAGE_NAME):latest

# Build arguments
DOCKER_BUILD_ARGS ?= \
	--build-arg VERSION=$(VERSION) \
	--build-arg BUILD_TIME=$(BUILD_TIME) \
	--build-arg GIT_COMMIT=$(GIT_COMMIT)

# Multi-platform builds
DOCKER_PLATFORMS ?= linux/amd64,linux/arm64

# Registry authentication helper
DOCKER_CONFIG_DIR = ~/.docker
```

**lib/kubernetes.mk:**

```makefile
# Kubernetes-specific variable patterns

# Cluster configuration
KUBE_CONTEXT ?= $(ENVIRONMENT)
KUBE_NAMESPACE = $(APP_NAME)-$(ENVIRONMENT)

# Resource naming
DEPLOYMENT_NAME = $(APP_NAME)
SERVICE_NAME = $(APP_NAME)
INGRESS_NAME = $(APP_NAME)

# Resource configuration
RESOURCE_REQUESTS_CPU ?= 100m
RESOURCE_REQUESTS_MEMORY ?= 128Mi
RESOURCE_LIMITS_CPU ?= 500m
RESOURCE_LIMITS_MEMORY ?= 512Mi

# Environment-specific overrides
ifeq ($(ENVIRONMENT),production)
  RESOURCE_REQUESTS_CPU = 200m
  RESOURCE_REQUESTS_MEMORY = 256Mi
  RESOURCE_LIMITS_CPU = 1000m
  RESOURCE_LIMITS_MEMORY = 1Gi
endif
```

### Using Variable Libraries

Include libraries in your project Makefiles:

```makefile
# Include common libraries
include lib/common.mk
include lib/docker.mk
include lib/kubernetes.mk

# Project-specific configuration
APP_NAME = myapp
ENVIRONMENT ?= development

# Override library defaults as needed
DOCKER_ORG = myteam
RESOURCE_REQUESTS_MEMORY = 256Mi

# Use library variables in targets
build: ## Build Docker image
	docker build $(DOCKER_BUILD_ARGS) -t $(IMAGE_TAG) .
	docker tag $(IMAGE_TAG) $(LATEST_TAG)

deploy: ## Deploy to Kubernetes
	kubectl config use-context $(KUBE_CONTEXT)
	kubectl apply -f k8s/ -n $(KUBE_NAMESPACE)
	kubectl set image deployment/$(DEPLOYMENT_NAME) app=$(IMAGE_TAG) -n $(KUBE_NAMESPACE)
```

## Integration with External Configuration Sources

Modern applications often need to integrate with external configuration management systems:

### Cloud Parameter Stores

Integrate with cloud-native parameter stores:

```makefile
# AWS Parameter Store integration
load-aws-config: ## Load configuration from AWS Parameter Store
	@echo "Loading configuration from AWS Parameter Store..."
	$(eval DATABASE_URL := $(shell aws ssm get-parameter --name "/myapp/$(ENVIRONMENT)/database-url" --with-decryption --query 'Parameter.Value' --output text))
	$(eval API_ENDPOINT := $(shell aws ssm get-parameter --name "/myapp/$(ENVIRONMENT)/api-endpoint" --query 'Parameter.Value' --output text))
	@echo " Configuration loaded from Parameter Store"

# Google Secret Manager integration
load-gcp-config: ## Load configuration from Google Secret Manager
	@echo "Loading configuration from Google Secret Manager..."
	$(eval DATABASE_PASSWORD := $(shell gcloud secrets versions access latest --secret="myapp-$(ENVIRONMENT)-db-password"))
	$(eval API_KEY := $(shell gcloud secrets versions access latest --secret="myapp-$(ENVIRONMENT)-api-key"))
	@echo " Configuration loaded from Secret Manager"

# HashiCorp Vault integration
load-vault-config: ## Load configuration from Vault
	@echo "Loading configuration from Vault..."
	$(eval VAULT_DATA := $(shell vault kv get -format=json secret/myapp/$(ENVIRONMENT)))
	$(eval DATABASE_URL := $(shell echo '$(VAULT_DATA)' | jq -r '.data.data.database_url'))
	$(eval API_KEY := $(shell echo '$(VAULT_DATA)' | jq -r '.data.data.api_key'))
	@echo " Configuration loaded from Vault"

# Use external configuration in deployment
deploy: load-$(CONFIG_SOURCE)-config validate-config
	@echo "Deploying with externally loaded configuration..."
	# ... deployment commands that use loaded variables
```

### Configuration File Formats

Support multiple configuration file formats:

```makefile
# YAML configuration support
load-yaml-config: ## Load configuration from YAML file
	@if [ -f config/$(ENVIRONMENT).yaml ]; then \
		echo "Loading YAML configuration..."; \
		$(eval DATABASE_URL := $(shell yq e '.database.url' config/$(ENVIRONMENT).yaml)); \
		$(eval REPLICAS := $(shell yq e '.deployment.replicas' config/$(ENVIRONMENT).yaml)); \
	fi

# JSON configuration support
load-json-config: ## Load configuration from JSON file
	@if [ -f config/$(ENVIRONMENT).json ]; then \
		echo "Loading JSON configuration..."; \
		$(eval DATABASE_URL := $(shell jq -r '.database.url' config/$(ENVIRONMENT).json)); \
		$(eval REPLICAS := $(shell jq -r '.deployment.replicas' config/$(ENVIRONMENT).json)); \
	fi

# TOML configuration support
load-toml-config: ## Load configuration from TOML file
	@if [ -f config/$(ENVIRONMENT).toml ]; then \
		echo "Loading TOML configuration..."; \
		$(eval DATABASE_URL := $(shell toml get config/$(ENVIRONMENT).toml database.url)); \
		$(eval REPLICAS := $(shell toml get config/$(ENVIRONMENT).toml deployment.replicas)); \
	fi

# Auto-detect configuration format
load-config: ## Auto-detect and load configuration
	@if [ -f config/$(ENVIRONMENT).yaml ]; then \
		$(MAKE) load-yaml-config; \
	elif [ -f config/$(ENVIRONMENT).json ]; then \
		$(MAKE) load-json-config; \
	elif [ -f config/$(ENVIRONMENT).toml ]; then \
		$(MAKE) load-toml-config; \
	elif [ -f config/$(ENVIRONMENT).mk ]; then \
		echo "Loading Make configuration..."; \
		include config/$(ENVIRONMENT).mk; \
	else \
		echo " No configuration file found for $(ENVIRONMENT)"; \
	fi
```

## Validation and Error Handling for Configuration Values

Robust configuration management includes comprehensive validation:

### Type and Format Validation

```makefile
# Validate configuration types and formats
validate-config-types: ## Validate configuration value types and formats
	@echo "Validating configuration types..."
	
	# Validate numeric values
	@echo "$(REPLICAS)" | grep -qE '^[0-9]+$$' || (echo " REPLICAS must be numeric: $(REPLICAS)" && exit 1)
	@test "$(REPLICAS)" -gt 0 || (echo " REPLICAS must be positive: $(REPLICAS)" && exit 1)
	
	# Validate URL formats
	@echo "$(DATABASE_URL)" | grep -qE '^[a-z]+://.*' || (echo " DATABASE_URL invalid format: $(DATABASE_URL)" && exit 1)
	
	# Validate version format
	@echo "$(VERSION)" | grep -qE '^v?[0-9]+\.[0-9]+\.[0-9]+' || echo " VERSION doesn't follow semver: $(VERSION)"
	
	# Validate environment values
	@case "$(ENVIRONMENT)" in \
		development|dev|staging|stage|production|prod) ;; \
		*) echo " Invalid ENVIRONMENT: $(ENVIRONMENT)" && exit 1 ;; \
	esac
	
	@echo " Configuration type validation passed"

# Validate configuration relationships
validate-config-relationships: ## Validate relationships between configuration values
	@echo "Validating configuration relationships..."
	
	# Production-specific validations
	@if [ "$(ENVIRONMENT)" = "production" ]; then \
		test "$(REPLICAS)" -ge 2 || (echo " Production requires REPLICAS >= 2" && exit 1); \
		echo "$(DATABASE_URL)" | grep -q "prod" || echo " Production should use production database"; \
		test "$(MONITORING_ENABLED)" = "true" || (echo " Production requires MONITORING_ENABLED=true" && exit 1); \
	fi
	
	# Development-specific validations
	@if [ "$(ENVIRONMENT)" = "development" ]; then \
		echo "$(DATABASE_URL)" | grep -qv "prod" || (echo " Development should not use production database" && exit 1); \
	fi
	
	@echo " Configuration relationship validation passed"
```

### Configuration Drift Detection

Detect when configuration drifts from expected patterns:

```makefile
# Store baseline configuration
save-config-baseline: ## Save current configuration as baseline
	@echo "Saving configuration baseline..."
	@mkdir -p .config-baselines
	@$(MAKE) show-config > .config-baselines/$(ENVIRONMENT)-baseline.txt
	@echo " Baseline saved to .config-baselines/$(ENVIRONMENT)-baseline.txt"

# Detect configuration drift
detect-config-drift: ## Detect drift from baseline configuration
	@echo "Detecting configuration drift for $(ENVIRONMENT)..."
	@if [ ! -f .config-baselines/$(ENVIRONMENT)-baseline.txt ]; then \
		echo " No baseline found for $(ENVIRONMENT). Run 'make save-config-baseline' first"; \
		exit 0; \
	fi
	@$(MAKE) show-config > .config-baselines/$(ENVIRONMENT)-current.txt
	@if ! diff -u .config-baselines/$(ENVIRONMENT)-baseline.txt .config-baselines/$(ENVIRONMENT)-current.txt > .config-baselines/$(ENVIRONMENT)-drift.txt; then \
		echo " Configuration drift detected for $(ENVIRONMENT):"; \
		cat .config-baselines/$(ENVIRONMENT)-drift.txt; \
		echo "Run 'make save-config-baseline' to update baseline if this change is intentional"; \
	else \
		echo " No configuration drift detected"; \
		rm .config-baselines/$(ENVIRONMENT)-current.txt .config-baselines/$(ENVIRONMENT)-drift.txt; \
	fi
```

## Putting It All Together: A Complete Configuration Management Example

Here's how all these patterns come together in a real-world Makefile:

```makefile
# =============================================================================
# Configuration Management Example
# =============================================================================

# Include reusable libraries
include lib/common.mk
include lib/docker.mk
include lib/kubernetes.mk

# Application configuration
APP_NAME = example-app
ENVIRONMENT ?= development

# Load environment-specific configuration
-include config/$(ENVIRONMENT).mk

# Configuration validation and defaults
ifeq ($(ENVIRONMENT),production)
  REPLICAS ?= 3
  MONITORING_ENABLED ?= true
  BACKUP_ENABLED ?= true
else
  REPLICAS ?= 1
  MONITORING_ENABLED ?= false
  BACKUP_ENABLED ?= false
endif

# Main workflow targets
.PHONY: config deploy validate-config show-config

deploy: validate-config ## Deploy application
	@echo " Deploying $(APP_NAME) version $(VERSION) to $(ENVIRONMENT)"
	@$(MAKE) build
	@$(MAKE) push
	@$(MAKE) deploy-k8s
	@echo " Deployment complete"

validate-config: ## Comprehensive configuration validation
	@echo " Validating configuration..."
	@$(MAKE) validate-required-vars
	@$(MAKE) validate-config-types
	@$(MAKE) validate-config-relationships
	@$(MAKE) validate-secrets
	@echo " All configuration validation passed"

show-config: ## Display current configuration
	@echo " Current Configuration ($(ENVIRONMENT)):"
	@echo " App: $(APP_NAME) v$(VERSION)"
	@echo " Image: $(IMAGE_TAG)"
	@echo " Namespace: $(KUBE_NAMESPACE)"
	@echo " Replicas: $(REPLICAS)"
	@echo " Registry: $(REGISTRY)"
	@echo " Monitoring: $(MONITORING_ENABLED)"
	@echo " Backup: $(BACKUP_ENABLED)"

# Helper targets for specific validations
validate-required-vars:
	@test -n "$(APP_NAME)" || (echo " APP_NAME required" && exit 1)
	@test -n "$(VERSION)" || (echo " VERSION required" && exit 1)
	@test -n "$(ENVIRONMENT)" || (echo " ENVIRONMENT required" && exit 1)

validate-config-types:
	@echo "$(REPLICAS)" | grep -qE '^[0-9]+$$' || (echo " REPLICAS must be numeric" && exit 1)
	@case "$(ENVIRONMENT)" in development|staging|production) ;; *) echo " Invalid ENVIRONMENT" && exit 1 ;; esac

validate-config-relationships:
	@if [ "$(ENVIRONMENT)" = "production" ]; then \
		test "$(REPLICAS)" -ge 2 || (echo " Production requires REPLICAS >= 2" && exit 1); \
		test "$(MONITORING_ENABLED)" = "true" || (echo " Production requires monitoring" && exit 1); \
	fi

validate-secrets:
	@test -n "$$DATABASE_PASSWORD" || (echo " DATABASE_PASSWORD environment variable required" && exit 1)

# Configuration management utilities
config-help: ## Show configuration help
	@echo "Configuration Help"
	@echo "=================="
	@echo ""
	@echo "Environment Variables:"
	@echo " ENVIRONMENT     - Target environment (development|staging|production)"
	@echo " VERSION         - Application version (defaults to git describe)"
	@echo " REPLICAS        - Number of replicas (environment-specific defaults)"
	@echo ""
	@echo "Required Secrets (via environment variables):"
	@echo " DATABASE_PASSWORD - Database password"
	@echo " API_KEY          - External API key"
	@echo ""
	@echo "Configuration Files:"
	@echo " config/development.mk - Development environment config"
	@echo " config/staging.mk     - Staging environment config"
	@echo " config/production.mk  - Production environment config"
	@echo ""
	@echo "Examples:"
	@echo " make deploy                                    # Deploy to development"
	@echo " make deploy ENVIRONMENT=staging               # Deploy to staging"
	@echo " make deploy ENVIRONMENT=production VERSION=v1.0.0  # Deploy to production"

create-config-template: ## Create configuration template for new environment
	@read -p "Environment name: " ENV; \
	if [ -f "config/$$ENV.mk" ]; then \
		echo " Configuration for $$ENV already exists"; \
		exit 1; \
	fi; \
	echo "Creating configuration template for $$ENV..."; \
	mkdir -p config; \
	echo "# Configuration for $$ENV environment" > "config/$$ENV.mk"; \
	echo "REGISTRY = registry.company.com" >> "config/$$ENV.mk"; \
	echo "REPLICAS = 1" >> "config/$$ENV.mk"; \
	echo "MONITORING_ENABLED = false" >> "config/$$ENV.mk"; \
	echo "BACKUP_ENABLED = false" >> "config/$$ENV.mk"; \
	echo " Template created at config/$$ENV.mk"
```

## Key Takeaways

Make's variable system transforms from a simple string substitution mechanism into a powerful configuration management platform when you understand its full capabilities. The key principles to remember:

1. **Start with Defaults**: Always provide sensible default values that work for development, but make everything configurable
    
2. **Environment Awareness**: Design your variables to adapt intelligently to different deployment environments
    
3. **Validation First**: Validate configuration early and fail fast with clear error messages
    
4. **Security by Design**: Never embed secrets in Makefiles; use environment variables and external systems
    
5. **Reusability**: Create shared variable libraries that can be used across multiple projects
    
6. **Discoverability**: Make your configuration self-documenting with help targets and clear variable names
    
7. **Integration**: Connect with external configuration management systems when needed
    

The investment in sophisticated configuration management pays dividends in reduced deployment errors, easier onboarding, and more reliable operations across all environments.

In the next chapter, we'll explore how to organize and structure your Make targets using phony targets and dependency management to create intuitive, discoverable workflows that scale with your team's needs.