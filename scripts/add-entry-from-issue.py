#!/usr/bin/env python3
"""
Parse a GitHub issue form submission and write AI applicability entry files.

Reads ISSUE_BODY and ISSUE_NUMBER from environment variables (set by the
GitHub Actions workflow). Writes .json and .bib files to the appropriate
technique/category folder, and outputs metadata for the workflow to create
a branch and PR.

Exit codes:
    0 - success, files written
    1 - validation error
"""

import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

from pybtex.database import parse_string
from pybtex.scanner import TokenRequired

TECHNIQUES_DIR = Path(__file__).parent.parent / "extensions" / "ai_applicability_data" / "techniques"

CATEGORY_LABEL_TO_DIR = {
    "In Tools": "in-tool",
    "Academic Implementation": "ac-imp",
    "Academic Idea": "ac-idea",
    "Non-AI": "non-ai",
}

CATEGORY_DIRS = list(CATEGORY_LABEL_TO_DIR.values())


def parse_issue_body(body):
    """Parse GitHub issue form body into a dict keyed by field label."""
    sections = {}
    current_header = None
    current_lines = []
    for line in body.splitlines():
        if line.startswith("### "):
            if current_header is not None:
                sections[current_header] = "\n".join(current_lines).strip()
            current_header = line[4:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    if current_header is not None:
        sections[current_header] = "\n".join(current_lines).strip()

    # Normalise empty optional fields
    for key in sections:
        if sections[key] == "_No response_":
            sections[key] = ""

    return sections


def strip_code_fences(text):
    """Remove markdown code fences that GitHub adds around rendered fields."""
    text = text.strip()
    # Remove opening fence (```bibtex or ```)
    text = re.sub(r"^```\w*\n?", "", text)
    # Remove closing fence
    text = re.sub(r"\n?```$", "", text)
    return text.strip()


def validate_technique_id(technique_id):
    """Check format and existence of a technique ID."""
    if not re.match(r"^DFT-\d{4}$", technique_id):
        return f"Invalid technique ID format: '{technique_id}'. Expected DFT-XXXX (e.g. DFT-1001)."
    if not (TECHNIQUES_DIR / technique_id).is_dir():
        return f"Technique folder not found for {technique_id}."
    return None


def validate_bibtex(bibtex_str):
    """Parse BibTeX and return (parsed_data, error_message)."""
    try:
        bib_data = parse_string(bibtex_str, bib_format="bibtex")
        if not bib_data.entries:
            return None, "BibTeX parsed but contains no entries."
        return bib_data, None
    except (TokenRequired, Exception) as e:
        return None, f"Failed to parse BibTeX: {e}"


def extract_title(bib_data):
    """Extract the title from parsed pybtex data."""
    for key in bib_data.entries:
        return bib_data.entries[key].fields.get("title", "")
    return ""


def normalise_for_comparison(text):
    """Lowercase and collapse whitespace for fuzzy matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def find_duplicate_bibtex(submitted_title):
    """Scan all .bib files and return matches by title."""
    if not submitted_title:
        return []

    target = normalise_for_comparison(submitted_title)
    duplicates = []

    for bib_path in TECHNIQUES_DIR.rglob("*.bib"):
        try:
            bib_data = parse_string(bib_path.read_text(encoding="utf-8"), bib_format="bibtex")
        except Exception:
            continue
        for key in bib_data.entries:
            title = bib_data.entries[key].fields.get("title", "")
            if normalise_for_comparison(title) == target:
                # Extract technique and category from path
                rel = bib_path.relative_to(TECHNIQUES_DIR)
                duplicates.append(str(rel))
    return duplicates


def next_entry_number(category_dir):
    """Determine the next sequential entry number in a category folder."""
    existing = []
    if category_dir.is_dir():
        for f in category_dir.iterdir():
            if f.stem.isdigit():
                existing.append(int(f.stem))
    return max(existing, default=0) + 1


def set_output(name, value):
    """Write a GitHub Actions output variable."""
    output_file = os.environ.get("GITHUB_OUTPUT")
    if output_file:
        with open(output_file, "a") as f:
            if "\n" in value:
                f.write(f"{name}<<EOF\n{value}\nEOF\n")
            else:
                f.write(f"{name}={value}\n")


def fail(message):
    """Report a validation error and exit."""
    print(f"ERROR: {message}", file=sys.stderr)
    set_output("error", message)
    sys.exit(1)


def main():
    body = os.environ.get("ISSUE_BODY", "")
    issue_number = os.environ.get("ISSUE_NUMBER", "0")

    if not body:
        fail("Issue body is empty.")

    fields = parse_issue_body(body)

    # --- Extract and validate fields ---

    technique_id = fields.get("Technique ID", "").strip()
    if not technique_id:
        fail("Technique ID is missing.")
    error = validate_technique_id(technique_id)
    if error:
        fail(error)

    category_label = fields.get("Category", "").strip()
    category_dir_name = CATEGORY_LABEL_TO_DIR.get(category_label)
    if not category_dir_name:
        fail(f"Invalid category: '{category_label}'. Expected one of: {', '.join(CATEGORY_LABEL_TO_DIR.keys())}.")

    notes = fields.get("Notes", "").strip()
    if not notes:
        fail("Notes field is empty.")

    bibtex_raw = strip_code_fences(fields.get("BibTeX Entry", ""))
    if not bibtex_raw:
        fail("BibTeX Entry is missing.")

    # Validate BibTeX
    bib_data, bib_error = validate_bibtex(bibtex_raw)
    if bib_error:
        fail(bib_error)

    # --- Duplicate detection ---

    duplicate_warning = ""
    if bib_data:
        submitted_title = extract_title(bib_data)
        duplicates = find_duplicate_bibtex(submitted_title)
        if duplicates:
            dup_list = "\n".join(f"- `{d}`" for d in duplicates)
            duplicate_warning = f"**Possible duplicate(s) detected:**\n{dup_list}"

    # --- Write files ---

    category_dir = TECHNIQUES_DIR / technique_id / category_dir_name
    category_dir.mkdir(parents=True, exist_ok=True)

    entry_num = next_entry_number(category_dir)

    repo_root = TECHNIQUES_DIR.parent.parent.parent

    json_path = category_dir / f"{entry_num}.json"
    json_path.write_text(json.dumps({"notes": notes}, indent=4) + "\n")

    bib_path = category_dir / f"{entry_num}.bib"
    bib_path.write_text(bibtex_raw + "\n")

    files_created = [
        str(json_path.relative_to(repo_root)),
        str(bib_path.relative_to(repo_root)),
    ]

    # --- Record assessment ---

    github_username = os.environ.get("ISSUE_AUTHOR", "")
    display_name = ""
    if github_username:
        try:
            result = subprocess.run(
                ["gh", "api", f"/users/{github_username}", "--jq", ".name"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0 and result.stdout.strip():
                display_name = result.stdout.strip()
        except Exception:
            pass

    assessment = {"date": date.today().isoformat(), "by": display_name or github_username}
    if github_username:
        assessment["github"] = github_username

    ext_path = TECHNIQUES_DIR / technique_id / "extension_data.json"
    if ext_path.exists():
        ext_data = json.loads(ext_path.read_text())
    else:
        ext_data = {}
    assessments = ext_data.get("assessments", [])
    assessments.append(assessment)
    ext_data["assessments"] = assessments
    ext_path.write_text(json.dumps(ext_data, indent=4) + "\n")
    files_created.append(str(ext_path.relative_to(repo_root)))

    # --- Outputs ---

    branch_name = f"add-entry/{technique_id}-{category_dir_name}-{entry_num}"
    pr_title = f"Add {category_label} entry #{entry_num} for {technique_id}"

    pr_body_lines = [
        f"## Summary",
        f"",
        f"Adds a new **{category_label}** entry (#{entry_num}) for **{technique_id}**.",
        f"",
        f"Closes #{issue_number}",
        f"",
        f"### Notes",
        f"",
        notes,
        f"",
        f"### Files created",
        f"",
    ]
    for f in files_created:
        pr_body_lines.append(f"- `{f}`")

    pr_body_lines += ["", "### BibTeX", "", "```bibtex", bibtex_raw, "```"]

    if duplicate_warning:
        pr_body_lines += ["", "---", "", duplicate_warning]

    pr_body = "\n".join(pr_body_lines)

    # Write PR body to file for gh pr create --body-file
    Path("/tmp/pr-body.md").write_text(pr_body)

    set_output("branch_name", branch_name)
    set_output("pr_title", pr_title)
    set_output("files_created", " ".join(files_created))
    set_output("duplicate_warning", duplicate_warning)

    print(f"Entry #{entry_num} written to {category_dir}")
    for f in files_created:
        print(f"  {f}")
    if duplicate_warning:
        print(f"\nWARNING: {duplicate_warning}")


if __name__ == "__main__":
    main()
