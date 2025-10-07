Write a subsection called "Reusable Components with Functions" for Chapter 8 of this Make book for DevOps. This subsection belongs in Section 8.6 "Creating Extensible Frameworks."

Context: This is an advanced Make book chapter that builds complexity gradually. Previous sections covered pattern rules, recursive Make, external tool integration, and conditional execution. The current section focuses on building frameworks teams can customize.

Tone and Style:
- Practical, hands-on approach with working code examples
- Focus on real DevOps scenarios, not theoretical examples
- Emphasize when to use functions vs. simpler alternatives
- Include clear explanations of syntax and benefits
- Follow the book's pattern of showing problems first, then solutions

Content Requirements:
- Explain Make functions using `define` and `endef`
- Show function parameters with $(1), $(2), etc.
- Demonstrate calling functions with `$(call function_name,arg1,arg2)`
- Use DevOps-relevant examples (notifications, deployments, cleanup tasks)
- Show how functions reduce duplication in framework code
- Include guidance on when functions are worth the complexity
- Keep examples practical and immediately useful
- Exmamples should be brief, and do NOT need to be complete working code
- Delegate complicated stuff to hand-wavy scripts... you are here to explain Make
- Try to avoid any examples that imploy one should deploy untested code (oops)
- Do NOT use the word "tribal"

Structure:
- Brief intro explaining when functions solve real problems
- Syntax explanation with simple example
- Suggestion: - an example function for repetiive text, like a reminder to run a cleanup operation
- Practical DevOps example showing before/after
- Advanced example with multiple parameters
- Guidance on when to use vs. avoid functions

Length: Approximately 2-3 pages following the existing chapter's format and depth.