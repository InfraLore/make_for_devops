# Chapter 13: Make for Infrastructure Provisioning

\chaptersubtitle{Orchestrating infrastructure-as-code workflows with consistency, safety, and team-wide discoverability.}

The transition from application deployment to infrastructure provisioning represents one of the most critical—and often most chaotic—aspects of modern DevOps. While CI/CD pipelines have become relatively standardized for deploying applications, infrastructure provisioning workflows remain surprisingly ad-hoc across most organizations. Senior engineers keep complex Terraform commands in their shell history, CloudFormation deployments require consulting multiple wiki pages, and the question "how do I provision a new environment?" often yields different answers from different team members.

This chaos isn't just an inconvenience—it's a significant risk. Infrastructure provisioning involves making changes to the very foundation of your systems. Yet these workflows are often the least documented, least standardized, and most dependent on team lore that lives only in senior engineers' minds.

Make provides a powerful solution by creating a discoverable interface for infrastructure workflows. Instead of maintaining prose documentation that drifts out of sync, you create executable targets that encode both the workflow and its documentation in one place.

## The Infrastructure Provisioning Challenge

Before diving into solutions, let's understand why infrastructure provisioning is particularly challenging.

Consider what a typical Terraform workflow looks like when you ask a senior engineer "How do I deploy staging?":

```bash
# Um, first make sure you're on the right branch
git checkout infrastructure/staging-v2

# Then set up AWS credentials... I think it's this profile?
export AWS_PROFILE=staging
export AWS_REGION=us-west-2

# Initialize with the backend config... let me find that command
terraform init -backend-config="bucket=company-terraform-state" \
  -backend-config="key=staging/us-west-2/terraform.tfstate" \
  -backend-config="region=us-east-1" \
  -backend-config="dynamodb_table=terraform-locks"

# Select or create the workspace
terraform workspace select staging-v2 || terraform workspace new staging-v2

# Now plan... wait, which var file?
terraform plan -var-file="environments/staging.tfvars" \
  -var="environment=staging" -var="version=v2.3.1" -out=staging.tfplan

# Review that carefully, then apply
terraform apply staging.tfplan

# Oh, and don't forget to tag the resources afterward...
```

This is a simplified example. The real version includes error handling,
validation checks, state file backups, cost estimation, and approval gates. Each
step has potential failure modes. Documenting this in a README means maintaining
a complex, multi-step prose description that will inevitably drift from reality.

The challenge is compounded by:

- **State management**: Terraform maintains state that's precious and fragile
- **Multi-environment complexity**: Each environment needs different
  configurations and safety levels
- **Dependency ordering**: Some infrastructure must exist before other
  infrastructure
- **Cost implications**: A mistake can spin up expensive resources indefinitely
- **Safety requirements**: Production needs different approval workflows than
  development

## The Discovery Pattern for Infrastructure

Rather than trying to document every step and flag, Make lets you create a
discoverable interface that reveals workflows as you need them.

Here's how that same workflow becomes discoverable (see next page):

```makefile
.DEFAULT_GOAL := help

help: ## Show available infrastructure commands
	@echo "Infrastructure Commands"
	@echo "======================"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
	@echo ""
	@echo "Current: ENVIRONMENT=$(ENVIRONMENT) REGION=$(REGION)"

init: check-environment ## Initialize Terraform for this environment
	@echo "Initializing $(ENVIRONMENT)..."
	@./scripts/terraform-init.sh $(ENVIRONMENT) $(REGION)

plan: init ## Create infrastructure plan
	@echo "Planning $(ENVIRONMENT)..."
	@./scripts/terraform-plan.sh $(ENVIRONMENT)
	@echo ""
	@echo "Review plan above. To apply: make apply"

apply: require-plan ## Apply infrastructure changes
	@echo "Applying to $(ENVIRONMENT)..."
	@./scripts/terraform-apply.sh $(ENVIRONMENT)

check-environment:
	@test -n "$(ENVIRONMENT)" || \
		(echo "Set ENVIRONMENT=dev|staging|prod" && exit 1)
	@test -f "environments/$(ENVIRONMENT).tfvars" || \
		(echo "Config not found for $(ENVIRONMENT)" && exit 1)

require-plan:
	@test -f "plans/$(ENVIRONMENT).tfplan" || \
		(echo "Run 'make plan' first" && exit 1)
```

