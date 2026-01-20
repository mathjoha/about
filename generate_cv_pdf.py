#!/usr/bin/env python3
"""
Generate a PDF-ready QMD file from CV data.

This script reads the CV data (YAML files and QMD frontmatter) and generates
a flat QMD file that can be rendered to PDF with Quarto.

Usage:
    python3 generate_cv_pdf.py
    quarto render cv_for_pdf.qmd --to pdf
"""

import re
from datetime import date
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

ROOT_DIR = Path(__file__).parent
CV_DIR = ROOT_DIR / "cv"
PUB_DIR = ROOT_DIR / "pub"
CODE_DIR = ROOT_DIR / "code"
OUTPUT_FILE = ROOT_DIR / "cv_for_pdf.qmd"


def simple_yaml_parse_list(content: str) -> list:
    """Parse a simple YAML list of dicts (no nesting beyond multiline strings)."""
    items = []
    current_item = {}
    current_key = None
    current_value_lines = []
    in_multiline = False

    for line in content.split("\n"):
        # New item starts with "- key:"
        if line.startswith("- "):
            if current_item:
                if current_key and current_value_lines:
                    current_item[current_key] = "\n".join(current_value_lines).strip()
                items.append(current_item)
            current_item = {}
            current_key = None
            current_value_lines = []
            in_multiline = False
            # Parse first key of new item
            rest = line[2:]
            if ":" in rest:
                key, _, val = rest.partition(":")
                key = key.strip()
                val = val.strip()
                if val == "|":
                    current_key = key
                    current_value_lines = []
                    in_multiline = True
                elif val.startswith('"') and val.endswith('"'):
                    current_item[key] = val[1:-1]
                elif val.startswith("'") and val.endswith("'"):
                    current_item[key] = val[1:-1]
                else:
                    current_item[key] = val
        elif in_multiline and (line.startswith("    ") or line.strip() == ""):
            current_value_lines.append(line[4:] if line.startswith("    ") else "")
        elif line.startswith("  ") and ":" in line:
            # Save previous multiline if any
            if current_key and current_value_lines:
                current_item[current_key] = "\n".join(current_value_lines).strip()
                current_key = None
                current_value_lines = []
                in_multiline = False
            # Regular key: value
            rest = line[2:]
            key, _, val = rest.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "|":
                current_key = key
                current_value_lines = []
                in_multiline = True
            elif val.startswith('"') and val.endswith('"'):
                current_item[key] = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                current_item[key] = val[1:-1]
            else:
                current_item[key] = val

    # Don't forget last item
    if current_item:
        if current_key and current_value_lines:
            current_item[current_key] = "\n".join(current_value_lines).strip()
        items.append(current_item)

    return items


def simple_yaml_parse_dict(content: str) -> dict:
    """Parse simple YAML dict from QMD frontmatter."""
    result = {}
    current_key = None
    current_value_lines = []
    in_multiline = False

    for line in content.split("\n"):
        if in_multiline:
            if line.startswith("    ") or line.strip() == "":
                current_value_lines.append(line[4:] if line.startswith("    ") else "")
                continue
            else:
                result[current_key] = "\n".join(current_value_lines).strip()
                current_key = None
                current_value_lines = []
                in_multiline = False

        if ":" in line and not line.startswith(" "):
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip()
            if val == "|":
                current_key = key
                current_value_lines = []
                in_multiline = True
            elif val.startswith('"') and val.endswith('"'):
                result[key] = val[1:-1]
            elif val.startswith("'") and val.endswith("'"):
                result[key] = val[1:-1]
            else:
                result[key] = val

    if current_key and current_value_lines:
        result[current_key] = "\n".join(current_value_lines).strip()

    return result


def parse_qmd_frontmatter(filepath: Path) -> dict:
    """Extract YAML frontmatter from a QMD file."""
    content = filepath.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if match:
        fm_content = match.group(1)
        if yaml:
            return yaml.safe_load(fm_content)
        return simple_yaml_parse_dict(fm_content)
    return {}


