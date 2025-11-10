convo:

https://claude.ai/chat/0b0cbf74-9c89-4541-8eac-21ecf5fef5e7

NOTE: that conversation was the start... but it took multiple conversations to get to the point of completing the project.

What follows are scattered notes from the early stages of the project.

It looks like Claude 3.5 really wants to make quick reference guides, not write books. That's OK. We can get Claude 4 to do this, two chapters at at time.

- [x] let Claude 4 know that we've added a new chapter 4 (hand it the revised TOC)

Build plan: 2-3 chapters a day:
- all chapters complete

## Chapter 1 - Why Make? - Research plan

Research Areas:

1. Knowledge Management in DevOps

- Academic papers on DevOps knowledge sharing
- Industry surveys about onboarding challenges
- Studies on documentation effectiveness
- Cost of knowledge loss in tech organizations

2. Documentation Failures

- Research on documentation rot
- Studies on why documentation becomes outdated
- Industry surveys about documentation practices
- Real-world examples of documentation failures

3. Make History and Evolution

- Original Make paper by Stuart Feldman
- Evolution of Make usage over time
- Modern Make implementations
- Make’s role in Unix/Linux development

4. ROI Metrics

- Team onboarding time statistics
- Cost of knowledge silos
- Productivity impact of self-documenting systems
- DevOps automation ROI studies

Sources to Consider:

1. Academic:

- IEEE Digital Library
- ACM Digital Library
- Google Scholar
- [arXiv.org](http://arxiv.org/)

2. Industry:

- State of DevOps Reports
- GitHub Octoverse Reports
- Stack Overflow Developer Surveys
- DevOps Enterprise Summit presentations

3. Case Studies:

- Large tech companies using Make
- Open source projects with exemplary Makefiles
- DevOps transformation stories

4. Community:

- DevOps forums
- Make-related GitHub discussions
- Reddit r/devops
- LinkedIn DevOps groups

1. Original Make Paper:
    S. I. Feldman, “Make — A Program for Maintaining Computer Programs,” Software: Practice and Experience, vol. 9, pp. 255-265, 1979.
    DOI: [https://doi.org/10.1002/spe.4380090402](https://doi.org/10.1002/spe.4380090402)
    https://pages.cs.wisc.edu/~horwitz/make/make.pdf

Some key quotes from this paper that would be relevant for Chapter 1:

1. On Make’s purpose (still relevant today):
    “Make allows a programmer to maintain a collection of programs by describing their interdependencies.”

2. On automation and reproducibility:
    “Make uses the recorded dependencies to determine automatically which pieces need to be redone…”

3. On Make’s universality (prescient for DevOps):
    “Make is most useful for programs that need to be modified frequently and whose compilations are complex…”


We could use these historical points to show how Make’s original principles align perfectly with modern DevOps needs:

- Dependencies management
- Automation
- Reproducibility
- Handling complexity
- Frequent modifications


papers that cite Feldman's paper:

“Build Systems à la Carte” by A. Mokhov, et al. (2018)
Proceedings of the ACM on Programming Languages, Vol. 2, No. ICFP, Article 79
[https://doi.org/10.1145/3236774](https://doi.org/10.1145/3236774)
https://dl.acm.org/doi/pdf/10.1145/3236774


*I* can find papers that cite other papers, no reason to make Claude work that hard, it's sort of bad at it.



2. Historical Context/Evolution:
    V. Henson and D. Garzik, “BitKeeper for kernel developers,” in Proceedings of the Linux Symposium, Ottawa, 2002.
    [Shows how Make evolved in Linux kernel development]
    Available: [https://www.kernel.org/doc/ols/2002/ols2002-pages-83-90.pdf](https://www.kernel.org/doc/ols/2002/ols2002-pages-83-90.pdf)

3. Modern Make Usage:
    P. Miller, “Recursive Make Considered Harmful,” AUUGN Journal of AUUG Inc., 1997.
    Available: [http://aegis.sourceforge.net/auug97.pdf](http://aegis.sourceforge.net/auug97.pdf)
    [This paper is frequently cited in discussions about Make best practices]


Oooh, cool, Julia Evans wrote about Make:
https://jvns.ca/blog/2025/06/10/how-to-compile-a-c-program/

Though that blog post is just about using Make as it was intended, to compile C code, which is *boring*. But, it's a good intro to Make in its original context.

---
## Recommended Blog Posts About Make

| Blog Post                                                    | Key Highlights                                                                                                                                 | URL                                                                                | Date     |
| ------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------- | -------- |
| <b>Makefiles – Best Practices</b>                            | - Detailed discussion of Make's strengths and limitations<br>- Insights from Hacker News discussion<br>- Comparison with modern build systems  | https://news.ycombinator.com/item?id=19052830                                      | Feb 2019 |
| <b>A Tutorial on Portable Makefiles</b>                      | - Explores Make's dependency handling<br>- Discusses challenges with non-existent dependencies<br>- Compares Make to alternative build systems | https://nullprogram.com/blog/2017/08/20/                                           | Aug 2017 |
| <b>Better Builds with Make</b>                               | - Beginner's guide to Make<br>- Explains Make's core concepts<br>- Practical examples of Makefile usage                                        | https://dev.to/danielrbradley/better-builds-with-make-a-beginners-guide-1n0        | Aug 2023 |
| <b>Why you should adopt Makefile in all of your projects</b> | - Introduction to Make and Makefiles<br>- Practical TypeScript project example<br>- Detailed explanation of Make's workflow                    | https://yieldcode.blog/post/why-you-should-adpot-makefile-in-all-of-your-projects/ | Nov 2022 |


## Additional Recommendations

- [Official GNU Make Manual](https://www.gnu.org/software/make/manual/): Several commenters recommended reading the official GNU Make manual as the most comprehensive resource

Would you like me to elaborate on any of these blog posts or help you find more specific Make resources?
Based on the search results, I can provide some additional context about blog posts on Make:

## Top Blog Posts About Make

1. <b>Makefiles – Best Practices</b>
   - Published on Hacker News
   - Discusses Make's strengths and limitations
   - Key insight: The GNU Make manual is extremely well-written and can serve as a tutorial

2. <b>A Tutorial on Portable Makefiles</b>
   - Explores dependency handling challenges
   - Highlights limitations in handling non-existent dependencies
   - Compares Make to alternative build systems

3. <b>Better Builds with Make</b>
   - Beginner's guide to Make
   - Explains core concepts like targets, dependencies, and rules
   - Provides practical examples of Makefile usage

4. <b>Why You Should Adopt Makefile in All Your Projects</b>
   - Explains Make's history (first released in April 1976)
   - Provides practical TypeScript project examples
   - Discusses Make's role in build automation

## Key Takeaways About Make

- <b>Make is a build automation tool</b> that helps manage project compilation and dependencies
- It compares file timestamps to determine when to rebuild targets
- Works across multiple programming languages
- Particularly useful for scientific computing and reproducible research


---
# presentations about Make in a DevOps context

- https://web.stanford.edu/class/archive/cs/cs45/cs45.1234/lectures/10-build-systems-devops.pdf
- https://www.devopsschool.com/tutorial/makefiles/Makefile.pptx
- https://configzen.com/blog/mastering-makefiles-avoid-devops-pitfalls
- https://adamtuttle.codes/blog/2021/my-ongoing-love-affair-with-gnu-make/
- https://adamtuttle.codes/blog/2020/how-i-use-make/
- https://data-science-master.github.io/lectures/08_make/08_make.html
	- includes some nice examples for Data Science use cases
- https://www.reddit.com/r/devops/comments/18bsodf/whats_with_devops_engineers_using_make_of_all/
	- massive, full of gripes, but generally respectful of Make and its place as DevOps glue


# Institutional Knowledge Crisis

Why configuration management shouldn't rely on institutional knowledge:
https://www.doppler.com/blog/config-management-institutional-knowledge-risk

https://chatgpt.com/c/68cca4c7-0678-8326-b19f-ef0dc971a127

^^ skip to the end, there's a gap in research (maybe)


Honestly, it's the theme of this book... And a big role of DevOps is to automate builds... so... gosh, maybe build automation is *causing* a perceived institutional knowledge crisis? It's kinda a complex thing...


### The Overlooked Role of Build Automation in the DevOps Knowledge Crisis

Most discussions of the “institutional knowledge crisis” in DevOps focus on culture, documentation practices, onboarding, and post-mortems. The central concern is that critical knowledge—how systems work, why decisions were made, how to recover from incidents—lives in people’s heads and disappears when they leave.

What’s missing in this conversation is the role of **build and workflow automation tools**, especially **GNU Make** and its modern successors (Taskfile, Just, Mage, etc.).

- **Makefiles capture tacit knowledge.** They encode the exact commands, dependencies, and environment assumptions required to build, test, and deploy software.

- **They are living artifacts.** Unlike a wiki, a `Makefile` breaks if it’s wrong—forcing it to stay closer to reality than static documentation.

- **They bridge gaps for newcomers.** Running `make deploy` provides immediate access to otherwise undocumented, fragile sequences of commands.

- **But they risk becoming opaque.** Without annotation or context, a Makefile can function as a black box: runnable, but not explainable. The _reasoning_ behind steps is still at risk of loss.


This creates a gap in both research and practice: **automation files are simultaneously one of the most durable carriers of institutional knowledge, and one of the least studied or discussed in the DevOps knowledge-management literature.**

A promising area for future work is to treat Makefiles not just as automation artifacts, but as **sites of knowledge capture**. For example:

- Embedding self-documentation (`make help` targets, annotated recipes).

- Linking Makefile tasks to architectural decision records or incident logs.

- Studying how teams actually use and maintain Makefiles as part of their knowledge ecosystem.


Exploring this angle could surface new strategies for mitigating the knowledge crisis in DevOps, bridging the gap between _automation_ and _institutional memory_.


---
### DevOps as Both Cure and Cause of the Knowledge Crisis

- **DevOps as automation-first culture.**
    At its heart, DevOps emphasizes _automating everything_: builds, tests, deployments, rollbacks, monitoring. It’s the pursuit of **build automation at organizational scale**.

- **The promise.**
    By automating, we reduce error, make workflows repeatable, and encode steps that once lived only in people’s heads. In theory, that _preserves_ institutional knowledge.

- **The paradox.**
    But the very success of automation can _hollow out human knowledge_:

    - Engineers stop learning the underlying commands because the pipeline handles it.

    - “Why” something happens gets obscured — the automation encodes _what to do_, but rarely _why it was designed that way_.

    - When automation fails, teams discover they’ve lost the _experiential knowledge_ needed to debug it.

- **The crisis.**
    DevOps culture may unintentionally accelerate the institutional knowledge crisis by:

    1. Encouraging teams to **skip documentation** (“the pipeline is the documentation”).

    2. **Shifting knowledge into scripts and YAML** that only a few specialists understand.

    3. **Masking fragile processes** under a veneer of automation, until turnover or incidents reveal the gap.

- **The opportunity.**
    If DevOps is both cure and cause, the real question is: _How do we design automation that also preserves context, rationale, and human understanding?_

    - Pipelines and Makefiles could embed explanatory notes, decision records, and links to design docs.

    - CI/CD tooling could enforce not just builds, but also “knowledge artifacts” (runbooks, ADRs) as part of the process.

    - Teams could treat automation as **knowledge infrastructure**, not just execution infrastructure.


---

That flips the story: instead of seeing DevOps only as the victim of knowledge loss, we start asking whether DevOps practices themselves are **structurally contributing** to the problem.

I poked around; found a few pieces that are close, but none that _exactly_ match the formulation of the paradox (i.e. DevOps automation contributing to institutional knowledge loss). Here’s what I found, plus thoughts on where the gap still is.

---

## What folks _are_ writing that’s related

These works touch on pieces of the paradox — automation vs human understanding / knowledge retention — though not always strongly or explicitly.

|Title / Source|What it Covers that’s Relevant|How Close It Gets to the Paradox|
|---|---|---|
|_ADEPT: A Socio-Technical Theory of Continuous Integration_|Explores how continuous practices (automation, processes, documentation) interact with people / collaboration. It looks at how the tools and automation affect human behavior and process. [arXiv](https://arxiv.org/abs/2102.06834?utm_source=chatgpt.com)|Fairly close. Talks about how automation shapes behavior/teams, though not specifically about loss of knowledge through automation.|
|_A Mixed Method Study of DevOps Challenges_ (arXiv 2024)|Surveys DevOps practitioners, looks at topics like CI/CD tools, infrastructure as code. Finds hard problems around tooling and quality assurance, difficulties in maintaining pipelines. [arXiv](https://arxiv.org/html/2403.16436v1?utm_source=chatgpt.com)|Somewhat close. The findings hint at legibility, complexity, etc., but don’t explicitly frame it as a knowledge crisis caused by automation.|
|_“Automation in DevOps: A Double-Edged Sword? Balancing Efficiency with Human Expertise”_ (blog-style)|Discusses risks of over-automation: losing human insight, becoming dependent on automation, scenario misfits, etc. [Moringa School](https://moringaschool.com/blog/automation-in-devops-a-double-edged-sword-balancing-efficiency-with-human-expertise/?utm_source=chatgpt.com)|This is closest in popular writing. It’s exactly about trade-offs, though not rigorous research; more cautionary piece.|
|_Why DevOps is Killing Innovation …_ (Medium)*|Points out how standardization + automation may stifle creativity, reduce exposure to underlying systems, etc. [Medium](https://medium.com/%40jeromedecinco/why-devops-is-killing-innovation-in-software-development-e7ed617f5798?utm_source=chatgpt.com)|Again, close in spirit, but more about innovation / homogenization than institutional memory per se.|

---

## What’s _not_ there (i.e. the gap)

Here are aspects of the paradox you want that seem under-explored:

- **Explicit framing**: No paper I found places “automation causing institutional knowledge loss” as a primary research question.

- **Case studies**: Lacking detailed empirical studies of teams where automation has led to knowledge gaps, e.g. when key people leave or when weird failures happen, and tracing how much automation played a role.

- **Build tool focused**: I couldn’t find anything that discusses Makefiles / build / workflow automation tools specifically in the knowledge retention context.

- **Context + rationale preservation**: The “why” behind automation choices (why pipelines are built the way they are, why certain commands exist) is rarely studied; most focus is on _how_ to or _how well_ automation is done.

- **Longitudinal perspectives**: How knowledge accumulates or erodes over time with automation.


---

## Possible leads / concepts to draw from

Even though the exact match isn’t found, there are adjacent ideas that could be linked or used in a paper or article:

- **Polanyi’s paradox** (implicit knowledge can’t always be made explicit) — useful to tie to how certain automation hides or abstracts away parts of the system that were once well‐understood. [Wikipedia](https://en.wikipedia.org/wiki/Polanyi%27s_paradox?utm_source=chatgpt.com)

- **Ironies of Automation** (from human factors) — when automation removes tasks, humans lose practice, get less ready/prepared for exceptional cases. [Wikipedia](https://en.wikipedia.org/wiki/Ironies_of_Automation?utm_source=chatgpt.com)

- **Socio-technical theory of CI / automation tools** — what ADEPT shows.


# handy bits of code

## footnote for examples
\footnote{Script delegation pattern---see Chapter 21 for how this aids learning.}

## find where to put the footnote
grep -n '@\./scripts/' chapters/*.md
