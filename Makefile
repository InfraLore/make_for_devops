####################################################################################################
# Configuration
####################################################################################################

.DEFAULT_GOAL := help

# Improve Error Handling
.ONESHELL:
ifdef DEBUG
.SHELLFLAGS := -eux -o pipefail -c
else
.SHELLFLAGS := -eu -o pipefail -c
endif

# catch errors in pipe chains
SHELL := /bin/bash

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

APPENDICES = chapters/Appendix_A-quick_reference_guide.md chapters/Appendix_B-migration_strategies.md chapters/Appendix_C-prompt_templates.md

CHAPTERS = $(PART_1) $(PART_2) $(PART_3) $(PART_4) $(PART_5) $(APPENDICES)

TOC = --toc --toc-depth 2
METADATA_ARGS = --metadata-file $(METADATA) --metadata-file $(TMP_METADATA)
IMAGES = $(shell find images -type f)
TEMPLATES = $(shell find templates/ -type f)

# Mermaid diagram files
MMD_FILES = $(shell find images -name "*.mmd" -type f)
PNG_FILES = $(MMD_FILES:.mmd=.png)
COVER_IMAGE = images/cover.png
MATH_FORMULAS = --webtex

# Chapters content
CONTENT = awk 'FNR==1 && NR!=1 {print "\n\n"}{print}' $(CHAPTERS)
CONTENT_FILTERS = tee # Use this to add sed filters or other piped commands

# Path to publish (can be overridden)
PUBLISH_PATH ?= /Users/hpottinger/Library/Mobile Documents/com~apple~CloudDocs

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
ECHO_BUILT = @echo "$@ was built" & echo

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
	printf "\r$(1): ✅          \n"
endef

####################################################################################################
# Basic actions
####################################################################################################

.PHONY: all book clean epub html pdf docx validate check-overflow check-long-lines sync-pdf publish stats find_bullets find_blank_pages blank_pages_report check-pdf-prereqs diagrams

all:	book ## Build all formats (epub, html, pdf, docx)

book:	epub html pdf docx ## Build all formats (epub, html, pdf, docx)

clean: ## Remove build directory and all generated files
	@if [ -d "$(BUILD)" ]; then \
		echo "Removing $(BUILD) directory..."; \
		$(RMDIR_CMD) $(BUILD); \
	else \
		echo "$(BUILD) directory already clean."; \
	fi

####################################################################################################
# Utilities
####################################################################################################

validate: ### Validate chapter contents for forbidden words
	@echo "Validating chapter contents..."
	@result=$$(grep -Ein '\btribal\b' $(CHAPTERS) 2>/dev/null || true); \
	if [ -n "$$result" ]; then \
		echo ""; \
		echo "ERROR: Forbidden word \"tribal\" found in chapters:"; \
		echo "$$result"; \
		echo ""; \
		exit 1; \
	else \
		echo "Validation passed."; \
	fi

check-pdf-prereqs: ## Check if PDF generation prerequisites are available
	@echo "Checking PDF generation prerequisites..."
	@if ! command -v xelatex >/dev/null 2>&1; then \
		echo ""; \
		echo "❌ xelatex not found!"; \
		echo ""; \
		echo "To fix this, you have several options:"; \
		echo ""; \
		echo "1. 🔧 If using devbox, activate the shell:"; \
		echo "   devbox shell"; \
		echo ""; \
		echo "2. 🍺 Install via Homebrew (macOS):"; \
		echo "   brew install --cask mactex"; \
		echo ""; \
		echo "3. 📦 Install via package manager:"; \
		echo "   # Ubuntu/Debian: sudo apt install texlive-xetex"; \
		echo "   # Fedora: sudo dnf install texlive-xetex"; \
		echo "   # Arch: sudo pacman -S texlive-xetex"; \
		echo ""; \
		exit 1; \
	fi
	@echo "✅ xelatex is available"

check-overflow: ### Check for potentially overflowing code lines
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

check-long-lines: ### Check for very long lines in code blocks
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

sync-pdf: $(BUILD)/pdf/$(OUTPUT_FILENAME).pdf ## Sync the generated PDF to PUBLISH_PATH
	@echo ""
	@echo "Copying PDF to PUBLISH_PATH..."
	@if [ -d "$(PUBLISH_PATH)" ]; then \
		cp "$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf" "$(PUBLISH_PATH)/$(OUTPUT_FILENAME).pdf"; \
		figlet "Make for Devops!"; \
		echo "✅ PDF copied to PUBLISH_PATH: $(PUBLISH_PATH)/$(OUTPUT_FILENAME).pdf"; \
	else \
		echo "❌ PUBLISH_PATH not found at: $(PUBLISH_PATH)"; \
		echo "  You can override with: make sync-pdf PUBLISH_PATH=/path/to/your/publish"; \
	fi

publish: sync-pdf stats ## Publish the book by syncing the PDF to PUBLISH_PATH and showing stats
	@echo ""
	@echo "🚀 Publish complete! Our book is ready to read."

find_blank_pages: $(BUILD)/pdf/$(OUTPUT_FILENAME).pdf ## Find blank pages in the PDF
	@bin/pdf_blank_scanner.py $(BUILD)/pdf/$(OUTPUT_FILENAME).pdf

blank_pages_report: $(BUILD)/pdf/$(OUTPUT_FILENAME).pdf ## Generate a report of blank pages in the PDF
	@bin/pdf_blank_scanner.py $(BUILD)/pdf/$(OUTPUT_FILENAME).pdf --create-report

diagrams: $(PNG_FILES) ## Generate PNG diagrams from all .mmd files

# Pa		ern rule to convert .mmd files to .png files
images/%.png: images/%.mmd
	@echo "Generating diagram: $@..."
	@if command -v mmdc >/dev/null 2>&1; then \
		mmdc -i $< -o $@; \
	else \
		echo "❌ mmdc (mermaid-cli) not found!"; \
		echo "Install it with: npm install -g @mermaid-js/mermaid-cli"; \
		exit 1; \
	fi
	@echo "✅ Generated: $@"
find_bullets: ## Find bullet points that may be incorrectly forma		ed
	@awk 'prev ~ /:$$/ && $$0 ~ /^[[:space:]]*[-*+][[:space:]]/ {print FILENAME ":" FNR ":" prev "\n" $$0} {prev=$$0}' chapters/*.md

stats: ## Show book statistics
	@echo ""
	@echo "📚 Book Statistics"
	@echo "========================"
	@main_chapters=$$(echo $(PART_1) $(PART_2) $(PART_3) $(PART_4) $(PART_5) | wc -w); \
	appendix_count=$$(echo $(APPENDICES) | wc -w); \
	total_chapters=$$(echo $(CHAPTERS) | wc -w); \
	total_words=$$(cat $(CHAPTERS) 2>/dev/null | wc -w); \
	total_lines=$$(cat $(CHAPTERS) 2>/dev/null | wc -l); \
	main_words=$$(cat $(PART_1) $(PART_2) $(PART_3) $(PART_4) $(PART_5) 2>/dev/null | wc -w); \
	appendix_words=$$(cat $(APPENDICES) 2>/dev/null | wc -w); \
	echo "📖 Main chapters: $$main_chapters"; \
	echo "📋 Appendices: $$appendix_count"; \
	echo "📄 Total files: $$total_chapters"; \
	echo ""; \
	echo "📝 Main content: $$main_words words"; \
	echo "📎 Appendices: $$appendix_words words"; \
	echo "📊 Total words: $$total_words"; \
	echo "📏 Total lines: $$total_lines"; \
	echo ""; \
	if [ -f "$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf" ]; then \
		if command -v pdfinfo >/dev/null 2>&1; then \
			pages=$$(pdfinfo "$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf" | grep "Pages:" | awk '{print $$2}'); \
			title=$$(pdfinfo "$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf" | grep "Title:" | cut -d: -f2- | sed 's/^ *//'); \
			author=$$(pdfinfo "$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf" | grep "Author:" | cut -d: -f2- | sed 's/^ *//'); \
			creator=$$(pdfinfo "$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf" | grep "Creator:" | cut -d: -f2- | sed 's/^ *//'); \
			echo "📑 PDF pages: $$pages"; \
			echo "📖 PDF title: $$title"; \
			echo "👤 PDF author: $$author"; \
			echo "🔧 PDF creator: $$creator"; \
		elif command -v mdls >/dev/null 2>&1; then \
			pages=$$(mdls -name kMDItemNumberOfPages "$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf" | awk '{print $$3}'); \
			title=$$(mdls -name kMDItemTitle "$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf" | cut -d= -f2 | sed 's/^ *"//;s/"$$//'); \
			author=$$(mdls -name kMDItemAuthors "$(BUILD)/pdf/$(OUTPUT_FILENAME).pdf" | cut -d= -f2 | sed 's/^ *"//;s/"$$//'); \
			echo "📑 PDF pages: $$pages"; \
			echo "📖 PDF title: $$title"; \
			echo "👤 PDF author: $$author"; \
		else \
			echo "📑 PDF pages: (install pdfinfo to see metadata)"; \
		fi; \
		echo ""; \
		echo "🔍 Git info embedded in PDF:"; \
		git_sha=$$(grep -o "git_sha: [a-f0-9]*" $(TMP_METADATA) 2>/dev/null | cut -d: -f2 | sed 's/^ *//'); \
		git_date=$$(grep -o "git_date: [0-9-]*" $(TMP_METADATA) 2>/dev/null | cut -d: -f2 | sed 's/^ *//'); \
		if [ -n "$$git_sha" ]; then \
			echo "📝 Git commit: $$git_sha"; \
			echo "📅 Git date: $$git_date"; \
		else \
			echo "📝 Git info: (run 'make clean && make pdf' to embed)"; \
		fi; \
	else \
		echo "📑 PDF pages: (run 'make pdf' first)"; \
	fi; \
	echo "";