def load_yaml(filepath: Path) -> list:
    """Load a YAML file."""
    content = filepath.read_text(encoding="utf-8")
    if yaml:
        return yaml.safe_load(content)
    return simple_yaml_parse_list(content)


def clean_title(title: str) -> str:
    """Remove HTML links and Quarto shortcodes from titles."""
    # Remove HTML links: <a href="...">text</a> -> text
    title = re.sub(r'<a[^>]*>([^<]*)</a>', r'\1', title)
    # Remove Quarto shortcodes: {{< ... >}}
    title = re.sub(r'\{\{<[^>]+>\}\}', '', title)
    # Remove markdown links: [text](url) -> text
    title = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', title)
    return title.strip()


def clean_html(text: str) -> str:
    """Remove HTML tags from text."""
    if not text:
        return ""
    text = re.sub(r'<a[^>]*>([^<]*)</a>', r'\1', text)
    text = re.sub(r'<[^>]+>', '', text)
    return text.strip()


def format_experience(items: list) -> str:
    """Format experience entries."""
    lines = ["## Experience\n"]
    for item in items:
        title = item.get("title", "")
        employer = item.get("employer", "")
        department = item.get("department", "")
        start = item.get("start", "")
        end = item.get("end", "")
        desc = clean_html(item.get("desc", ""))

        lines.append(f"**{title}**\\")
        lines.append(f"{employer}, {department}\\")
        lines.append(f"*{start} – {end}*")
        if desc:
            lines.append(f"\\")
            lines.append(desc)
        lines.append("")
    return "\n".join(lines)


def format_education(items: list) -> str:
    """Format education entries."""
    # Sort by sort-order, then start desc
    items = sorted(items, key=lambda x: (x.get("sort-order", 99), -int(x.get("start", "0"))))

    lines = ["## Education\n"]
    for item in items:
        title = item.get("title", "")
        level = item.get("level", "")
        school = item.get("school", "")
        department = item.get("department", "")
        start = item.get("start", "")
        end = item.get("end", "")
        item_type = clean_html(item.get("type", ""))

        lines.append(f"**{title}**\\")
        if level and item_type:
            lines.append(f"*{level} {item_type}*\\")
        lines.append(f"{school}, {department}\\")
        lines.append(f"*{start} – {end}*")
        lines.append("")
    return "\n".join(lines)


def format_teaching(items: list) -> str:
    """Format teaching entries."""
    # Sort by year desc
    items = sorted(items, key=lambda x: -int(x.get("year", 0)))

    lines = ["## Teaching\n"]
    for item in items:
        title = item.get("title", "").strip()
        year = item.get("year", "")
        level = item.get("level", "")
        school = item.get("School", "")
        subtitle = item.get("subtitle", "").strip()

        lines.append(f"**{title} ({year})**\\")
        lines.append(f"{school} – {level}")
        if subtitle:
            # Clean up markdown links for PDF
            subtitle = re.sub(r'\[([^\]]+)\]\([^)]+\)', r'\1', subtitle)
            lines.append(f"\\")
            lines.append(subtitle)
        lines.append("")
    return "\n".join(lines)


def format_projects(project_dir: Path) -> str:
    """Format project entries from QMD files."""
    lines = ["## Projects\n"]

    projects = []
    for qmd_file in project_dir.glob("*.qmd"):
        fm = parse_qmd_frontmatter(qmd_file)
        if fm:
            projects.append(fm)

    # Sort by active desc, start asc
    projects = sorted(projects, key=lambda x: (-float(x.get("active", 0) or 0), x.get("start", "")))

    for item in projects:
        title = clean_title(item.get("title", ""))
        start = item.get("start", "")
        end = item.get("end", "")
        abstract = item.get("abstract", "").strip()
        university = item.get("university", "")

        lines.append(f"**{title}**\\")
        lines.append(f"{university}, {start} – {end}")
        if abstract:
            # Take first paragraph only for brevity
            first_para = abstract.split("\n\n")[0]
            lines.append(f"\\")
            lines.append(first_para)
        lines.append("")
    return "\n".join(lines)


