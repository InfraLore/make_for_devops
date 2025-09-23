# Make for DevOps — A Book Project

> _Format and tooling derived from the [wikiti/pandoc-book-template](https://github.com/wikiti/pandoc-book-template) with content authored for "Make for DevOps"._

---

## What is this?

**Make for DevOps** is a practical, research-driven book project exploring how the humble `Makefile` can bridge the DevOps knowledge crisis—serving both as project glue and as an executable, discoverable record of workflow know-how.

This repo holds:

- Draft chapters and plan for "Make for DevOps"
- All supporting material, references, and research
- Pandoc/Makefile-based build system for fast PDF, HTML, and EPUB export
- A Devbox dev environment configuration

---

## Why "Make for DevOps"?

DevOps teams face a persistent challenge with undocumented system expertise--the practical details of how systems work and the reasoning behind design decisions often remain locked in informal channels, scattered across temporary chat logs and outdated documentation. Most books and tools treat Make as only a build tool for code; **we show how it can be the backbone of workflow documentation, discoverability, and team onboarding**.

See [proposal.md](proposal.md) and [plan.md](plan.md) for:
- Audience and technical level
- Book structure, competitive analysis, and research
- Detailed writing plan and annotated references

---

## Status

- 📝 Draft in progress: see [plan.md](plan.md) for writing schedule and chapter statuses
- 📚 Goal: 350–400 pages, 200+ code samples, shipping 2026
- 💡 Open to feedback! Open an issue to discuss DevOps knowledge management, Make workflows, or suggest resources

---

## Who is this for?

See full details in [proposal.md](proposal.md); a brief version:

- **DevOps, SRE, Platform Engineers** (2–5 years’ experience)
- Teams scaling infra and onboarding, using or interested in Make beyond C/C++ builds
- Anyone facing the "Institutional Knowledge" crisis or using/maintaining complex automation workflows

---

## About this Repository

Originally forked from [wikiti/pandoc-book-template](https://github.com/wikiti/pandoc-book-template), this repository greatly extends and modifies the template for book-length DevOps and workflow automation topics. We retain Pandoc/Makefile-based builds for reliability and reproducibility.

---

## Quickstart: Dev Environment with Devbox

**This repository includes a [`devbox.json`](devbox.json) for instant bootstrapping.**

If you use [Devbox](https://www.jetpack.io/devbox):

1. Install Devbox:  
   [https://www.jetpack.io/devbox/docs/install/](https://www.jetpack.io/devbox/docs/install/)
2. In this project directory, run:
   ```sh
   devbox shell
   ```
3. That’s it! All necessary tools for building (Pandoc, Make, XeLaTeX, etc) are automatically installed and available in your shell.

No need to install dependencies one-by-one or pollute your global environment.  
If you don’t use Devbox, see below for manual setup instructions.

---

## Usage & Build

**Requirements:**  
- [Pandoc](http://pandoc.org/)
- [GNU Make](https://www.gnu.org/software/make/)
- [XeLaTeX](https://tug.org/xetex/) for PDF output  
- (Recommended) [pandoc-crossref](https://github.com/lierdakil/pandoc-crossref) for cross-referencing

**Basic build:**
```bash
make pdf    # Build book PDF (in build/pdf/)
make html   # Build HTML (in build/html/)
make epub   # Build EPUB (in build/epub/)
```

See the original [template README](https://github.com/wikiti/pandoc-book-template) for advanced topics—this repo adds many book-specific tweaks.

---

## Project Structure

```
my-book/
|- build/             # Output (PDF, HTML, EPUB, DOCX, etc)
|- chapters/          # Book content (per-chapter markdown)
|- images/            # Figures and diagrams
|- plan.md            # Writing plan, research, sources, TODO
|- metadata.yml       # Book metadata
|- Makefile           # Build instructions
|- proposal.md        # Formal book proposal, audience research
|- README.md          # You're here!
```

---

## Research Philosophy & Roadmap

We are explicitly researching the **role of automation (Makefiles, pipelines) in the DevOps knowledge crisis**:
- Can automation *preserve* team know-how?
- Or does it bury context and rationale under inscrutable scripts?

This book covers not only how to use Make, but why it matters for team productivity, onboarding, and reliable operations. See [plan.md](plan.md) for deep-dive research, industry and academic citations, and our writing plan.

---

## Acknowledgments

- Original template © Daniel Herzog, [wikiti/pandoc-book-template](https://github.com/wikiti/pandoc-book-template), MIT License
- Significant updates, research, and content © Contributors to "Make for DevOps" (see [plan.md](plan.md) for author info and project direction)

---

## References and Further Reading

- [Proposal & audience definition](proposal.md)
- [Detailed writing plan, research, blog/article links](plan.md)
- [Pandoc Manual](http://pandoc.org/MANUAL.html)
- [Official GNU Make Manual](https://www.gnu.org/software/make/manual/)
- [Managaing Projects with GNU Make (O'Reilly)](https://learning.oreilly.com/library/view/managing-projects-with/0596006101/pt01.html)
- Academic/industry sources: see bottom of [plan.md](plan.md)