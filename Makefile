####################################################################################################
# Configuration
####################################################################################################

# Build configuration

BUILD = build
MAKEFILE = Makefile
OUTPUT_FILENAME = MakeForDevops
METADATA = metadata.yml
TMP_METADATA = $(BUILD)/tmp-metadata.yml

# Line length limits for code blocks
OVERFLOW_LIMIT ?= 87
LONG_LINE_LIMIT ?= 95


# Chapters content organized by parts
PART_1 = parts/part-1.md chapters/01-why_make.md chapters/02-executable_readme.md chapters/03-make_fundamentals.md
PART_2 = parts/part-2.md chapters/04-testing_and_validating.md chapters/05-variables_and_configuration.md chapters/06-phony_targets_and_task_organization.md chapters/07-dependency_management.md chapters/08-advanced_make.md
PART_3 = parts/part-3.md chapters/09-make_and_docker.md chapters/10-make_and_kubernetes.md chapters/11-make_and_ci_cd.md chapters/12-make_in_the_ci_cd_ecosystem.md
PART_4 = parts/part-4.md chapters/13-make_for_infrastructure_provisioning.md chapters/14-make_for_infrastructure_reliability.md chapters/15-make_for_monitoring_and_metrics.md chapters/16-make_for_logging_and_incident_response.md chapters/17-security_and_compliance_workflows.md
PART_5 = parts/part-5.md chapters/18-scaling_make_across_teams_and_projects.md chapters/19-troubleshooting_and_debugging_make_workflows.md chapters/20-the_future_of_make_in_devops.md chapters/21-make_as_your_personal_learning_tool.md

APPENDICES = chapters/Appendix_A-quick_referrence_guide.md chapters/Appendix_B-migration_strategies.md chapters/Appendix_C-prompt_templates.md

CHAPTERS = $(PART_1) $(PART_2) $(PART_3) $(PART_4) $(PART_5) $(APPENDICES)

TOC = --toc --toc-depth 2
METADATA_ARGS = --metadata-file $(METADATA) --metadata-file $(TMP_METADATA)
IMAGES = $(shell find images -type f)
TEMPLATES = $(shell find templates/ -type f)
COVER_IMAGE = images/cover.png
MATH_FORMULAS = --webtex

# Chapters content
CONTENT = awk 'FNR==1 && NR!=1 {print "\n\n"}{print}' $(CHAPTERS)
CONTENT_FILTERS = tee # Use this to add sed filters or other piped commands

# Debugging

# DEBUG_ARGS = --verbose

# Pandoc filters - uncomment the following variable to enable cross references filter. For more
# information, check the "Cross references" section on the README.md file.

# FILTER_ARGS = --filter pandoc-crossref

# use the codeblock-border.lua filter to add borders to code blocks
FILTER_ARGS = --lua-filter=codeblock-border.lua

# Combined arguments

ARGS = $(TOC) $(MATH_FORMULAS) $(METADATA_ARGS) $(FILTER_ARGS) $(DEBUG_ARGS)
	
PANDOC_COMMAND = pandoc

# Per-format options

DOCX_ARGS = --standalone --reference-doc templates/docx.docx
EPUB_ARGS = --template templates/epub.html --epub-cover-image $(COVER_IMAGE)
HTML_ARGS = --template templates/html.html --standalone --to html5
PDF_ARGS = --template templates/pdf.latex --pdf-engine xelatex --no-highlight --quiet

# Per-format file dependencies

BASE_DEPENDENCIES = $(MAKEFILE) $(CHAPTERS) $(METADATA) $(IMAGES) $(TEMPLATES)
DOCX_DEPENDENCIES = $(BASE_DEPENDENCIES)
EPUB_DEPENDENCIES = $(BASE_DEPENDENCIES)
HTML_DEPENDENCIES = $(BASE_DEPENDENCIES)
PDF_DEPENDENCIES = $(BASE_DEPENDENCIES)

# Detected Operating System

OS = $(shell sh -c 'uname -s 2>/dev/null || echo Unknown')

# OS specific commands

ifeq ($(OS),Darwin) # Mac OS X
	COPY_CMD = cp -P
else # Linux
	COPY_CMD = cp --parent
endif

MKDIR_CMD = mkdir -p
RMDIR_CMD = rm -r
ECHO_BUILDING = @echo "building $@..."
ECHO_BUILT = @echo "$@ was built\n"

# Progress bar function - shows countdown blocks that disappear over time
define PROGRESS_BAR
	@printf "$(1): ▓▓▓▓▓▓"
	@($(2)) & \
	PID=$$!; \
	blocks="▓▓▓▓▓▓"; \
	while ps $$PID > /dev/null 2>&1; do \
		printf "\r"; \
		printf "$(1): $$blocks"; \
		if [ "$${#blocks}" -gt 0 ]; then \
			blocks="$${blocks%▓}"; \
		fi; \
		sleep 3; \
	done; \
	printf "\r$(1): ✓          \n"