Now a new engineer runs `make help` and discovers:

```
Infrastructure Commands
======================

  init                 Initialize Terraform for this environment
  plan                 Create infrastructure plan
  apply                Apply infrastructure changes
  
Current: ENVIRONMENT= REGION=
```

They see they need to set `ENVIRONMENT`, so they try:

```bash
make init ENVIRONMENT=staging
```

The workflow reveals itself progressively. Each target provides clear feedback
about what's happening and what to do next. The complexity is hidden in scripts,
but the interface is simple and discoverable.

## Progressive Disclosure of Complexity

The key principle is **progressive disclosure**: show simple interfaces first,
reveal complexity as needed.

```makefile
# Simple top-level interface
deploy-dev: ## Quick deploy to development
	@$(MAKE) _deploy ENV=development AUTO_APPROVE=true

deploy-staging: ## Deploy to staging (requires review)
	@$(MAKE) _deploy ENV=staging

deploy-prod: ## Deploy to production (requires approval)
	@echo "Production deployment requires:"
	@echo "  - Approved change ticket"
	@echo "  - Tech lead sign-off"
	@echo ""
	@$(MAKE) _require-change-ticket
	@$(MAKE) _deploy ENV=production

# Internal target that does the real work
_deploy:
	@$(MAKE) init ENVIRONMENT=$(ENV)
	@$(MAKE) validate ENVIRONMENT=$(ENV)
	@$(MAKE) plan ENVIRONMENT=$(ENV)
	@if [ "$(AUTO_APPROVE)" = "true" ]; then \
		$(MAKE) apply-auto ENVIRONMENT=$(ENV); \
	else \
		echo ""; \
		echo "Review plan. To apply: make apply ENVIRONMENT=$(ENV)"; \
	fi
```

Notice the pattern:

- Public targets (`deploy-dev`, `deploy-staging`) are simple and clear
- Implementation details are in `_deploy` (underscore prefix indicates internal)
- Each environment has appropriate safety levels
- Complexity is hidden but accessible when needed

## Environment-Specific Discovery

Different environments need different workflows. Make this discoverable:

```makefile
help: ## Show commands (environment-specific)
	@if [ "$(ENVIRONMENT)" = "production" ]; then \
		$(MAKE) help-production; \
	elif [ "$(ENVIRONMENT)" = "staging" ]; then \
		$(MAKE) help-staging; \
	else \
		$(MAKE) help-development; \
	fi

help-development:
	@echo "Development Environment"
	@echo "======================="
	@echo "  make deploy-dev       - Quick deploy (auto-apply)"
	@echo "  make destroy-dev      - Clean up dev resources"
	@echo "  make reset-dev        - Destroy and recreate"

help-staging:
	@echo "Staging Environment"
	@echo "==================="
	@echo "  make plan             - Create deployment plan"
	@echo "  make apply            - Apply reviewed plan"
	@echo "  make rollback         - Rollback to previous state"

help-production:
	@echo "Production Environment"
	@echo "======================"
	@echo "  make plan             - Create deployment plan"
	@echo "  make apply            - Apply (requires CHANGE_TICKET)"
	@echo "  make emergency        - Emergency procedures"
	@echo ""
	@echo "All production changes require change tickets"
```

Now when someone runs `make help ENVIRONMENT=production`, they see only
production-relevant commands with appropriate warnings.

## Discovering Infrastructure Components

Many infrastructure deployments have multiple components with dependencies. Make
these relationships discoverable:

