#!/usr/bin/env python3
"""
This script demonstrates how the data from a SOLVE-IT-X extension can be integrated with the main knowledge base.

This script:
1. Clones the solve-it repository (main branch)
2. Installs any required dependencies from the cloned repository's requirements.txt
3. Copies extension data (extension folders and extension_config.json) into the extension_data folder
4. Runs the report generation scripts (markdown, Excel, and HTML) and puts the reports in an output folder.
"""

import json
import os
import shutil
import subprocess
import sys
import argparse
from pathlib import Path


def clone_solve_it_repo(target_dir="solve-it-clone"):
    """
    Clone the solve-it repository (main branch).

    Args:
        target_dir: Directory name for the cloned repository

    Returns:
        Path to the cloned repository
    """
    print("=" * 60)
    print("Step 1: Cloning solve-it repository (main branch)")
    print("=" * 60)

    repo_url = "https://github.com/SOLVE-IT-DF/solve-it.git"
    target_path = Path(target_dir).resolve()

    # Check if directory already exists
    if target_path.exists():
        print("=" * 60)
        print(f"[ERROR] Directory '{target_dir}' already exists.")
        print(f"Please remove it before running again.")
        print("=" * 60)
        sys.exit(1)

    # Clone the repository
    print(f"Cloning {repo_url} into {target_dir}...")
    try:
        subprocess.run(
            ["git", "clone", repo_url, str(target_path)],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"[SUCCESS] Successfully cloned repository to: {target_path}")
        return target_path
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Error cloning repository: {e}")
        print(f"stderr: {e.stderr}")
        sys.exit(-1)


def install_dependencies(solve_it_path):
    """
    Install required dependencies from the cloned repository's requirements.txt.

    Args:
        solve_it_path: Path to the cloned solve-it repository
    """
    print("=" * 60)
    print("Step 2: Checking and installing dependencies")
    print("=" * 60)

    requirements_file = solve_it_path / "requirements.txt"

    if not requirements_file.exists():
        print("No requirements.txt found in cloned repository, skipping.")
        return

    print(f"Installing dependencies from: {requirements_file}")
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_file)],
            check=True,
            stdin=subprocess.DEVNULL
        )
        print("[SUCCESS] Dependencies installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to install dependencies (exit code: {e.returncode})")
        sys.exit(1)


def copy_extension_data(solve_it_path, extension_path="examples", config_file=None):
    """
    Copy all extension data (extension folders and extension_config.json) into the solve-it extension_data folder.

    Args:
        solve_it_path: Path to the cloned solve-it repository
        extension_path: Path to the extension folder (default: "examples")
        config_file: Optional path to an alternative extension_config.json to use

    Returns:
        Path to the destination extension_data folder
    """
    print("=" * 60)
    print("Step 3: Copying extension data")
    print("=" * 60)

    # Resolve the extension base path
    script_dir = Path(__file__).parent.resolve()
    if os.path.isabs(extension_path):
        source_dir = Path(extension_path).resolve()
    else:
        source_dir = script_dir / extension_path

    # Target is extension_data in the cloned repo
    dest_dir = solve_it_path / "extension_data"

    # Verify source exists
    if not source_dir.exists():
        print(f"[ERROR] Error: Source directory not found: {source_dir}")
        sys.exit(1)

    print(f"Source: {source_dir}")
    print(f"Destination: {dest_dir}")

    # Create extension_data directory if it doesn't exist
    if not dest_dir.exists():
        print(f"Creating extension_data directory: {dest_dir}")
        dest_dir.mkdir(parents=True, exist_ok=True)

    # Copy all contents from source to destination
    try:
        print(f"Copying extension data contents...")
        for item in source_dir.iterdir():
            dest_item = dest_dir / item.name

            # Remove existing item if it exists
            if dest_item.exists():
                if dest_item.is_dir():
                    shutil.rmtree(dest_item)
                else:
                    dest_item.unlink()

            # Copy the item
            if item.is_dir():
                shutil.copytree(item, dest_item)
                print(f"  Copied folder: {item.name}")
            else:
                shutil.copy2(item, dest_item)
                print(f"  Copied file: {item.name}")

        # Override extension_config.json if an alternative was specified
        if config_file:
            script_dir = Path(__file__).parent.resolve()
            if os.path.isabs(config_file):
                config_source = Path(config_file).resolve()
            else:
                config_source = script_dir / config_file

            if not config_source.exists():
                print(f"[ERROR] Config file not found: {config_source}")
                sys.exit(1)

            dest_config = dest_dir / "extension_config.json"
            shutil.copy2(config_source, dest_config)
            print(f"  Overriding extension_config.json with: {config_source}")

        # Check extension_config.json for a custom global_config setting
        dest_config = dest_dir / "extension_config.json"
        if dest_config.exists():
            with open(dest_config) as f:
                ext_config = json.load(f)
            global_config_name = ext_config.get("global_config")
            if global_config_name:
                global_config_source = source_dir / global_config_name
                if not global_config_source.exists():
                    print(f"[ERROR] Global config file not found: {global_config_source}")
                    sys.exit(1)
                dest_global_config = dest_dir / "global_solveit_config.py"
                shutil.copy2(global_config_source, dest_global_config)
                print(f"  Using global config: {global_config_name}")

        print(f"[SUCCESS] Successfully copied extension data to: {dest_dir}")
        return dest_dir
    except Exception as e:
        print(f"[ERROR] Error copying files: {e}")
        sys.exit(1)


