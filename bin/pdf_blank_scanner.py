#!/usr/bin/env python3

import sys
import click
from pdf2image import convert_from_path
from PIL import Image
import os
import numpy as np

# --- Core Logic ---


def analyze_page_image(image_path: str, max_noise_percent: float) -> bool:
    """
    Analyzes an image to determine if it is mostly blank based on a noise threshold.
    """
    try:
        # Open the image and convert it to grayscale
        img = Image.open(image_path).convert("L")
        img_array = np.array(img)

        # Pixels below a value of 250 are considered "content" or "noise" (out of 255).
        content_pixels = np.sum(img_array < 250)

        total_pixels = img_array.size
        content_percent = (content_pixels / total_pixels) * 100

        is_blank = content_percent <= max_noise_percent

        # Clean up the temporary image file
        os.remove(image_path)

        return is_blank

    except Exception as e:
        click.echo(f"Error analyzing image {image_path}: {e}", err=True)
        return False


def generate_html_report(pdf_file_path: str, blank_pages: list):
    """
    Generates an HTML file with clickable links to jump to specific pages in the PDF.
    """
    base_name = os.path.splitext(os.path.basename(pdf_file_path))[0]
    html_report_path = f"{base_name}_blank_pages_report.html"

    # Use URL encoding for the file path to handle spaces
    pdf_uri = "file://" + os.path.abspath(pdf_file_path).replace(os.path.sep, "/")

    # HTML content template
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Blank Page Scan Report for {base_name}</title>
        <style>
            body {{ font-family: sans-serif; line-height: 1.6; margin: 2em; }}
            h1 {{ border-bottom: 2px solid #ccc; padding-bottom: 0.5em; }}
            .pages a {{ 
                margin: 0.25em; 
                padding: 0.5em 1em; 
                background-color: #f0f0f0; 
                border: 1px solid #ddd; 
                text-decoration: none;
                color: #007bff;
                display: inline-block;
            }}
            .pages a:hover {{ background-color: #e9ecef; }}
        </style>
    </head>
    <body>
        <h1>Blank Page Scan Report</h1>
        <p><strong>PDF File:</strong> {pdf_file_path}</p>
        <p><strong>Found {len(blank_pages)} Mostly Blank Pages.</strong></p>
        <h2>Clickable Page List:</h2>
        <div class="pages">
    """

    # Add clickable links for each page
    for page_num in blank_pages:
        # Standard PDF viewer link syntax to open to a specific page: #page=[number]
        link = f"{pdf_uri}#page={page_num}"
        html_content += (
            f'            <a href="{link}" target="_blank">Page {page_num}</a>\n'
        )

    html_content += """
        </div>
        <p style="margin-top: 2em;">NOTE: Links use standard PDF fragment identifiers (e.g., #page=X). Compatibility depends on your browser and PDF viewer settings.</p>
    </body>
    </html>
    """

    # Write the content to the HTML file
    with open(html_report_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    return html_report_path


# --- Click Command ---


@click.command()
@click.argument("pdf_file", type=click.Path(exists=True))
@click.option(
    "--max-noise",
    "-m",
    type=click.FloatRange(0.0, 100.0),
    default=0.25,
    show_default=True,
    help=(
        "Maximum percentage of non-blank (non-white) space allowed for a page to be considered blank. "
        "A page is flagged as blank if its content percentage is less than or equal to this threshold."
        "\n\n"
        "Suggested values:"
        "\n  - 0.0: Strict blank (no content whatsoever)."
        "\n  - 0.1 - 0.5: Recommended range to find pages containing only *minor* elements like page numbers, headers, or footers."
        "\n  - 1.0+: Will start flagging pages with very little body text as blank."
    ),
)
@click.option(
    "--create-report",
    "-r",
    is_flag=True,
    help="Generate an HTML file with clickable links to jump directly to the blank pages in your PDF viewer.",
)
def scan_pdf_for_blanks(pdf_file, max_noise, create_report):
    """
    Scans a PDF file to find pages that have less than the configured
    percentage of non-blank content (noise/text/images).
    """
    click.echo(f"Scanning PDF: {pdf_file}")
    click.echo(f"Maximum allowed content (noise) percentage: {max_noise}%")

    blank_pages = []
    temp_dir = "pdf_scan_temp_images"

    try:
        # 1. Create a temporary directory for images
        os.makedirs(temp_dir, exist_ok=True)

        # 2. Convert PDF pages to images
        click.echo("Converting pages to images for analysis...")
        images = convert_from_path(
            pdf_file, dpi=100, output_folder=temp_dir, fmt="jpeg", paths_only=True
        )

        # 3. Analyze each image
        click.echo("Analyzing images...")
        for i, image_path in enumerate(images):
            page_number = i - 3 # adjust for frontmatter
            is_blank = analyze_page_image(image_path, max_noise)

            if is_blank:
                blank_pages.append(page_number)
                # Only echo individual pages if not creating a report (to keep terminal clean)
                if not create_report:
                    click.echo(f"Found mostly blank page: {page_number}")

        # 4. Final Output
        click.echo("\n" + "=" * 30)
        if blank_pages:
            click.echo(f"RESULTS: {len(blank_pages)} Mostly Blank Pages Found.")

            if create_report:
                report_file = generate_html_report(pdf_file, blank_pages)
                click.echo(
                    f"Open the following file for clickable links: {report_file}"
                )
            else:
                click.echo("Page Numbers: " + ", ".join(map(str, blank_pages)))
        else:
            click.echo("RESULTS: No mostly blank pages found.")
        click.echo("=" * 30)

    except Exception as e:
        click.echo(f"\nAn error occurred during processing: {e}", err=True)
        sys.exit(1)

    finally:
        # 5. Clean up the temporary directory
        try:
            if os.path.exists(temp_dir):
                if not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
                else:
                    click.echo(
                        f"Warning: Temporary files remain in {temp_dir}. Please delete manually.",
                        err=True,
                    )
        except Exception as e:
            click.echo(f"Cleanup error: {e}", err=True)

    # --- Script Exit ---
    sys.exit(0)


if __name__ == "__main__":
    scan_pdf_for_blanks()
