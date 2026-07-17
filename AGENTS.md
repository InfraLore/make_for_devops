# Agents

## Book Conventions

- Always capitalize **Make** when referring to the software (proper noun).
- Never use the word "tribal" — use "team lore" instead.
- Keep Makefile line width to **75 characters max**.
- Use `\chaptersubtitle{...}` for chapter subtitle markup.

## Makefile Examples in the Book

- Keep examples focused and conceptual, 10–30 lines illustrating a specific pattern.
- Show the interface and discovery pattern, not complete implementations.
- Use placeholders like `./scripts/deploy.sh` or `@echo "Running validation..."` for complex operations.
- Teach how to think about structuring Makefiles, not production-ready copy-paste code.
- Show simple, high-level targets first; indicate internal implementation with `_` prefix or script references.
- Emphasize the learning journey over comprehensive solutions.

### Avoid

- 100+ line "complete" Makefiles trying to cover every edge case.
- Showing every flag and option for tools like terraform, docker, kubectl.
- Implementation details that obscure the pattern being taught.
- Examples that could work as-is in production (that's not the book's goal).