endef

####################################################################################################
# Basic actions
####################################################################################################

.PHONY: all book clean epub html pdf docx

all:	book

book:	epub html pdf docx

clean:
	@if [ -d "$(BUILD)" ]; then \
		echo "Removing $(BUILD) directory..."; \
		$(RMDIR_CMD) $(BUILD); \
	else \
		echo "$(BUILD) directory already clean."; \
	fi

####################################################################################################
# Utilities
####################################################################################################

validate:
	@echo "Validating chapter contents..."
	@result=$$(grep -Ein '\btribal\b' $(CHAPTERS)); \
	if [ -n "$$result" ]; then \
		echo ""; \
		echo "ERROR: Forbidden word \"tribal\" found in chapters:"; \
		echo "$$result"; \
		echo ""; \
		exit 1; \
	else \
		echo "Validation passed."; \
	fi

check-overflow:
	@echo "Checking for potentially overflowing code lines..."
	@echo "Lines longer than $(OVERFLOW_LIMIT) characters in code blocks:"
	@echo "================================================"
	@for file in $(CHAPTERS); do \
		if [ -f "$$file" ]; then \
			awk -v limit=$(OVERFLOW_LIMIT) '/^```/ { in_code = !in_code; next } \
			     in_code && length($$0) > limit { \
			       print FILENAME ":" NR ":" length($$0) " chars: " substr($$0, 1, 60) "..." \
			     }' "$$file"; \
		fi; \
	done

check-long-lines:
	@echo "Checking for very long lines ($(LONG_LINE_LIMIT)+ chars) in code blocks..."
	@echo "=========================================================="
	@for file in $(CHAPTERS); do \
		if [ -f "$$file" ]; then \
			awk -v limit=$(LONG_LINE_LIMIT) '/^```/ { in_code = !in_code; next } \
			     in_code && length($$0) > limit { \
			       print FILENAME ":" NR ":" length($$0) " chars: " substr($$0, 1, 40) "..." \
			     }' "$$file"; \
		fi; \
	done

####################################################################################################
# File builders
####################################################################################################

$(TMP_METADATA): 
	$(MKDIR_CMD) $(BUILD)
	echo "git_sha: $(shell git rev-parse --short HEAD)" > $(TMP_METADATA)
	echo "git_url: $(shell git config --get remote.origin.url | \
		sed -E 's#git@([^:]+):#\1/#; s#\.git$$##')" >> $(TMP_METADATA)
	echo "git_date: $(shell git log -1 --format=%cd --date=short)" >> $(TMP_METADATA)

epub:	validate $(BUILD)/epub/$(OUTPUT_FILENAME).epub

html:	validate $(BUILD)/html/$(OUTPUT_FILENAME).html

pdf:	validate $(BUILD)/pdf/$(OUTPUT_FILENAME).pdf

docx:	validate $(BUILD)/docx/$(OUTPUT_FILENAME).docx

$(BUILD)/epub/$(OUTPUT_FILENAME).epub:	$(EPUB_DEPENDENCIES) $(TMP_METADATA)
	$(ECHO_BUILDING)
	$(MKDIR_CMD) $(BUILD)/epub
	$(CONTENT) | $(CONTENT_FILTERS) | $(PANDOC_COMMAND) $(ARGS) $(EPUB_ARGS) -o $@
	$(ECHO_BUILT)

$(BUILD)/html/$(OUTPUT_FILENAME).html:	$(HTML_DEPENDENCIES) $(TMP_METADATA)
	$(ECHO_BUILDING)
	$(MKDIR_CMD) $(BUILD)/html
	$(CONTENT) | $(CONTENT_FILTERS) | $(PANDOC_COMMAND) $(ARGS) $(HTML_ARGS) -o $@
	$(COPY_CMD) $(IMAGES) $(BUILD)/html/
	$(ECHO_BUILT)

$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf:	$(PDF_DEPENDENCIES) $(TMP_METADATA)
	$(ECHO_BUILDING)
	$(MKDIR_CMD) $(BUILD)/pdf
	$(call PROGRESS_BAR,Generating PDF (about 24 seconds),$(CONTENT) | $(CONTENT_FILTERS) | $(PANDOC_COMMAND) $(ARGS) $(PDF_ARGS) -o $@)
	$(ECHO_BUILT)

$(BUILD)/docx/$(OUTPUT_FILENAME).docx:	$(DOCX_DEPENDENCIES)
	$(ECHO_BUILDING)
	$(MKDIR_CMD) $(BUILD)/docx
	$(CONTENT) | $(CONTENT_FILTERS) | $(PANDOC_COMMAND) $(ARGS) $(DOCX_ARGS) -o $@
	$(ECHO_BUILT)
