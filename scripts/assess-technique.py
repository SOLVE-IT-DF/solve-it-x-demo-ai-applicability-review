#!/usr/bin/env python3
"""
Record an assessment for one or more techniques.

Usage:
    python3 scripts/assess-technique.py DFT-1171
    python3 scripts/assess-technique.py DFT-1171 DFT-1172 --by "Chris Hargreaves"
    python3 scripts/assess-technique.py DFT-1001 --by "Jane Smith" --date 2026-02-15

Adds an entry to the assessments list in extension_data.json and ensures
category subfolders exist.
"""

import argparse
from datetime import date
import json
import sys
from pathlib import Path

CATEGORY_DIRS = ["ac-idea", "ac-imp", "in-tool", "non-ai"]
DEFAULT_TECHNIQUES_DIR = Path(__file__).parent.parent / "extensions" / "ai_applicability_data" / "techniques"


def assess_technique(t_id, techniques_dir, assessor, assessment_date):
    """Add an assessment entry to a technique."""
    technique_dir = techniques_dir / t_id

    if not technique_dir.is_dir():
        print(f"  [ERROR] Folder not found: {technique_dir}")
        return False

    # Ensure category subfolders exist
    for cat in CATEGORY_DIRS:
        (technique_dir / cat).mkdir(exist_ok=True)

    # Read existing metadata
    ext_path = technique_dir / "extension_data.json"
    if ext_path.exists():
        existing = json.loads(ext_path.read_text())
    else:
        existing = {}

    # Get or create assessments list
    assessments = existing.get("assessments", [])

    # Add new assessment
    entry = {"date": assessment_date, "by": assessor}
    assessments.append(entry)

    new_data = {"assessments": assessments}
    ext_path.write_text(json.dumps(new_data, indent=4) + "\n")

    by_str = f" by {assessor}" if assessor else ""
    prev_count = len(assessments) - 1
    print(f"  {t_id}: recorded assessment{by_str} ({assessment_date}) [{prev_count} previous]")
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Record an assessment for one or more techniques"
    )
    parser.add_argument(
        "technique_ids",
        nargs="+",
        metavar="DFT-XXXX",
        help="One or more technique IDs to assess"
    )
    parser.add_argument(
        "--by",
        default="",
        help="Name of the assessor"
    )
    parser.add_argument(
        "--date",
        default=None,
        help="Assessment date in ISO format (default: today)"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_TECHNIQUES_DIR,
        help=f"Path to the techniques directory (default: {DEFAULT_TECHNIQUES_DIR})"
    )
    args = parser.parse_args()

    assessment_date = args.date or date.today().isoformat()

    count = 0
    for t_id in args.technique_ids:
        if assess_technique(t_id, args.path, args.by, assessment_date):
            count += 1

    print(f"\nUpdated {count} technique(s).")


if __name__ == "__main__":
    main()