```makefile
help: ## Show infrastructure components
	@echo "Infrastructure Components"
	@echo "========================"
	@echo ""
	@echo "Core Infrastructure:"
	@echo "  make deploy-networking    - VPC, subnets, gateways"
	@echo "  make deploy-security      - Security groups, IAM (needs: network)"
	@echo "  make deploy-data          - Databases, caches (needs: security)"
	@echo ""
	@echo "Application Layer:"
	@echo "  make deploy-compute       - ECS/EKS clusters (needs: data)"
	@echo "  make deploy-apps          - Applications (needs: compute)"
	@echo ""
	@echo "Supporting:"
	@echo "  make deploy-monitoring    - Monitoring stack (needs: network)"
	@echo ""
	@echo "Complete workflows:"
	@echo "  make deploy-all           - Deploy entire stack"
	@echo "  make status-all           - Check all components"

# Component targets encode dependencies
deploy-data: deploy-security ## Deploy databases
	@$(MAKE) _deploy-component COMPONENT=data

deploy-compute: deploy-data ## Deploy compute layer
	@$(MAKE) _deploy-component COMPONENT=compute

# The _deploy-component target handles the actual work
_deploy-component:
	@./scripts/deploy-component.sh $(COMPONENT) $(ENVIRONMENT)
```

The help output makes the architecture and dependencies obvious. New engineers
can understand the system structure just by running `make help`.

## Discovering Safety Checks

Infrastructure changes are risky. Make safety checks discoverable:

```makefile
apply: ## Apply infrastructure changes
	@echo "Pre-flight checks for $(ENVIRONMENT)..."
	@$(MAKE) _safety-checks
	@$(MAKE) _apply-with-confirmation

_safety-checks:
	@echo "Checking prerequisites..."
	@$(MAKE) _check-environment
	@$(MAKE) _check-credentials
	@$(MAKE) _check-state-lock
	@if [ "$(ENVIRONMENT)" = "production" ]; then \
		$(MAKE) _check-production-requirements; \
	fi
	@echo "All safety checks passed"

_check-production-requirements:
	@echo "Checking production requirements..."
	@test -n "$(CHANGE_TICKET)" || \
		(echo "Production requires CHANGE_TICKET" && exit 1)
	@test "$(git symbolic-ref --short HEAD)" = "main" || \
		(echo "Must deploy from main branch" && exit 1)
	@echo "Production requirements met"
```

When someone tries to deploy to production without following the process, they
get clear, actionable feedback:

```bash
$ make apply ENVIRONMENT=production
Pre-flight checks for production...
Checking prerequisites...
Checking production requirements...
Production requires CHANGE_TICKET

# They now know what's needed
$ make apply ENVIRONMENT=production CHANGE_TICKET=CHG-12345
```

## Discovering Cost and Impact

Infrastructure has cost implications. Make this visible:

```makefile
plan: ## Create deployment plan with cost estimate
	@$(MAKE) _create-plan
	@if command -v infracost >/dev/null 2>&1; then \
		$(MAKE) _show-cost-estimate; \
	fi
	@$(MAKE) _show-impact-summary

_show-impact-summary:
	@echo ""
	@echo "Impact Summary"
	@echo "=============="
	@terraform show plans/$(ENVIRONMENT).tfplan | \
		grep -E "(will be created|will be destroyed|will be updated)" | \
		sort | uniq -c
	@echo ""
	@echo "To apply: make apply ENVIRONMENT=$(ENVIRONMENT)"

_show-cost-estimate:
	@echo ""
	@echo "Estimated Costs"
	@echo "==============="
	@infracost breakdown --path=plans/$(ENVIRONMENT).tfplan \
		--format=table --show-skipped
```

Now `make plan` automatically shows what will change and what it will cost,
making the impact discoverable before any changes are made.

## Discovering Drift and State

Infrastructure drift—when actual infrastructure diverges from Terraform state—is
a common problem. Make it discoverable:

