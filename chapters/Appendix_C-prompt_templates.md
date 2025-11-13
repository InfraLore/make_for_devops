# Appendix C: LLM Prompt Templates for Makefile Development

This appendix provides prompt templates for working with AI coding assistants to create or improve Makefiles. These prompts encode the core principles from this book: discoverability, executable documentation, progressive disclosure, and reducing cognitive load.

## How to Use These Prompts

1. **Copy the entire prompt** including the principles section
2. **Customize the specifics** for your project (replace [PROJECT TYPE], [LANGUAGES], etc.)
3. **Review the output carefully** - Always run `make -n <target>` to verify before executing
4. **Iterate if needed** - Use follow-up prompts to refine the result
5. **Test thoroughly** - AI-generated Makefiles should be tested just like any code

Remember: You're responsible for the final Makefile. AI generates, you validate and approve.

---

## Prompt 1: Creating a New Makefile from Scratch

```
I need help creating a Makefile for my project. Follow these core principles:

DISCOVERABILITY PRINCIPLES:

- Set .DEFAULT_GOAL := help so running plain "make" shows available commands
- Every target should have a ## comment explaining what it does
- The help target should parse and display these comments
- Group related targets and show them in logical sections
- Each target should suggest relevant next steps after completing

PROGRESSIVE DISCLOSURE:

- Start with simple, common tasks (dev, test, build, deploy)
- More complex operations should be discoverable but not overwhelming
- Use underscore prefix for internal targets (_internal-task)
- Provide menu targets that show related operations (make docker shows Docker commands)

EXECUTABLE DOCUMENTATION:

- The Makefile is both documentation and implementation
- Targets should be self-explanatory from their names
- Complex logic should live in scripts, Makefile provides interface
- Include usage examples in comments

SAFETY AND VALIDATION:

- Validate prerequisites before dangerous operations
- Use .PHONY for all non-file targets
- Include dry-run capabilities where appropriate
- Build validation into workflows (deploy depends on test)

PROJECT DETAILS:

- Project type: [web application / CLI tool / library / microservice / etc.]
- Languages: [Python / Go / Node.js / etc.]
- Key tools: [Docker / Kubernetes / Terraform / etc.]
- Environments: [dev / staging / production]
- Team size: [solo / small team / large organization]

COMMON WORKFLOWS NEEDED:

- Development environment setup
- Running tests
- Building artifacts
- Deployment to different environments
- [Add any specific workflows]

CONSTRAINTS:

- Assume all engineers run on [macOS / Linux / Windows with WSL]
- Never use localStorage or sessionStorage (this is Make, not a browser)
- Keep it simple - only add complexity that solves real problems
- Extract complex operations to scripts in ./scripts/

Generate a Makefile that embodies these principles. Include:

1. A comprehensive help target
2. Common workflow targets (dev, test, build)
3. Appropriate validation
4. Clear organization with comments
5. Guidance for next steps

After generating, explain key design decisions you made.
```

---

## Prompt 2: Improving an Existing Makefile

```
I have an existing Makefile that needs improvement based on these principles:

CURRENT MAKEFILE:
[Paste your existing Makefile here]

IMPROVEMENT GOALS:
☐ Add discoverability (help target, ## comments)
☐ Improve organization and readability
☐ Add validation and safety checks
☐ Extract complex logic to scripts
☐ Add progressive disclosure
☐ Standardize naming conventions
☐ Add .PHONY declarations
☐ [Other specific goals]

CORE PRINCIPLES TO APPLY:

1. DISCOVERABILITY
   - Add .DEFAULT_GOAL := help
   - Add ## comments to all public targets
   - Create a help target that parses and displays comments
   - Group related operations

2. PROGRESSIVE DISCLOSURE
   - Common tasks should be simple (make dev, make test)
   - Complex operations should be available but not prominent
   - Use underscore prefix for internal targets
   - Provide menu targets for related operations

3. SAFETY
   - Validate prerequisites before destructive operations
   - Add .PHONY for non-file targets
   - Build dependencies between targets (deploy depends on test)

4. MAINTAINABILITY
   - Extract complex shell logic to scripts in ./scripts/
   - Use consistent variable naming
   - Add comments explaining non-obvious decisions
   - Keep the Makefile focused on orchestration

SPECIFIC ISSUES TO ADDRESS:
[List any specific problems: unclear target names, missing documentation,
repetitive code, unsafe operations, etc.]

CONSTRAINTS:

- Maintain backward compatibility where possible
- Preserve existing target names if they're already in use
- Don't break existing CI/CD pipelines
- Keep changes incremental - don't rewrite everything at once

Generate an improved version of this Makefile. Highlight:

1. What you changed and why
2. Any backward compatibility concerns
3. Suggested follow-up improvements
4. How to test the changes safely
```

