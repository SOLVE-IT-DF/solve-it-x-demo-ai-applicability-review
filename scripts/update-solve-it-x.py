#!/usr/bin/env python3
"""
Update script for solve-it-x extensions

This script updates an existing extension folder by:
- Fetching the current list of techniques, weaknesses, and mitigations from SOLVE-IT repo
- Comparing with existing folders
- Creating only new folders that don't exist yet
- Preserving all existing data and extension_code.py

Usage:
    python3 update-solve-it-x.py --path /path/to/extension
"""
import argparse
import sys
import json
import urllib.request
from pathlib import Path


def update_extension(folder_path):
    """
    Updates an extension folder by creating folders for new techniques/weaknesses/mitigations
    without touching any existing data.

    Args:
        folder_path: Path to the existing extension folder
    """
    target_folder = Path(folder_path)

    # Verify the folder exists
    if not target_folder.exists():
        print(f"[ERROR] Extension folder does not exist: {folder_path}")
        print(f"Use init-solve-it-x.py to create a new extension first.")
        sys.exit(1)

    # Verify extension_code.py exists (sanity check this is an extension folder)
    extension_code_file = target_folder / "extension_code.py"
    if not extension_code_file.exists():
        print(f"[WARNING] extension_code.py not found in {folder_path}")
        print(f"This may not be a valid extension folder.")
        response = input("Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Aborted.")
            sys.exit(0)

    print(f"Updating extension at: {folder_path}\n")

    # Fetch IDs from the SOLVE-IT GitHub repository
    print("Fetching latest data from SOLVE-IT repository...")

    repo_api_base = "https://api.github.com/repos/SOLVE-IT-DF/solve-it/contents/data"
    categories = ["techniques", "weaknesses", "mitigations"]

    # Track statistics and proposed changes
    total_existing = 0
    proposed_changes = {}  # category -> list of new items

    # First pass: collect all proposed changes without making any modifications
    for category_name in categories:
        print(f"\n{'='*60}")
        print(f"Analyzing {category_name}...")
        print(f"{'='*60}")

        # Get or create the category subfolder
        category_folder = target_folder / category_name

        # Get list of existing folders
        existing_folders = set()
        if category_folder.exists():
            existing_folders = {
                item.name for item in category_folder.iterdir()
                if item.is_dir()
            }

        try:
            # Fetch the directory listing from GitHub API
            api_url = f"{repo_api_base}/{category_name}"
            req = urllib.request.Request(api_url)
            req.add_header('User-Agent', 'solve-it-x-update-script')

            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode())

            # Filter for directories (JSON files in SOLVE-IT repo)
            # Each technique/weakness/mitigation has a corresponding .json file
            item_ids = []
            for item in data:
                if item['type'] == 'file' and item['name'].endswith('.json'):
                    # Extract ID from filename (e.g., T1001.json -> T1001)
                    item_id = item['name'].replace('.json', '')
                    item_ids.append(item_id)

            # Separate new and existing items
            new_items = []
            for item_id in sorted(item_ids):
                if item_id not in existing_folders:
                    new_items.append(item_id)

            # Store results
            existing_count = len(item_ids) - len(new_items)
            total_existing += existing_count
            proposed_changes[category_name] = new_items

            print(f"  Existing folders: {existing_count}")
            print(f"  New items found: {len(new_items)}")

        except Exception as e:
            print(f"  [ERROR] Could not fetch {category_name} from repository: {e}")
            print(f"  Skipping {category_name}")
            proposed_changes[category_name] = []

    # Display proposed changes summary
    total_new = sum(len(items) for items in proposed_changes.values())

    print(f"\n{'='*60}")
    print("PROPOSED CHANGES")
    print(f"{'='*60}")

    if total_new == 0:
        print("\n[INFO] No new folders to add. Extension is already up to date!")
        print(f"\nExtension location: {folder_path}")
        return

    print(f"\nThe following {total_new} new folders will be created:\n")

    for category_name, new_items in proposed_changes.items():
        if new_items:
            print(f"{category_name.upper()}:")
            for item_id in new_items:
                print(f"  - {item_id}")
            print()

    # Ask for user confirmation
    print(f"{'='*60}")
    response = input(f"Proceed with creating {total_new} new folders? (yes/no): ").strip().lower()

    if response not in ['yes', 'y']:
        print("\n[CANCELLED] Update cancelled by user.")
        sys.exit(0)

    # Second pass: actually create the folders
    print(f"\n{'='*60}")
    print("Creating folders...")
    print(f"{'='*60}\n")

    total_added = 0
    for category_name, new_items in proposed_changes.items():
        if new_items:
            category_folder = target_folder / category_name
            category_folder.mkdir(parents=True, exist_ok=True)

            for item_id in new_items:
                item_folder = category_folder / item_id
                item_folder.mkdir(parents=True, exist_ok=True)

            total_added += len(new_items)
            print(f"  Created {len(new_items)} folders in {category_name}/")


    # Final summary
    print(f"\n{'='*60}")
    print("Update Summary")
    print(f"{'='*60}")
    print(f"Total existing folders: {total_existing}")
    print(f"Total new folders added: {total_added}")

    if total_added == 0:
        print("\n[SUCCESS] Extension is already up to date!")
    else:
        print(f"\n[SUCCESS] Added {total_added} new folders to extension")

    print(f"\nExtension location: {folder_path}")


def main():
    parser = argparse.ArgumentParser(
        description='Update an existing solve-it-x extension with new techniques/weaknesses/mitigations'
    )

    parser.add_argument(
        '--path',
        type=str,
        required=True,
        help='Path to the existing extension folder to update'
    )

    args = parser.parse_args()

    update_extension(args.path)


if __name__ == '__main__':
    main()