def generate_markdown_output(solve_it_path):
    """
    Run generate_md_from_kb.py to generate markdown output.

    Args:
        solve_it_path: Path to the cloned solve-it repository

    Returns:
        Path to the generated markdown file
    """
    print("=" * 60)
    print("Step 6: Generating markdown output")
    print("=" * 60)

    # Path to the script
    script_path = solve_it_path / "reporting_scripts" / "generate_md_from_kb.py"

    # Verify script exists
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        sys.exit(1)

    print(f"Running: {script_path}")
    print(f"Working directory: {solve_it_path}")

    # Run the script from the solve-it root directory
    # Use sys.executable to ensure we use the same Python interpreter
    try:
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(solve_it_path),
            check=True,
            stdin=subprocess.DEVNULL
        )

        # The default output is in solve-it/output/solve-it.md
        output_file = solve_it_path / "output" / "solve-it.md"
        print(f"[SUCCESS] Markdown generated at: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Error generating markdown (exit code: {e.returncode})")
        sys.exit(1)


def generate_excel_output(solve_it_path):
    """
    Run generate_excel_from_kb.py to generate Excel output.

    Args:
        solve_it_path: Path to the cloned solve-it repository

    Returns:
        Path to the generated Excel file
    """
    print("=" * 60)
    print("Step 7: Generating Excel output")
    print("=" * 60)

    # Path to the script
    script_path = solve_it_path / "reporting_scripts" / "generate_excel_from_kb.py"

    # Verify script exists
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        sys.exit(1)

    print(f"Running: {script_path}")
    print(f"Working directory: {solve_it_path}")

    # Run the script from the solve-it root directory
    # Use sys.executable to ensure we use the same Python interpreter
    try:
        subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(solve_it_path),
            check=True,
            stdin=subprocess.DEVNULL
        )

        # The default output is in solve-it/output/solve-it.xlsx
        output_file = solve_it_path / "output" / "solve-it.xlsx"
        print(f"[SUCCESS] Excel generated at: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Error generating Excel (exit code: {e.returncode})")
        sys.exit(1)