def format_publications(pub_dir: Path) -> str:
    """Format publication entries from QMD files."""
    lines = ["## Publications\n"]

    pubs = []
    for qmd_file in pub_dir.glob("*.qmd"):
        fm = parse_qmd_frontmatter(qmd_file)
        if fm:
            pubs.append(fm)

    # Sort by date desc
    pubs = sorted(pubs, key=lambda x: x.get("date", ""), reverse=True)

    for item in pubs:
        title = clean_title(item.get("title", ""))
        subtitle = item.get("subtitle", "").strip()
        pub_type = item.get("Type", "")
        pub_date = item.get("date", "")
        author = item.get("author", "")
        journal = item.get("Journal", "")
        doi = item.get("doi", "")

        # Clean author formatting
        author = re.sub(r'\*\*<u>([^<]+)</u>\*\*', r'**\1**', author)

        if subtitle:
            lines.append(f"**{title} {subtitle}**\\")
        else:
            lines.append(f"**{title}**\\")
        if author:
            lines.append(f"{author}\\")
        meta_parts = []
        if pub_type:
            meta_parts.append(pub_type)
        if journal and journal != "N/A":
            meta_parts.append(journal)
        if pub_date:
            meta_parts.append(pub_date)
        if meta_parts:
            lines.append(f"*{', '.join(meta_parts)}*")
        if doi:
            lines.append(f"\\")
            lines.append(f"DOI: {doi}")
        lines.append("")
    return "\n".join(lines)


def format_datasets(dataset_dir: Path) -> str:
    """Format dataset entries from QMD files."""
    lines = ["## Datasets\n"]

    datasets = []
    for qmd_file in dataset_dir.glob("*.qmd"):
        fm = parse_qmd_frontmatter(qmd_file)
        if fm:
            datasets.append(fm)

    # Sort by date desc
    datasets = sorted(datasets, key=lambda x: x.get("date", ""), reverse=True)

    for item in datasets:
        title = clean_title(item.get("title", ""))
        ds_type = item.get("Type", "")
        ds_date = item.get("date", "")
        doi = item.get("doi", "")
        url = item.get("url", "")

        lines.append(f"**{title}**\\")
        meta_parts = []
        if ds_type:
            meta_parts.append(ds_type)
        if ds_date:
            meta_parts.append(ds_date)
        if meta_parts:
            lines.append(f"*{', '.join(meta_parts)}*")
        if doi:
            lines.append(f"\\")
            lines.append(f"DOI: {doi}")
        elif url:
            lines.append(f"\\")
            lines.append(f"URL: {url}")
        lines.append("")
    return "\n".join(lines)


def format_code(code_dir: Path) -> str:
    """Format code/software entries from QMD files."""
    lines = ["## Software & Code\n"]

    repos = []
    for qmd_file in code_dir.glob("*.qmd"):
        fm = parse_qmd_frontmatter(qmd_file)
        if fm:
            repos.append(fm)

    # Sort by date desc
    repos = sorted(repos, key=lambda x: x.get("date", ""), reverse=True)

    for item in repos:
        title = clean_title(item.get("title", ""))
        repo_type = item.get("Type", "")
        repo_date = item.get("date", "")
        abstract = item.get("abstract", "").strip()
        repo_url = item.get("repo", "")
        url = item.get("url", "")

        lines.append(f"**{title}**\\")
        meta_parts = []
        if repo_type:
            meta_parts.append(repo_type)
        if repo_date:
            meta_parts.append(repo_date)
        if meta_parts:
            lines.append(f"*{', '.join(meta_parts)}*")
        if abstract:
            first_para = abstract.split("\n\n")[0]
            lines.append(f"\\")
            lines.append(first_para)
        if repo_url:
            lines.append(f"\\")
            lines.append(f"Repository: {repo_url}")
        lines.append("")
    return "\n".join(lines)


