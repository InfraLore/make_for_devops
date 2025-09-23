#! /usr/bin/env python3
"""
fenced_wrap.py
Reformat code blocks in a markdown file to ensure no line exceeds a specified length,
using an Ollama model to perform the reformatting.
"""

import re
import click
import ollama

def ask_ollama(model, code, language, max_length=80):
    prompt = (
        f"Reformat the following {language} code so that no line exceeds {max_length} characters. "
        "Preserve indentation and code meaning. Return ONLY the code block.\n\n"
        f"{code}"
    )
    response = ollama.generate(
        model=model,
        prompt=prompt
    )
    out = response["response"]
    return out.strip()

def process_markdown(content, model, max_length):
    def replace_block(match):
        fence = match.group("fence")
        language = match.group("lang").strip()
        code = match.group("code")
        print(f"Processing code block with language '{language}'...")
        new_code = ask_ollama(model, code, language or "code", max_length)
        # Clean the output - remove possible triple backticks from Ollama reply
        new_code = re.sub(r"^```.*?\n", "", new_code)
        new_code = re.sub(r"```$", "", new_code)
        return f"{fence}{language}\n{new_code}\n{fence}"

    pattern = re.compile(
        r"(?P<fence>```)(?P<lang>[^\n]*)\n(?P<code>.*?)(?<=\n)(?P=fence)",
        flags=re.DOTALL
    )
    return pattern.sub(replace_block, content)

@click.command()
@click.argument("markdown_file", type=click.Path(exists=True))
@click.option("--model", default="qwen3:4B", help="Ollama model to use")
@click.option("--max-length", default=80, help="Max line length for code")
def main(markdown_file, model, max_length):
    with open(markdown_file, "r", encoding="utf-8") as f:
        content = f.read()
    new_content = process_markdown(content, model, max_length)
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(new_content)
    print(f"Processed {markdown_file} with {model} - All code blocks wrapped.")

if __name__ == "__main__":
    main()