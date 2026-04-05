# TODO: Extract Make Cheatsheet to Standalone Project

## Overview
Extract the Make cheatsheet functionality from this book project into a simple, standalone project.

## What We Have
- **Content**: `parts/cheat-sheet.md` - comprehensive Make reference (313 lines)
- **Template**: `templates/cheat-sheet.latex` - 4-column landscape PDF template
- **Build**: `cheat` target generates PDF using pandoc + XeLaTeX

## Minimal Extraction (30 minutes)

### Step 1: Copy Files (5 minutes)
- [ ] Copy `parts/cheat-sheet.md` → `cheatsheet.md` 
- [ ] Copy `templates/cheat-sheet.latex` → `template.latex`
- [ ] Create `.gitignore` with `build/`

### Step 2: Simple Makefile (15 minutes)
- [ ] `help` target (default)
- [ ] `build` target (generate PDF)  
- [ ] `clean` target (remove build/)
- [ ] Basic dependency check

### Step 3: Basic README (10 minutes)
- [ ] What it is
- [ ] Requirements: pandoc, xelatex
- [ ] Usage: `make build`
- [ ] Output: `build/make-cheatsheet.pdf`

That's it. Working cheat sheet project in 30 minutes.

## Minimal Project Structure
```
make-cheatsheet/
├── cheatsheet.md     # Main content  
├── template.latex    # PDF template
├── Makefile         # Simple build
├── README.md        # Basic docs
├── .gitignore       # Ignore build/
└── build/           # Generated PDF
```

## Simple Makefile
```makefile
.DEFAULT_GOAL := help

help: ## Show commands
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-10s %s\n", $$1, $$2}'

build: ## Generate PDF cheat sheet
	@mkdir -p build
	pandoc --listings cheatsheet.md \
		-o build/make-cheatsheet.pdf \
		--template=template.latex \
		--pdf-engine=xelatex

clean: ## Remove build directory
	rm -rf build

.PHONY: help build clean
```

## Future Enhancements (Later)
- Multiple output formats (HTML, mobile-friendly)
- GitHub Actions for automated builds
- Font customization options  
- Community contribution process
- Release management