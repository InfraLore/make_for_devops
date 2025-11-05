# Editing Session Summary

## Book context

Make for DevOps, a book-length tutorial that prioritizes clarity, practicality, and progressive disclosure. Assumes readers are practitioners who need to understand when and why to use features, not just how.

## Editing Patterns Applied

### Disambiguate jargon with concrete examples

Changed: "cost of indirection" (computer science jargon)
To: "overhead of adding these features" + specific costs (harder to trace, more mental context, more bug hiding places)

Principle: If a term requires CS background, either define it or replace it with plain language


### Establish concepts before using shorthand

Added: Explicit "Bash strict mode" label when introducing -euo pipefail
Then: Consistently use "strict mode" throughout the section
Principle: Give readers a mental anchor before using abbreviated references


### Use callouts for common gotchas and misconceptions

Added: Callout about Make function argument handling
Included: Both the problem (missing args) and the less-dangerous case (extra args)
Principle: Warn about pitfalls that will bite practitioners, but don't over-engineer solutions
Used Latex formatting for the callout

### Acknowledge alternative approaches and set proper context

Added: Note that strict mode is a "safety net, not primary defense" for variable validation
Context: Strict mode shines during development, then stays as insurance
Principle: Don't oversell a feature's role; explain where it fits in the toolkit


### Identify and remove duplicate advice

Found: "Warning Signs You're Over-Engineering" subsection repeated content from "Recognizing When You Need Advanced Features" (literally two paragraphs earlier)
Found: Seven different "don't overdo it" warnings throughout the chapter
Action: Cut the immediate duplicate; kept later warnings because they were separated by content and added new context
Principle: Important messages deserve repetition, but not word-for-word duplication in adjacent sections. Map where advice appears and consolidate near-duplicates.


### Help readers prioritize in comprehensive sections

Identified: "Hidden Gems" section lists many features but doesn't triage
Suggested: "Start here... Explore later..." guidance
Principle: When presenting multiple options, guide readers on where to begin


### Watch for structural issues

Identified: "The Test" subsection felt orphaned from "Incremental Adoption Pattern"
Identified: "Combining Hidden Features" example might confuse priorities
Principle: Check that subsections connect logically to their parents; flag examples that might contradict earlier advice


### Add forward/backward references for complex topics

Suggested: Pattern rules section could reference pattern-specific variables
Principle: Help readers see connections between related features across the chapter



## Key Quality Checks:

Does this require specialized knowledge to understand? (If yes, define or simplify)
Is this safety mechanism positioned correctly? (Primary defense vs. backup)
Will readers know which feature to try first? (Prioritization guidance)
Are examples showing best practices or just capability demonstrations?
Does new content contradict or undermine earlier advice?
Is this advice repeated elsewhere in the chapter? (Map all instances; keep strategically placed ones, cut duplicates)

## Voice/Tone Notes:

Practical over academic
Acknowledge tradeoffs honestly ("That overhead is real...")
Don't be defensive about edge cases ("no sense being too defensive")
Give readers agency ("You've got all the spots marked")
Trust your editing instincts ("sometimes the best revision is just deleting the redundant bit")

# Example diff from an editing session:
