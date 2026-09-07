#!/usr/bin/env python3
"""
Generate a PDF-ready QMD file listing all scholarly outputs.

Aggregates Publications, Datasets, Software & Code, and Presentations into a
flat QMD file that Quarto can render to PDF. Reuses the parsers and section
formatters from generate_cv_pdf.py.

Usage:
    python3 generate_outputs_pdf.py
    quarto render outputs_for_pdf.qmd --to pdf --output Outputs_MJ.latest.pdf
"""

from datetime import date
from pathlib import Path

from generate_cv_pdf import (
    CODE_DIR,
    CV_DIR,
    PUB_DIR,
    contact_block,
    format_code,
    format_datasets,
    format_presentations,
    format_publications,
    load_yaml,
    pdf_frontmatter,
)

ROOT_DIR = Path(__file__).parent
OUTPUT_FILE = ROOT_DIR / "outputs_for_pdf.qmd"


def generate_qmd():
    today = date.today().strftime("%Y-%m-%d")

    sections = [contact_block()]

    if PUB_DIR.exists():
        sections.append(format_publications(PUB_DIR))

    dataset_dir = CV_DIR / "dataset"
    if dataset_dir.exists():
        sections.append(format_datasets(dataset_dir))

    if CODE_DIR.exists():
        sections.append(format_code(CODE_DIR))

    pres_file = CV_DIR / "presentations.yaml"
    if pres_file.exists():
        sections.append(format_presentations(load_yaml(pres_file)))

    content = pdf_frontmatter("Outputs", today) + "\n".join(sections)
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Generated: {OUTPUT_FILE}")
    print(f"To render PDF: quarto render {OUTPUT_FILE.name} --to pdf --output Outputs_MJ.latest.pdf")


if __name__ == "__main__":
    generate_qmd()