---

## Prompt 3: Adding Multi-Environment Support

```
I need to add multi-environment support to my Makefile following these patterns:

CURRENT SITUATION:

- Environments: [development, staging, production]
- Current approach: [describe current approach or "none - everything hardcoded"]
- Pain points: [duplication, environment-specific logic scattered, etc.]

DESIRED PATTERN (choose one):

OPTION A: Pattern Rules (for similar environments)
When environments are mostly identical:
```makefile
deploy-%: validate-% ## Deploy to specified environment
	@echo "Deploying to $*..."
	@./scripts/deploy.sh $* 

validate-dev:
	@./scripts/validate-basic.sh

validate-production: validate-dev
	@./scripts/validate-production.sh
	@./scripts/security-audit.sh
```

OPTION B: Conditionals (for different environments)
When environments need different logic:

```makefile
ENVIRONMENT ?= development

ifeq ($(ENVIRONMENT),production)
  REPLICAS = 3
  REGISTRY = prod-registry.company.com
else ifeq ($(ENVIRONMENT),staging)
  REPLICAS = 2
  REGISTRY = staging-registry.company.com
else
  REPLICAS = 1
  REGISTRY = localhost:5000
endif
```

OPTION C: Config Files (for many variables)
When you have 10+ variables per environment:

```makefile
-include config/$(ENVIRONMENT).mk

show-config:
	@echo "Environment: $(ENVIRONMENT)"
	@echo "Registry: $(REGISTRY)"
	@echo "Replicas: $(REPLICAS)"
```

REQUIREMENTS:

- Default to development environment
- Make environment overridable: ENVIRONMENT=staging make deploy
- Validate environment names
- Production should require extra validation
- Show current configuration clearly

PROJECT SPECIFICS:

- Build tool: [Docker / native / etc.]
- Deployment target: [Kubernetes / AWS / Heroku / etc.]
- Environment-specific values: [list key differences]

Generate Makefile code that implements multi-environment support.
Include:
1. Clear environment detection
2. Appropriate validation for each environment
3. Way to show current configuration
4. Usage examples
5. Explanation of which pattern you chose and why

---

## Prompt 4: Adding Docker Workflow Support

```

I need to add Docker workflows to my Makefile following these principles:

DOCKER ORCHESTRATION CONTEXT:

- Currently using: [Docker Compose / Dockerfile only / Lando / etc.]
- Services: [database, cache, app, etc.]
- Environments: [dev, test, production]

KEY PRINCIPLE: Make doesn't replace Docker tools, it provides the discoverable
interface to them. Make should:

- Show what Docker operations are available (make docker or make help)
- Coordinate pre/post Docker operations
- Handle environment-specific differences
- Make complex Docker commands simple and memorable

COMMON PATTERNS NEEDED:

1. DEVELOPMENT ENVIRONMENT

```makefile
dev: ## Start development environment
	@if [ ! -f .env ]; then cp .env.example .env; fi
	@docker-compose up -d
	@$(MAKE) _wait-for-services
	@$(MAKE) migrate
	@echo "✓ Ready at http://localhost:8000"
```

2. MULTI-STAGE BUILDS

```makefile
build-dev: ## Build development image
	docker build --target development -t $(APP_NAME):dev .

build-prod: ## Build production image
	docker build --target production -t $(APP_NAME):$(VERSION) .
```

3. REGISTRY OPERATIONS

```makefile
push: build-prod login ## Push to registry
	docker tag $(APP_NAME):$(VERSION) $(REGISTRY)/$(APP_NAME):$(VERSION)
	docker push $(REGISTRY)/$(APP_NAME):$(VERSION)
```