def generate_qmd():
    """Generate the PDF-ready QMD file."""
    today = date.today().strftime("%Y-%m-%d")

    frontmatter = f'''---
format:
  pdf:
    documentclass: article
    papersize: a4
    fontsize: 10pt
    mainfont: "Times New Roman"
    geometry:
      - margin=2.5cm
    header-includes: |
      \\usepackage{{titlesec}}
      \\titleformat{{\\section}}{{\\normalfont\\fontsize{{14}}{{16}}\\bfseries}}{{\\thesection}}{{1em}}{{}}
      \\titlespacing{{\\section}}{{0pt}}{{2ex plus 0.5ex minus 0.2ex}}{{1ex plus 0.2ex}}
      \\setlength{{\\parskip}}{{0.5ex}}
      \\usepackage{{fancyhdr}}
      \\pagestyle{{fancy}}
      \\fancyhf{{}}
      \\fancyhead[L]{{Mathias Johansson -- Systems Developer}}
      \\fancyhead[C]{{CV}}
      \\fancyhead[R]{{{today}}}
      \\fancyfoot[L]{{mathjoha.se}}
      \\fancyfoot[R]{{\\thepage}}
      \\renewcommand{{\\headrulewidth}}{{0.4pt}}
      \\renewcommand{{\\footrulewidth}}{{0.4pt}}
      \\fancypagestyle{{plain}}{{
        \\fancyhf{{}}
        \\fancyhead[L]{{Mathias Johansson -- Systems Developer}}
        \\fancyhead[C]{{CV}}
        \\fancyhead[R]{{{today}}}
        \\fancyfoot[L]{{mathjoha.se}}
        \\fancyfoot[R]{{\\thepage}}
        \\renewcommand{{\\headrulewidth}}{{0.4pt}}
        \\renewcommand{{\\footrulewidth}}{{0.4pt}}
      }}
---

'''

    contact_info = """::: {layout="[75,25]" layout-valign="top"}

::: {}
[mathjoha.se](https://mathjoha.se)\\
[mathiasjoha@gmail.com](mailto:mathiasjoha@gmail.com)\\
[github.com/mathjoha](https://github.com/mathjoha)\\
[linkedin.com/MathiasJoha](https://linkedin.com/MathiasJoha)\\
[orcid.org/0000-0002-3338-0551](https://orcid.org/0000-0002-3338-0551)\\
[portal.research.lu.se/en/persons/mathias-johansson](https://portal.research.lu.se/en/persons/mathias-johansson)\\
[pypi.org/user/MathiasJoha](https://pypi.org/user/MathiasJoha/)
:::

![](mathjoha.se.qr.png){width=100%}

:::

"""

    sections = [contact_info]

    # Experience
    exp_file = CV_DIR / "experience.yaml"
    if exp_file.exists():
        sections.append(format_experience(load_yaml(exp_file)))

    # Projects
    project_dir = CV_DIR / "project"
    if project_dir.exists():
        sections.append(format_projects(project_dir))

    # Education
    edu_file = CV_DIR / "education.yaml"
    if edu_file.exists():
        sections.append(format_education(load_yaml(edu_file)))

    # Publications
    if PUB_DIR.exists():
        sections.append(format_publications(PUB_DIR))

    # Teaching
    teaching_file = CV_DIR / "teaching.yaml"
    if teaching_file.exists():
        sections.append(format_teaching(load_yaml(teaching_file)))

    # Software & Code
    if CODE_DIR.exists():
        sections.append(format_code(CODE_DIR))

    # Datasets
    dataset_dir = CV_DIR / "dataset"
    if dataset_dir.exists():
        sections.append(format_datasets(dataset_dir))

    content = frontmatter + "\n".join(sections)

    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"Generated: {OUTPUT_FILE}")
    print(f"To render PDF: quarto render {OUTPUT_FILE.name} --to pdf")


if __name__ == "__main__":
    generate_qmd()