def generate_html_output(solve_it_path):
    """
    Run generate_html_from_kb.py to generate HTML output.

    Args:
        solve_it_path: Path to the cloned solve-it repository

    Returns:
        Path to the generated HTML file
    """
    print("=" * 60)
    print("Step 4: Generating HTML output")
    print("=" * 60)

    # Path to the script
    script_path = solve_it_path / "reporting_scripts" / "generate_html_from_kb.py"

    # Verify script exists
    if not script_path.exists():
        print(f"[ERROR] Script not found: {script_path}")
        sys.exit(1)

    print(f"Running: {script_path}")
    print(f"Working directory: {solve_it_path}")

    # Run the script from the solve-it root directory, outputting to the output folder
    output_dir = solve_it_path / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "solveit-viewer.html"
    try:
        subprocess.run(
            [sys.executable, str(script_path), "--custom", "--output", str(output_file)],
            cwd=str(solve_it_path),
            check=True,
            stdin=subprocess.DEVNULL
        )
        print(f"[SUCCESS] HTML generated at: {output_file}")
        return output_file
    except subprocess.CalledProcessError as e:
        print(f"\n[ERROR] Error generating HTML (exit code: {e.returncode})")
        sys.exit(1)


def copy_html_to_docs(html_file):
    """
    Copy the generated HTML file to a docs folder for GitHub Pages serving.

    Args:
        html_file: Path to the generated HTML file

    Returns:
        Path to the copied HTML file in the docs folder
    """
    print("=" * 60)
    print("Step 5: Copying HTML to docs folder for GitHub Pages")
    print("=" * 60)

    script_dir = Path(__file__).parent.resolve()
    docs_dir = script_dir / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)

    dest_file = docs_dir / "index.html"
    shutil.copy2(html_file, dest_file)
    print(f"[SUCCESS] Copied HTML to: {dest_file}")
    return dest_file


def main():
    """Main execution function."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Run SOLVE-IT-X demo with custom or example extensions'
    )
    parser.add_argument(
        'extension_path',
        nargs='?',
        default='examples',
        help='Path to extension folder containing demo_extension_data and extension_config.json (default: examples)'
    )
    parser.add_argument(
        '--config',
        default=None,
        help='Path to an alternative extension_config.json (overrides the one in extension_path)'
    )
    args = parser.parse_args()

    print("\n[START] Starting solve-it-x demo setup\n")
    print(f"Using extension path: {args.extension_path}")
    if args.config:
        print(f"Using config override: {args.config}")
    print()

    # Step 1: Clone the repository
    solve_it_path = clone_solve_it_repo()
    print(f"\n[SUCCESS] Step 1 complete. Repository at: {solve_it_path}\n")

    # Step 2: Install dependencies
    install_dependencies(solve_it_path)
    print(f"\n[SUCCESS] Step 2 complete. Dependencies installed.\n")

    # Step 3: Copy extension data
    extension_data_path = copy_extension_data(solve_it_path, args.extension_path, args.config)
    print(f"\n[SUCCESS] Step 3 complete. Extension data copied to: {extension_data_path}\n")

    # # Step 6 (optional): Generate markdown output
    # markdown_file = generate_markdown_output(solve_it_path)
    # print(f"\n[SUCCESS] Step 6 complete. Markdown output at: {markdown_file}\n")

    # # Step 7 (optional): Generate Excel output
    # excel_file = generate_excel_output(solve_it_path)
    # print(f"\n[SUCCESS] Step 7 complete. Excel output at: {excel_file}\n")

    # Step 4: Generate HTML output
    html_file = generate_html_output(solve_it_path)
    print(f"\n[SUCCESS] Step 4 complete. HTML output at: {html_file}\n")

    # Step 5: Copy HTML to docs folder for GitHub Pages
    docs_file = copy_html_to_docs(html_file)
    print(f"\n[SUCCESS] Step 5 complete. HTML copied to: {docs_file}\n")

    print("\n[SUCCESS] Demo setup complete!\n")
    print(f"Repository location: {solve_it_path}")
    print(f"HTML output: {html_file}")
    print(f"GitHub Pages: {docs_file}")


if __name__ == "__main__":
    main()