help:  ## Show this help message
	@echo "📖 Make for DevOps - Build System"
	@echo "=================================="
	@echo ""
	@echo "Available targets:"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*##/ { printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)
	@echo ""
	@echo "Configuration:"
	@echo "  OVERFLOW_LIMIT=$(OVERFLOW_LIMIT)     # Line length limit for code blocks"
	@echo "  LONG_LINE_LIMIT=$(LONG_LINE_LIMIT)    # Very long line limit"
	@echo
	@echo "  PUBLISH_PATH=$(PUBLISH_PATH)"
	@echo ""

toc: ## Generate the Table of Contents from source files
	@echo "## 5. Detailed Table of Contents"
	@# Process each part
	@for part_num in 1 2 3 4 5; do \
		part_file="parts/part-$$part_num.md"; \
		if [ -f "$$part_file" ]; then \
			part_title=$$(grep '\\part{' "$$part_file" | sed 's/\\part{\(.*\)}/\1/'); \
			echo
			echo "### $$part_title"; \
		fi; \
		\
		case $$part_num in \
			1) chapters="$(PART_1)";; \
			2) chapters="$(PART_2)";; \
			3) chapters="$(PART_3)";; \
			4) chapters="$(PART_4)";; \
			5) chapters="$(PART_5)";; \
		esac; \
		\
		for chapter_file in $$chapters; do \
			if [[ "$$chapter_file" == chapters/*.md ]]; then \
				chapter_title=$$(head -1 "$$chapter_file" | sed 's/^# //'); \
				echo "- **$$chapter_title**"; \
			fi; \
		done; \
	done; \
	\
	echo ""; \
	echo "### Appendices"; \
	for appendix in $(APPENDICES); do \
		appendix_title=$$(head -1 "$$appendix" | sed 's/^# //'); \
		echo "- **$$appendix_title**"; \
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

epub:	validate $(BUILD)/epub/$(OUTPUT_FILENAME).epub ## Generate EPUB format (warning, not functional)

html:	validate $(BUILD)/html/$(OUTPUT_FILENAME).html ## Generate HTML format

pdf:	validate check-pdf-prereqs $(BUILD)/pdf/$(OUTPUT_FILENAME).pdf ## Generate PDF format

docx:	validate $(BUILD)/docx/$(OUTPUT_FILENAME).docx ## Generate DOCX format

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
