---
title: "Make Cheat Sheet"
mainfont: Merriweather 24pt
monofont: JetBrainsMono Nerd Font Mono
headingfont: Lato-Regular
---

# Basics
```makefile
target: prerequisites
	command  # MUST be TAB
```

## Variables
```makefile
VAR := immediate    # Simple expansion
VAR = deferred      # Recursive
VAR ?= default      # Conditional
VAR += append       # Append
$(VAR) ${VAR}       # Expand
$$VAR               # Shell var (literal $)
```

## Automatic Variables
```makefile
$@  # Target name
$<  # First prerequisite
$^  # All prerequisites
$?  # Newer prerequisites
$*  # Pattern stem
```

## Phony Targets
```makefile
.PHONY: clean test deploy
clean:
	rm -rf build/
```

## Functions

```makefile
# Pattern substitution
$(patsubst %.c,%.o,$(SRC))
# Shell command
$(shell git rev-parse HEAD)
# Conditional
$(if $(DEBUG),-g,)
# Filter
$(filter %.go,$(FILES))
# Directory/basename
$(dir src/main.c)
$(notdir src/main.c)
```

## Conditionals

```makefile
ifeq ($(ENV),prod)
  REPLICAS := 10
else
  REPLICAS := 2
endif

ifdef DEBUG
  CFLAGS += -g
endif
```

# Self-Documenting Help

## Basic Help
```makefile
.DEFAULT_GOAL := help

help: ## Show help
	@awk 'BEGIN {FS = ":.*##"} \
	/^[a-zA-Z_-]+:.*?##/ { \
	  printf "  \033[36m%-15s\033[0m %s\n", \
	  $$1, $$2 \
	}' $(MAKEFILE_LIST)

setup: ## Set up project
	npm install
```

## Categorized Help
```makefile
help: ## Show commands
	@awk 'BEGIN {FS = ":.*##"} \
	/^[a-zA-Z_-]+:.*?##/ { \
	  printf "  \033[36m%-15s\033[0m %s\n", \
	  $$1, $$2 \
	} \
	/^##@/ { \
	  printf "\n\033[1m%s\033[0m\n", \
	  substr($$0, 5) \
	}' $(MAKEFILE_LIST)

##@ Development
dev: ## Start dev server
	npm run dev

##@ Deployment
deploy: ## Deploy to prod
	./deploy.sh
```

# Common Patterns

## Validation
```makefile
_check-docker:
	@command -v docker >/dev/null || \
	  (echo "docker required" && exit 1)

_check-version:
	@test -n "$(VERSION)" || \
	  (echo "VERSION not set" && exit 1)

deploy: _check-docker _check-version
	docker push $(IMAGE):$(VERSION)
```

## Confirmation
```makefile
deploy-prod:
	@echo "Deploy to PRODUCTION?"
	@echo -n "Type 'yes': " && read ans && \
	  [ "$$ans" = "yes" ]
	@$(MAKE) _deploy ENV=prod
```

## Multi-line Commands
```makefile
# Backslash continuation
build:
	docker build \
	  -t $(IMAGE) \
	  --build-arg V=$(VERSION) \
	  .

# Same shell (semicolons)
deploy:
	cd app && \
	npm install && \
	npm run build

# Suppress output
quiet:
	@echo "Visible"
	@npm install --silent
```

## Error Handling
```makefile
# Ignore errors (-)
clean:
	-rm -rf build/

# Continue with || true
optional:
	./might-fail.sh || true

# Custom error message
deploy:
	@./deploy.sh || \
	  (echo "Failed. Check: make logs" \
	   && exit 1)
```

## Environment Detection
```makefile
UNAME := $(shell uname -s)
ifeq ($(UNAME),Linux)
  PLATFORM := linux
endif
ifeq ($(UNAME),Darwin)
  PLATFORM := macos
endif

ifdef CI
  FLAGS := --no-cache
endif
```

## Pattern Rules
```makefile
%.html: %.md
	markdown $< > $@

%.o: %.c
	gcc -c $< -o $@
```

## Dynamic Targets
```makefile
SERVICES := api worker frontend
DEPLOY := $(addprefix deploy-,$(SERVICES))

$(DEPLOY): deploy-%:
	kubectl apply -f k8s/$*/

deploy-all: $(DEPLOY)
```

## Includes
```makefile
include common.mk
include config/*.mk
-include optional.mk  # No error if missing
```

# Debugging

## Dry Run
```bash
make -n target
make -n deploy VERSION=1.2.3
```

## Debug Output
```makefile
debug-vars:
	$(info VERSION=$(VERSION))
	$(info IMAGE=$(IMAGE))
	@:
```

## Verbose Mode
```makefile
VERBOSE ?= 0
ifeq ($(VERBOSE),1)
  Q :=
else
  Q := @
endif

build:
	$(Q)docker build -t $(IMAGE) .
# Run: make build VERBOSE=1
```

## Trace Commands
```bash
make --debug=v target  # Verbose
make --debug=b target  # Basic
make -p                # Print database
```

# Command-Line Usage

```bash
# Basic
make target
make clean build test

# With variables
make deploy VERSION=1.2.3 ENV=prod

# Flags
make -n deploy         # Dry run
make -i test           # Ignore errors
make -k test           # Keep going
make -j4 test          # Parallel (4 jobs)
make -C subdir target  # Change dir
make -f Custom.mk      # Different file

# Environment
ENVIRONMENT=prod make deploy
export ENV=prod; make deploy
```

# Common Errors

**"missing separator"**
→ Use TAB, not spaces

**"No rule to make target"**
→ Check spelling/dependencies

**Variables not expanding**
```makefile
# Wrong
deploy:
	VERSION=1.2.3
	echo $(VERSION)  # Empty!

# Right
VERSION := 1.2.3
deploy:
	echo $(VERSION)
# Or: VERSION=1.2.3; echo $$VERSION
```

**Target not running**
→ Add `.PHONY`:
```makefile
.PHONY: test
test:
	pytest
```

**Circular dependency**
```makefile
# Wrong
a: b
b: a

# Check with: make -p
```
# Best Practices

- Use `.DEFAULT_GOAL := help`
- Mark non-file targets as `.PHONY`
- Use `##` for self-documenting help
- Prefix internal targets with `_`
- Validate prerequisites before executing
- Confirm destructive operations
- Use `:=` for immediate, `?=` for defaults
- Suppress output with `@` unless debugging
- Test with `make -n` first
- Keep lines under 75 characters
- Version control your Makefile