```makefile
status: ## Check infrastructure status
	@echo "Infrastructure Status - $(ENVIRONMENT)"
	@echo "====================================="
	@$(MAKE) _show-resource-count
	@$(MAKE) _check-drift-quick
	@echo ""
	@echo "Detailed commands:"
	@echo "  make drift-report     - Detailed drift analysis"
	@echo "  make resources        - List all resources"
	@echo "  make state-history    - Show recent state changes"

_check-drift-quick:
	@echo ""
	@echo "Drift Check:"
	@terraform plan -detailed-exitcode > /dev/null 2>&1; \
	case $$? in \
		0) echo "  No drift detected" ;; \
		2) echo "  Drift detected - run 'make drift-report'" ;; \
		*) echo "  Error checking drift" ;; \
	esac

drift-report: ## Detailed drift analysis
	@echo "Analyzing drift for $(ENVIRONMENT)..."
	@./scripts/drift-analysis.sh $(ENVIRONMENT)
```

Running `make status` gives a quick overview and points to more detailed
commands when needed.

## Discovering Multi-Region Patterns

When infrastructure spans regions, make the pattern discoverable:

```makefile
REGIONS ?= us-east-1 us-west-2 eu-west-1

help-multi-region: ## Show multi-region commands
	@echo "Multi-Region Deployment"
	@echo "======================="
	@echo "Regions: $(REGIONS)"
	@echo ""
	@echo "  make plan-all-regions     - Plan all regions"
	@echo "  make apply-all-regions    - Deploy to all regions"
	@echo "  make status-all-regions   - Status across regions"
	@echo ""
	@echo "Single region:"
	@echo "  make plan REGION=us-east-1"

plan-all-regions: ## Plan deployment across all regions
	@for region in $(REGIONS); do \
		echo ""; \
		echo "=== $$region ==="; \
		$(MAKE) plan ENVIRONMENT=$(ENVIRONMENT) REGION=$$region; \
	done
	@echo ""
	@echo "To deploy all: make apply-all-regions"

status-all-regions: ## Check status across regions
	@for region in $(REGIONS); do \
		echo "=== $$region ==="; \
		$(MAKE) _quick-status REGION=$$region; \
		echo ""; \
	done
```

The pattern is clear: Make handles the orchestration, showing what's happening
in each region while keeping the interface simple.

## Discovering Emergency Procedures

When things go wrong, discoverability becomes critical:

```makefile
emergency: ## Show emergency procedures
	@echo "Emergency Procedures"
	@echo "======================="
	@echo ""
	@echo "Infrastructure Issues:"
	@echo "  make emergency-status     - Quick health check"
	@echo "  make emergency-rollback   - Rollback to last good state"
	@echo "  make emergency-scale-down - Reduce to minimum resources"
	@echo ""
	@echo "State Issues:"
	@echo "  make state-unlock         - Unlock stuck state"
	@echo "  make state-recover        - Recover from backup"
	@echo ""
	@echo "Contact: #infrastructure-emergency on Slack"

emergency-status: ## Quick infrastructure health check
	@echo "Emergency Status Check - $(ENVIRONMENT)"
	@echo "========================================"
	@./scripts/emergency-status.sh $(ENVIRONMENT)
	@echo ""
	@echo "Next steps: make emergency-rollback or contact on-call"

emergency-rollback: ## Rollback to last known good state
	@echo "EMERGENCY ROLLBACK"
	@echo ""
	@echo "This will restore infrastructure to last backup"
	@./scripts/emergency-rollback.sh $(ENVIRONMENT)
```

In a crisis, `make emergency` immediately shows available options without
requiring anyone to hunt through documentation.

## Discovering Through Examples

The help system can include examples that teach the workflow:

