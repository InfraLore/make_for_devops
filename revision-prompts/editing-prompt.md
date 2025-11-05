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

diff --git a/chapters/08-advanced_make.md b/chapters/08-advanced_make.md
index b056f0cf4..f364364e4 100644
--- a/chapters/08-advanced_make.md
+++ b/chapters/08-advanced_make.md
@@ -81,16 +81,11 @@ what's possible. They can run `make -n deploy-staging` and see exactly what will
 happen. But behind that simplicity, you've eliminated hundreds of lines of
 duplication.

-### Warning Signs You're Over-Engineering
-
-- You're using pattern rules for two targets (just write two targets)
-- Your functions have functions calling functions (flatten it)
-- New team members can't figure out what `make deploy-prod` does (too much
-  indirection)
-- You're writing advanced features "because we might need this later" (YAGNI)
-- Your Makefile feels clever rather than clear
-
-Advanced features solve real problems, but only use them when duplication pain or failure risk exceeds the overhead of adding these features. That overhead is real: pattern rules make targets harder to trace, functions hide logic behind calls that require jumping to definitions, and secondary expansion adds a second evaluation pass that can confuse debugging.
+Advanced features solve real problems, but only use them when duplication pain
+or failure risk exceeds the overhead of adding these features. That overhead is
+real: pattern rules make targets harder to trace, functions hide logic behind
+calls that require jumping to definitions, and secondary expansion adds a second
+evaluation pass that can confuse debugging.

 \newpage
 ## Pattern Rules for Handling Multiple Environments
@@ -119,7 +114,8 @@ deploy-%: validate-% ## Deploy to specified environment
 The `%` matches any string, and `$*` contains the matched portion. One rule
 creates multiple targets.

-Pattern rules become even more powerful with pattern-specific variables (covered later in this chapter).
+Pattern rules become even more powerful with pattern-specific variables (covered
+later in this chapter).

 \newpage
 ### Environment-Specific Validation
@@ -287,7 +283,9 @@ deploy-safe:
 	terraform plan
 	terraform apply
 ```
-**This combination is known as "Bash strict mode",a set of flags that transforms the shell from permissive to rigorous, catching errors that would otherwise fail silently.**
+**This combination is known as "Bash strict mode", a set of flags that
+transforms the shell from permissive to rigorous, catching errors that would
+otherwise fail silently.**

 Each flag provides specific protection:

diff --git a/revision-prompts/editing-prompt.md b/revision-prompts/editing-prompt.md
new file mode 100644
index 000000000..b130031dc
--- /dev/null
+++ b/revision-prompts/editing-prompt.md
@@ -0,0 +1,84 @@
+# Editing Session Summary
+
+## Book context
+
+Make for DevOps, a book-length tutorial that prioritizes clarity, practicality, and progressive disclosure. Assumes readers are practitioners who need to understand when and why to use features, not just how.
+
+## Editing Patterns Applied
+
+### Disambiguate jargon with concrete examples
+
+Changed: "cost of indirection" (computer science jargon)
+To: "overhead of adding these features" + specific costs (harder to trace, more mental context, more bug hiding places)
+
+Principle: If a term requires CS background, either define it or replace it with plain language
+
+
+### Establish concepts before using shorthand
+
+Added: Explicit "Bash strict mode" label when introducing -euo pipefail
+Then: Consistently use "strict mode" throughout the section
+Principle: Give readers a mental anchor before using abbreviated references
+
+
+### Use callouts for common gotchas and misconceptions
+
+Added: Callout about Make function argument handling
+Included: Both the problem (missing args) and the less-dangerous case (extra args)
+Principle: Warn about pitfalls that will bite practitioners, but don't over-engineer solutions
+Used Latex formatting for the callout
+
+### Acknowledge alternative approaches and set proper context
+
+Added: Note that strict mode is a "safety net, not primary defense" for variable validation
+Context: Strict mode shines during development, then stays as insurance
+Principle: Don't oversell a feature's role; explain where it fits in the toolkit
+
+
+### Identify and remove duplicate advice
+
+Found: "Warning Signs You're Over-Engineering" subsection repeated content from "Recognizing When You Need Advanced Features" (literally two paragraphs earlier)
+Found: Seven different "don't overdo it" warnings throughout the chapter
+Action: Cut the immediate duplicate; kept later warnings because they were separated by content and added new context
+Principle: Important messages deserve repetition, but not word-for-word duplication in adjacent sections. Map where advice appears and consolidate near-duplicates.
+
+
+### Help readers prioritize in comprehensive sections
+
+Identified: "Hidden Gems" section lists many features but doesn't triage
+Suggested: "Start here... Explore later..." guidance
+Principle: When presenting multiple options, guide readers on where to begin
+
+
+### Watch for structural issues
+
+Identified: "The Test" subsection felt orphaned from "Incremental Adoption Pattern"
+Identified: "Combining Hidden Features" example might confuse priorities
+Principle: Check that subsections connect logically to their parents; flag examples that might contradict earlier advice
+
+
+### Add forward/backward references for complex topics
+
+Suggested: Pattern rules section could reference pattern-specific variables
+Principle: Help readers see connections between related features across the chapter
+
+
+
+## Key Quality Checks:
+
+Does this require specialized knowledge to understand? (If yes, define or simplify)
+Is this safety mechanism positioned correctly? (Primary defense vs. backup)
+Will readers know which feature to try first? (Prioritization guidance)
+Are examples showing best practices or just capability demonstrations?
+Does new content contradict or undermine earlier advice?
+Is this advice repeated elsewhere in the chapter? (Map all instances; keep strategically placed ones, cut duplicates)
+
+## Voice/Tone Notes:
+
+Practical over academic
+Acknowledge tradeoffs honestly ("That overhead is real...")
+Don't be defensive about edge cases ("no sense being too defensive")
+Give readers agency ("You've got all the spots marked")
+Trust your editing instincts ("sometimes the best revision is just deleting the redundant bit")
+

```

# What to do with this context:
In a moment, I will paste another chapter for us to work on. You should apply the same principles and methods as exemplified in the context I just provided, as well as in the diff.

Signify your understanding by asking for the chapter content that we need to work on. You can do so by saying "Ready to Go! Please paste the next chapter."
