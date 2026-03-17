#!/usr/bin/env python3
# This script:

# - examines the current solve-it repo and looks at the total techniques, weaknesses and mitigations
# - creates a folder structure mirroring that set,
# - copies the relevant scripts to that initialised folder
"""
Setup script for solve-it-x extensions
"""
import argparse
import sys
import shutil
import json
import urllib.request
from pathlib import Path


def setup_extensions_base_folder(folder_path, include_extension=None):
    """
    Sets up the extensions base folder by:
    - Creating the folder if it doesn't exist
    - Copying extension_config_template.json to extension_config.json
    - Optionally initializing a named extension if include_extension is provided
    """
    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    template_path = script_dir / "extension_config_template.json"

    # Create the target folder
    target_folder = Path(folder_path)
    target_folder.mkdir(parents=True, exist_ok=True)

    # Copy template to extension_config.json
    target_config_file = target_folder / "extension_config.json"
    shutil.copy2(template_path, target_config_file)
    print(f"Copied extension_config_template.json to {target_config_file}")

    # Copy default global_solveit_config.py
    global_config_template = script_dir.parent / "examples" / "global_solveit_config.py"
    if global_config_template.exists():
        target_global_config = target_folder / "global_solveit_config.py"
        shutil.copy2(global_config_template, target_global_config)
        print(f"Copied default global_solveit_config.py to {target_global_config}")

    # If include_extension is provided, create that extension folder and initialize it
    if include_extension:
        extension_folder = target_folder / include_extension
        extension_folder.mkdir(parents=True, exist_ok=True)
        print(f"Created extension folder: {extension_folder}")
        print(f"Initializing extension: {include_extension}")
        init_extension(str(extension_folder))

        # Update extension_config.json to register the new extension
        print(f"Registering extension in extension_config.json...")
        with open(target_config_file, 'r') as f:
            config = json.load(f)

        # Add the extension to the extensions field
        if "extensions" not in config:
            config["extensions"] = {}

        config["extensions"][include_extension] = {
            "folder_path": include_extension,
            "description": f"Extension: {include_extension}"
        }

        # Write the updated config back
        with open(target_config_file, 'w') as f:
            json.dump(config, f, indent=4)

        print(f"  Registered '{include_extension}' in extension_config.json")

    print(f"\nSuccessfully set up extensions base folder at: {folder_path}")

def init_extension(folder_path):
    """
    Initializes an extension folder by:
    - Copying extension_code_template.py to extension_code.py
    - Creating techniques, weaknesses, and mitigations subfolders
    - Creating folders for each ID from the online SOLVE-IT repo
    """
    target_folder = Path(folder_path)
    target_folder.mkdir(parents=True, exist_ok=True)

    # Get the directory where this script is located
    script_dir = Path(__file__).parent
    template_path = script_dir / "extension_code_template.py"

    # Copy template to extension_code.py
    target_code_file = target_folder / "extension_code.py"
    shutil.copy2(template_path, target_code_file)
    print(f"Copied extension_code_template.py to {target_code_file}")

    # Fetch IDs from the SOLVE-IT GitHub repository
    print("Fetching data from SOLVE-IT repository...")

    repo_api_base = "https://api.github.com/repos/SOLVE-IT-DF/solve-it/contents/data"

    categories = ["techniques", "weaknesses", "mitigations"]

    for category_name in categories:
        print(f"Processing {category_name}...")

        # Create the category subfolder
        category_folder = target_folder / category_name
        category_folder.mkdir(parents=True, exist_ok=True)

        try:
            # Fetch the directory listing from GitHub API
            api_url = f"{repo_api_base}/{category_name}"
            req = urllib.request.Request(api_url)
            req.add_header('User-Agent', 'solve-it-x-init-script')

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

            # Create folders for each ID
            for item_id in sorted(item_ids):
                item_folder = category_folder / item_id
                item_folder.mkdir(parents=True, exist_ok=True)

            print(f"  Created {len(item_ids)} {category_name} folders")

        except Exception as e:
            print(f"  Warning: Could not fetch {category_name} from repository: {e}")
            print(f"  Creating empty {category_name} folder")

    print(f"\nSuccessfully initialized extension at: {folder_path}")
    

def main():
    parser = argparse.ArgumentParser(
        description='Setup script for solve-it-x extensions'
    )

    # Create a mutually exclusive group for the action flags
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        '--setup-extensions-base-folder',
        action='store_true',
        help='Setup the extensions base folder in the supplied folder path'
    )
    action_group.add_argument(
        '--init-extension',
        action='store_true',
        help='Initialize a new extension in the supplied folder path'
    )

    # Path argument required for both actions
    parser.add_argument(
        '--path',
        type=str,
        required=True,
        help='Path for the setup operation'
    )

    # Optional argument to include a basic extension during setup
    parser.add_argument(
        '--include-extension',
        type=str,
        help='Name of extension to create and initialize (only used with --setup-extensions-base-folder)'
    )

    args = parser.parse_args()

    if args.setup_extensions_base_folder:
        setup_extensions_base_folder(args.path, include_extension=args.include_extension)

    elif args.init_extension:
        init_extension(args.path)


if __name__ == '__main__':
    main()