```makefile
examples: ## Show common workflow examples
	@echo "Common Infrastructure Workflows"
	@echo "==============================="
	@echo ""
	@echo "First time setup:"
	@echo "  $$ make setup-backend ENVIRONMENT=staging"
	@echo "  $$ make init ENVIRONMENT=staging"
	@echo ""
	@echo "Regular deployment:"
	@echo "  $$ make plan ENVIRONMENT=staging"
	@echo "  $$ make apply ENVIRONMENT=staging"
	@echo ""
	@echo "Deploying a single component:"
	@echo "  $$ make deploy-component COMPONENT=networking ENV=staging"
	@echo ""
	@echo "Production deployment:"
	@echo "  $$ make plan ENVIRONMENT=production"
	@echo "  $$ make apply ENVIRONMENT=production CHANGE_TICKET=CHG-12345"
	@echo ""
	@echo "Checking status:"
	@echo "  $$ make status ENVIRONMENT=staging"
	@echo "  $$ make drift-report ENVIRONMENT=staging"
```

## Real-World Discovery Story

Let's look at how discovery patterns work in practice.

### The Old Way: 50-Page Wiki

The team maintained a comprehensive wiki titled "Infrastructure Provisioning
Guide":

```markdown
# Deploying to Staging

Prerequisites:

- AWS CLI installed (version 2.x)
- Terraform 1.5.0 or higher
- Access to 1Password for credentials
- VPN connected to staging network

Steps:

1. Configure AWS credentials...
   [15 lines of instructions]
2. Initialize Terraform backend...
   [20 lines of commands and troubleshooting]
3. Select workspace...
   [10 lines about workspace selection]
...
[45 more pages of similar content]
```

New engineers faced:

- 2-3 days to read and understand the guide
- Instructions that were outdated
- No confidence about what commands to run
- Different engineers following different procedures

### The New Way: Discovery Through Make

After implementing discovery patterns:

```bash
# Day 1, Hour 1
$ make help
Infrastructure Commands
======================
  setup-backend        - One-time backend initialization
  init                 - Initialize for ENVIRONMENT
  plan                 - Create deployment plan
  ...

Set ENVIRONMENT=dev|staging|prod to see environment-specific commands

# They discover what they need to set
$ make help ENVIRONMENT=staging
Staging Environment
===================
  make plan            - Create deployment plan
  make apply           - Apply changes (requires review)
  ...

Current: ENVIRONMENT=staging REGION=us-west-2

# They follow the discovery path
$ make plan ENVIRONMENT=staging
Pre-flight checks for staging...
AWS credentials valid
Terraform version correct
Configuration file found

Creating plan for staging...
[terraform output]

Review plan above. To apply:
  make apply ENVIRONMENT=staging
```

Results after migration:

- Onboarding time: 2-3 days → 2-3 hours
- Wiki reduced from 50 pages to: "Run `make help`"
- Zero deployments to wrong environment
- Consistent procedures across all engineers
- Junior engineers deploying infrastructure safely within first week

The key insight: **discovery replaces documentation**. Instead of maintaining
prose that describes what to do, create targets that reveal the workflow as
engineers interact with it.

## Key Takeaways

Infrastructure provisioning workflows become discoverable through Make by:

1. **Progressive disclosure**: Simple interfaces that reveal complexity as needed
2. **Self-documenting help**: Context-aware help that shows relevant commands
3. **Clear prerequisites**: Targets that communicate what's needed before running
4. **Safe defaults**: Protection built into the workflow itself
5. **Examples built in**: The Makefile teaches the workflow through use

The pattern is consistent: start with `make help`, follow the breadcrumbs, get
clear feedback at each step. The workflow reveals itself through interaction
rather than requiring upfront documentation study.

This discovery-based approach works because it aligns with how engineers
actually work: trying things, reading error messages, following suggestions.
Instead of fighting this pattern with static documentation, Make embraces it by
making the documentation executable and responsive.

In the next chapter, we'll extend these patterns to infrastructure
reliability—how Make can orchestrate testing, disaster recovery, and operational
maintenance workflows that keep your infrastructure healthy.