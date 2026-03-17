#!/usr/bin/env python3
"""
Migration script: populates the SOLVE-IT-X AI Applicability extension from
the solve-it-ai-applications BibTeX source.

For each technique:
  1. Creates category subfolders (app-env, ac-idea, ac-imp, in-tool, non-ai)
  2. Copies raw .bib files into the appropriate subfolders
  3. Writes extension_data.json with metadata only (reviewed_name, renamed, unassessed)

Also detects renamed techniques by comparing SOLVE-IT repo git history.
"""

import argparse
import json
import logging
import os
import shutil
import subprocess
import sys
import tempfile

# The original review covered T1001-T1105 (mapped to DFT-1001 through DFT-1105)
REVIEWED_MIN = 1001
REVIEWED_MAX = 1105

# SOLVE-IT repo commit closest to the review date (April 2025)
REVIEW_ERA_COMMIT = "c8143a6ef4121334d412a28213baa1b4614160c3"

SOLVE_IT_REPO_URL = "https://github.com/SOLVE-IT-DF/solve-it.git"

CATEGORY_DIRS = ["app-env", "ac-idea", "ac-imp", "in-tool", "non-ai"]

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_technique_names_at_commit(repo_path, commit_hash):
    """Read technique names from a specific commit of the SOLVE-IT repo."""
    names = {}
    try:
        result = subprocess.run(
            ["git", "ls-tree", "--name-only", commit_hash, "data/techniques/"],
            capture_output=True, text=True, cwd=repo_path, check=True,
        )
        for line in result.stdout.strip().split("\n"):
            if not line.endswith(".json"):
                continue
            t_id = os.path.basename(line).replace(".json", "")
            file_result = subprocess.run(
                ["git", "show", f"{commit_hash}:{line}"],
                capture_output=True, text=True, cwd=repo_path, check=True,
            )
            try:
                data = json.loads(file_result.stdout)
                names[t_id] = data.get("name", "")
            except json.JSONDecodeError:
                logger.warning("Could not parse JSON for %s at commit %s", t_id, commit_hash[:8])
    except subprocess.CalledProcessError as e:
        logger.error("Git command failed: %s", e)
    return names


def clone_solve_it_repo():
    """Clone the SOLVE-IT repo to a temp directory and return the path."""
    tmp_dir = tempfile.mkdtemp(prefix="solve-it-migrate-")
    repo_path = os.path.join(tmp_dir, "solve-it")
    logger.info("Cloning SOLVE-IT repo to %s ...", repo_path)
    subprocess.run(
        ["git", "clone", "--quiet", SOLVE_IT_REPO_URL, repo_path],
        check=True,
    )
    return repo_path


def main():
    parser = argparse.ArgumentParser(
        description="Migrate BibTeX AI applicability data to SOLVE-IT-X extension format"
    )
    parser.add_argument(
        "--source", required=True,
        help="Path to solve-it-ai-applications/data directory"
    )
    parser.add_argument(
        "--target", required=True,
        help="Path to ai_applicability_data/techniques directory"
    )
    parser.add_argument(
        "--solve-it-repo", default=None,
        help="Path to existing SOLVE-IT repo clone (will clone if not provided)"
    )
    args = parser.parse_args()

    if not os.path.isdir(args.source):
        logger.error("Source directory does not exist: %s", args.source)
        sys.exit(1)
    if not os.path.isdir(args.target):
        logger.error("Target directory does not exist: %s", args.target)
        sys.exit(1)

    # Step 1: Clone or use existing SOLVE-IT repo for rename detection
    if args.solve_it_repo:
        repo_path = args.solve_it_repo
    else:
        repo_path = clone_solve_it_repo()

    logger.info("Reading technique names at review-era commit (%s) ...", REVIEW_ERA_COMMIT[:8])
    historical_names = get_technique_names_at_commit(repo_path, REVIEW_ERA_COMMIT)
    logger.info("Found %d techniques at review-era commit", len(historical_names))

    logger.info("Reading technique names at current HEAD ...")
    current_names = get_technique_names_at_commit(repo_path, "HEAD")
    logger.info("Found %d techniques at current HEAD", len(current_names))

    # Step 2: Build a map of source .bib files per technique/category
    # Source structure: data/T1001/ac-idea/1.bib
    source_files = {}  # { "DFT-1001": { "ac-idea": ["/path/to/1.bib", ...], ... } }
    for dir_name in sorted(os.listdir(args.source)):
        dir_path = os.path.join(args.source, dir_name)
        if not os.path.isdir(dir_path) or dir_name == "T1000" or not dir_name.startswith("T"):
            continue
        dft_id = f"DFT-{dir_name[1:]}"
        source_files[dft_id] = {}
        for cat_dir in CATEGORY_DIRS:
            cat_path = os.path.join(dir_path, cat_dir)
            bib_files = []
            if os.path.isdir(cat_path):
                for f in sorted(os.listdir(cat_path)):
                    if f.endswith(".bib"):
                        bib_files.append(os.path.join(cat_path, f))
            source_files[dft_id][cat_dir] = bib_files

    # Step 3: Process each technique folder in the target
    stats = {"assessed": 0, "unassessed": 0, "bib_copied": 0}

    for dir_name in sorted(os.listdir(args.target)):
        dir_path = os.path.join(args.target, dir_name)
        if not os.path.isdir(dir_path) or not dir_name.startswith("DFT-"):
            continue

        t_num = int(dir_name.split("-")[1])

        # Create category subfolders for all techniques
        for cat_dir in CATEGORY_DIRS:
            os.makedirs(os.path.join(dir_path, cat_dir), exist_ok=True)

        # Write extension_data.json (metadata only)
        output_path = os.path.join(dir_path, "extension_data.json")

        if t_num > REVIEWED_MAX or t_num < REVIEWED_MIN:
            ext_data = {"assessments": []}
            stats["unassessed"] += 1
        else:
            ext_data = {
                "assessments": [
                    {"date": "2025-04-03", "by": "Chris Hargreaves"}
                ]
            }
            stats["assessed"] += 1

        with open(output_path, "w") as f:
            json.dump(ext_data, f, indent=4)

        # Copy .bib files from source into category subfolders
        if dir_name in source_files:
            for cat_dir, bib_paths in source_files[dir_name].items():
                dest_cat = os.path.join(dir_path, cat_dir)
                for bib_path in bib_paths:
                    dest_file = os.path.join(dest_cat, os.path.basename(bib_path))
                    shutil.copy2(bib_path, dest_file)
                    stats["bib_copied"] += 1

    # Summary
    logger.info("")
    logger.info("=== Migration Summary ===")
    logger.info("BibTeX files copied: %d", stats["bib_copied"])
    logger.info("Techniques assessed (original review): %d", stats["assessed"])
    logger.info("Techniques unassessed (new): %d", stats["unassessed"])


if __name__ == "__main__":
    main()