PROJECT DETAILS:

- Application: [type and language]
- Dockerfile stages: [development, test, production, etc.]
- Registry: [Docker Hub / private / etc.]
- Testing approach: [in container / on host / etc.]

REQUIRED WORKFLOWS:

- Start development environment
- Run tests in container
- Build production image
- Push to registry
- Security scanning
- [Other specific needs]

Generate Makefile code for Docker workflows. Include:
1. Clear help/menu target
2. Development environment setup
3. Build workflows for different stages
4. Testing in containers
5. Registry operations with proper tagging
6. Guidance on what commands to use when
```

---

## Prompt 5: Adding CI/CD Pipeline Support

```
I need CI/CD pipeline support in my Makefile following these principles:

CI/CD PHILOSOPHY:

- Same commands should work locally and in CI
- CI should just be "make ci" - everything else is implementation
- Local engineers should be able to run CI steps individually
- No surprises in CI that can't be reproduced locally

CURRENT CI SETUP:

- Platform: [GitHub Actions / GitLab CI / Jenkins / etc.]
- Current approach: [describe or "starting fresh"]
- Pain points: [different commands locally vs CI, hard to debug, etc.]

DESIRED PATTERN:

```makefile
ci: ## Run full CI pipeline
	@echo "Running CI pipeline..."
	@$(MAKE) ci-validate
	@$(MAKE) ci-test
	@$(MAKE) ci-build
	@$(MAKE) ci-security
	@echo "✓ CI pipeline passed"

ci-validate: ## CI: Validate code quality
	@./scripts/ci-validate.sh

ci-test: ## CI: Run test suite
	@./scripts/ci-test.sh

ci-build: ## CI: Build artifacts
	@./scripts/ci-build.sh

ci-security: ## CI: Security scanning
	@./scripts/ci-security.sh
```

PIPELINE STAGES NEEDED:

- Linting / code quality checks
- Unit tests
- Integration tests
- Build artifacts
- Security scanning
- Deployment (if applicable)
- [Other stages]

PROJECT SPECIFICS:

- Languages: [list]
- Test frameworks: [list]
- Build tools: [list]
- Deployment targets: [list]
- Security tools: [list if any]

REQUIREMENTS:

- Each stage should be independently runnable
- Full pipeline should be one command: make ci
- Should work identically locally and in CI
- Fast feedback - fail fast on errors
- Clear output showing what's happening

Generate Makefile code for CI/CD. Include:

1. Individual targets for each pipeline stage
2. Combined ci target that runs everything
3. Validation and error handling
4. Clear progress output
5. Usage examples for local and CI contexts
```

---

## Prompt 6: Converting Repetitive Targets to Pattern Rules

```
I have repetitive targets in my Makefile that should use pattern rules.

CURRENT REPETITIVE TARGETS:
[Paste the repetitive targets here]

PATTERN RULE PRINCIPLES:

- Use when you have 3+ similar targets that differ only in one parameter
- The % matches any string, $* contains the matched portion
- Pattern rules can have prerequisites: deploy-%: validate-%
- Keep it simple - if exceptions complicate the pattern, use explicit targets

EXAMPLE CONVERSION:

Before (repetitive):

```makefile
deploy-dev:
	@./scripts/deploy.sh dev

deploy-staging:
	@./scripts/deploy.sh staging

deploy-prod:
	@./scripts/deploy.sh prod
```

After (pattern rule):

```makefile
deploy-%: validate-% ## Deploy to specified environment
	@echo "Deploying to $*..."
	@./scripts/deploy.sh $*

# Environment-specific validation
validate-dev:
	@./scripts/validate-basic.sh

validate-prod: validate-dev
	@./scripts/validate-production.sh
```

REQUIREMENTS:

- Convert repetitive targets to pattern rules where appropriate
- Keep exceptions as explicit targets (don't force everything into patterns)
- Maintain or improve discoverability
- Add validation appropriate to each use case
- Include usage examples

QUESTIONS TO CONSIDER:

- Are the targets truly identical except for one parameter?
- Do any environments need special handling?
- Would pattern rules make the Makefile clearer or more confusing?
- Can new engineers still understand what's happening?

Generate improved Makefile code using pattern rules. Explain:

1. Which targets you converted and why
2. Which targets you left explicit and why
3. How to use the new pattern rules
4. Any trade-offs made
```

---

## Prompt 7: Adding Functions for Repetitive Command Sequences

```
I have repetitive command sequences that should use Make functions.

FUNCTION PRINCIPLES FROM THE BOOK:

- Use functions when multi-line command sequences repeat across 3+ targets
- Functions accept parameters via $(1), $(2), etc.
- Invoke with $(call function_name,arg1,arg2)
- Don't overuse - single-line commands should use variables instead
- Functions add indirection - only use when duplication pain exceeds learning curve

EXAMPLE PATTERN:

Before (repetitive):
```makefile
deploy-api:
	@echo "Deploying API..."
	@./scripts/health-check.sh || exit 1
	@./scripts/deploy.sh api
	@./scripts/verify.sh api

deploy-worker:
	@echo "Deploying worker..."
	@./scripts/health-check.sh || exit 1
	@./scripts/deploy.sh worker
	@./scripts/verify.sh worker
```

After (with function):
```makefile
define safe_deploy
	@echo "Deploying $(1)..."
	@./scripts/health-check.sh || exit 1
	@./scripts/deploy.sh $(1)
	@./scripts/verify.sh $(1)
endef

deploy-api:
	$(call safe_deploy,api)

deploy-worker:
	$(call safe_deploy,worker)
```

CURRENT REPETITIVE SEQUENCES:
[Paste the repetitive command sequences here]

REQUIREMENTS:

- Convert repetitive multi-line sequences to functions
- Keep single-line commands as variables
- Maintain readability - targets should still be understandable
- Add comments explaining what functions do
- Consider if functions are actually simpler than inline code

QUESTIONS TO CONSIDER:

- Does this sequence repeat 3+ times?
- Is it truly identical each time?
- Would a function make this clearer or more obscure?
- Can someone unfamiliar with Make functions understand this?

Generate improved Makefile code using functions where appropriate. Explain:

1. Which sequences you converted to functions and why
2. What you left inline and why
3. How to use the new functions
4. When to add more functions vs when to stop
```

---

## Prompt 8: Adding Secret Management

```
I need to add secret management to my Makefile following security best practices.

SECURITY PRINCIPLES:

- NEVER put secrets in Makefiles or config files
- NEVER commit secrets to version control
- Secrets come from environment variables or secure stores
- Validate secrets exist before using them
- Never expose secrets in logs or output

PATTERN FOR ENVIRONMENT VARIABLE SECRETS:

```makefile
check-secrets: ## Verify required secrets are set
	@test -n "$$DATABASE_PASSWORD" || \
		(echo "ERROR: Set DATABASE_PASSWORD environment variable" && exit 1)
	@test -n "$$API_KEY" || \
		(echo "ERROR: Set API_KEY environment variable" && exit 1)
	@echo "✓ Required secrets are set"

# Use secrets without exposing them
deploy: check-secrets
	@echo "Deploying with secrets..."
	@# Note: Use $$VAR (double $) to pass to shell, not $(VAR)
	@kubectl create secret generic app-secrets \
		--from-literal=db-password="$$DATABASE_PASSWORD" \
		--from-literal=api-key="$$API_KEY" \
		--dry-run=client -o yaml | kubectl apply -f -
```

OPTIONAL: Development .env file (never committed):
```makefile
ifneq ($(ENVIRONMENT),production)
  -include .env
  export
endif

setup-dev-env: ## Create .env template for development
	@if [ ! -f .env ]; then \
		echo "DATABASE_PASSWORD=dev_password" > .env; \
		echo "API_KEY=dev_key" >> .env; \
		echo "Created .env - edit with your dev values"; \
		echo "Remember: .env is in .gitignore, never commit it"; \
	fi
```

PROJECT DETAILS:

- Required secrets: [list them]
- Environment: [local dev / staging / production]
- Secret store if any: [AWS Secrets Manager / Vault / etc.]
- Deployment target: [Kubernetes / AWS / etc.]

REQUIREMENTS:

- Validate all required secrets before critical operations
- Never expose secret values in output
- Provide clear error messages when secrets are missing
- Support local development secrets (.env file pattern)
- Document where secrets should be set

Generate Makefile code for secret management. Include:

1. Secret validation targets
2. Clear documentation of required secrets
3. Development environment setup if applicable
4. Integration with deployment workflows
5. Security best practices followed
```

---

## Prompt 9: Making an Existing Makefile More Discoverable

```
I have a working Makefile but new team members can't figure out how to use it.

CURRENT MAKEFILE:
[Paste your Makefile here]

DISCOVERABILITY PROBLEMS:

- No help target - running "make" gives an error or does something unexpected
- Targets have unclear names or no documentation
- No guidance on what to do first or next
- Complex targets with no explanation
- [Other specific issues]

DISCOVERABILITY PRINCIPLES TO APPLY:

1. DEFAULT GOAL
```makefile
.DEFAULT_GOAL := help
```
Running plain "make" should show help, not error or do something unexpected.

2. HELP TARGET
```makefile
help: ## Show available commands
	@echo "Common tasks:"
	@echo "  make dev     Start development"
	@echo "  make test    Run tests"
	@echo "  make deploy  Deploy to staging"
	@echo ""
	@echo "All commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
```

3. TARGET DOCUMENTATION
Every public target should have a ## comment:
```makefile
dev: ## Start development environment
	@./scripts/start-dev.sh

test: ## Run test suite
	@./scripts/run-tests.sh
```

4. PROGRESSIVE DISCLOSURE
Common tasks should be simple, complex tasks available but not overwhelming:
```makefile
# Simple entry point
dev: ## Start development
	@$(MAKE) _setup-dev
	@$(MAKE) _start-services
	@echo "Ready at http://localhost:8000"
	@echo "Next steps: make test, make logs"

# Complex tasks use underscore prefix
_setup-dev:
	@./scripts/setup-dev.sh

_start-services:
	@docker-compose up -d
```

5. MENU TARGETS
Group related operations:
```makefile
docker: ## Show Docker commands
	@echo "Docker commands:"
	@echo "  make docker-build   Build images"
	@echo "  make docker-push    Push to registry"
	@echo "  make docker-clean   Clean up images"
```

REQUIREMENTS:

- Add comprehensive help target
- Add ## comments to all public targets
- Set .DEFAULT_GOAL := help
- Group related operations with menu targets
- Add guidance for next steps
- Use underscore prefix for internal targets
- Keep existing functionality - don't break things

Generate an improved version focused on discoverability. Explain:

1. What you changed and why
2. How new engineers should start using it
3. How to gradually adopt changes without breaking existing usage
```

---

## Follow-Up Prompts

After getting initial results, use these follow-up prompts to refine:

### For More Safety
```
Add more validation to this Makefile:

- Check prerequisites before running (required tools installed)
- Validate environment names
- Require confirmation for destructive operations
- Add dry-run capabilities where appropriate
```

### For Better Organization
```
Improve the organization of this Makefile:

- Group related targets with comment headers
- Order targets logically (common tasks first)
- Extract complex logic to scripts
- Add more .PHONY declarations
```

### For Better Testing
```
Make this Makefile more testable:

- Add targets that show what would happen without doing it
- Add validation-only targets
- Make it easier to test individual components
- Add targets for running in CI
```

---

## General Guidelines for All Prompts

When working with AI on Makefiles:

1. **Always include the core principles** - AI needs context about discoverability, progressive disclosure, etc.

2. **Provide examples of good patterns** - Show the AI what "good" looks like

3. **Specify constraints clearly** - Team size, tools used, deployment targets, etc.

4. **Request explanations** - Ask AI to explain design decisions

5. **Test thoroughly** - Always use `make -n <target>` before running for real

6. **Iterate incrementally** - Don't try to perfect everything at once

7. **Maintain human oversight** - You're responsible for reviewing and approving

8. **Consider your team** - What works for a solo developer might not work for a large team

Remember: These prompts encode best practices from this book, but AI is a tool, not a replacement for understanding. Use AI to accelerate your work, but maintain accountability for the results.
