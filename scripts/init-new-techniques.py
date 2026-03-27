#!/usr/bin/env python3
"""
Initialise new technique folders for the AI Applicability Review extension.

Scans the techniques directory for folders that are missing extension_data.json
or category subfolders, and populates them with the standard structure:

  DFT-XXXX/
    extension_data.json       # {"unassessed": true}
    ac-idea/
    ac-imp/
    in-tool/
    non-ai/

Run this after update-solve-it-x.py to prepare newly added techniques.

Usage:
    python3 scripts/init-new-techniques.py
    python3 scripts/init-new-techniques.py --path ./extensions/ai_applicability_data/techniques
"""

import argparse
import json
from pathlib import Path

CATEGORY_DIRS = ["ac-idea", "ac-imp", "in-tool", "non-ai"]

DEFAULT_PATH = Path(__file__).parent.parent / "extensions" / "ai_applicability_data" / "techniques"


def init_technique(technique_dir):
    """Ensure a technique folder has extension_data.json and category subfolders."""
    created = []

    # Create category subfolders
    for cat in CATEGORY_DIRS:
        cat_dir = technique_dir / cat
        if not cat_dir.exists():
            cat_dir.mkdir(parents=True)
            created.append(cat)

    # Create extension_data.json if missing
    ext_json = technique_dir / "extension_data.json"
    if not ext_json.exists():
        ext_json.write_text(json.dumps({"assessments": []}, indent=4) + "\n")
        created.append("extension_data.json")

    return created


def main():
    parser = argparse.ArgumentParser(
        description="Initialise new technique folders with extension_data.json and category subfolders"
    )
    parser.add_argument(
        "--path",
        type=Path,
        default=DEFAULT_PATH,
        help=f"Path to the techniques directory (default: {DEFAULT_PATH})"
    )
    args = parser.parse_args()

    techniques_dir = args.path
    if not techniques_dir.is_dir():
        print(f"[ERROR] Directory not found: {techniques_dir}")
        raise SystemExit(1)

    initialised = 0
    for item in sorted(techniques_dir.iterdir()):
        if not item.is_dir() or not item.name.startswith("DFT-"):
            continue

        created = init_technique(item)
        if created:
            print(f"  {item.name}: created {', '.join(created)}")
            initialised += 1

    if initialised == 0:
        print("All technique folders are already initialised.")
    else:
        print(f"\nInitialised {initialised} technique(s).")


if __name__ == "__main__":
    main()
