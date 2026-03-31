# SOLVE-IT-X: AI Applicability Review

## Introduction
This is a [SOLVE-IT-X](https://github.com/SOLVE-IT-DF/solve-it-x) extension that overlays an **AI applicability review** onto the [SOLVE-IT](https://github.com/SOLVE-IT-DF/solve-it) digital forensic knowledge base.


This replaced the [original repository](https://github.com/SOLVE-IT-DF/solve-it-applications-ai-review) based on the work in:


```Hargreaves, C., van Beek, H., Casey, E., SOLVE-IT: A proposed digital forensic knowledge base inspired by MITRE ATT&CK, Forensic Science International: Digital Investigation, Volume 52, Supplement, 2025, 301864, ISSN 2666-2817, https://doi.org/10.1016/j.fsidi.2025.301864```


The HTML version of this SOLVE-IT-X extension is available [here](https://solve-it-df.github.io/solve-it-x-demo-ai-applicability-review/).

## Content

For each SOLVE-IT technique, the review records whether AI has been applied (or could be applied), categorised by maturity level:

| Category | Description |
|----------|-------------|
| **In Tools** | AI capability already integrated into forensic tools |
| **Academic Implementation** | Published academic work with a working implementation |
| **Academic Idea** | Proposed in academic literature but not yet implemented |
| **Non-AI** | Assessed and determined that a non-AI-based process is likely sufficient |

Each entry includes the AI relevance note and, where applicable, a supporting citation.

Note the distinction between **Non-AI** and **Unassessed**: a Non-AI classification means someone has explicitly reviewed the technique and concluded AI is not needed, whereas an unassessed technique simply has not been reviewed yet.

## Outputs

The build produces two outputs in the `docs/` folder:

- **`index.html`** -- interactive SOLVE-IT matrix viewer with AI applicability badges on each technique, colour-coded status filters, and detail panels
- **`ai-applicability-report.html`** -- standalone report organised by investigative objective, listing every technique with its AI applicability entries and full references (linked from the viewer via the "Full Report" button)

## Review status

Techniques are colour-coded based on the date of their most recent assessment:

- **Recently assessed** (green) -- assessed within the last 3 months
- **Previously assessed** (blue) -- assessed more than 3 months ago
- **Unassessed** (grey) -- no assessment recorded

Assessment history (who assessed, when) is displayed in each technique's detail panel.

## Data format

Each technique's `extension_data.json` tracks assessment history:

```json
{
    "assessments": [
        {"date": "2025-04", "by": "Initial review"},
        {"date": "2026-03-17", "by": "Chris Hargreaves"}
    ]
}
```

Unassessed techniques have an empty list: `{"assessments": []}`.

## Adding entries via GitHub Issues

The easiest way to add a new entry is through the GitHub issue form:

1. Click the **+ Add entry** button on any technique in the [HTML viewer](https://solve-it-df.github.io/solve-it-x-demo-ai-applicability-review/), or [open a new issue](https://github.com/SOLVE-IT-DF/solve-it-x-demo-ai-applicability-review/issues/new?template=add-ai-entry.yml) directly
2. Fill in the technique ID, category, BibTeX citation, and notes
3. Add the **ai-entry** label to the issue
4. A GitHub Actions workflow will automatically validate the submission, check for duplicate references, write the entry files, record an assessment, and open a pull request

The PR includes a summary of the entry, the BibTeX citation, and any duplicate warnings for review before merging.

## Adding or updating entries manually

Each technique folder contains category subfolders where you can drop citation files:

```
extensions/ai_applicability_data/techniques/
  DFT-1001/
    extension_data.json   # assessment history
    ac-idea/
      1.json              # AI relevance description
      1.bib               # BibTeX citation (optional)
    ac-imp/
    in-tool/
    non-ai/
```

Two file formats are supported:

### JSON description (`.json`) + BibTeX citation (`.bib`)

The preferred format uses a pair of files with the same stem. The `.json` file contains the AI relevance description and the `.bib` file contains the citation:

**`1.json`**
```json
{
    "notes": "Identifying the most relevant devices from a set could potentially be improved with AI"
}
```

**`1.bib`**
```bibtex
@inproceedings{du2020sok,
  title={SoK: Exploring the state of the art and the future potential of AI in digital forensic investigation},
  author={Du, Xiaoyu and Hargreaves, Chris and Sheppard, John and others},
  booktitle={Proceedings of the 15th ARES conference},
  pages={1--10},
  year={2020}
}
```

A standalone `.json` file (no matching `.bib`) is also valid when there is no formal citation.

After adding files, rebuild to see the changes.

### Recording an assessment

Use the helper script to record who assessed a technique and when:

```bash
# Assess a technique (uses today's date)
python3 scripts/assess-technique.py DFT-1171 --by "Chris Hargreaves"

# Assess multiple techniques at once
python3 scripts/assess-technique.py DFT-1171 DFT-1172 DFT-1173 --by "Chris Hargreaves"

# Specify a custom date
python3 scripts/assess-technique.py DFT-1001 --by "Jane Smith" --date 2026-02-15
```

Or edit `extension_data.json` directly -- just append to the `assessments` list:

```json
{
    "assessments": [
        {"date": "2025-04", "by": "Initial review"},
        {"date": "2026-03-17", "by": "Chris Hargreaves"}
    ]
}
```

## Building

Requires Python 3, pip, and git. The build script handles all other dependencies automatically (it clones the main SOLVE-IT repo and installs its requirements via pip).

```bash
python3 build_solve-it-x.py
```

This clones the main SOLVE-IT repo, copies in the extension data, reads all `.json`/`.bib` files from category subfolders at build time, generates the HTML viewer and report, and places both in `docs/`.

The included GitHub Actions workflow (`build.yml`) builds automatically on push to main. A separate workflow (`add-entry.yml`) handles automated entry creation from GitHub issues.

## Repository structure

```
extensions/
  extension_config.json                   # Extension registration and field visibility
  ai_applicability_data/
    extension_code.py                     # Rendering logic (HTML, Markdown, Excel)
    global_solveit_config.py              # Status labels, colours, and title
    techniques/
      DFT-1001/
        extension_data.json               # Assessment history
        ac-idea/1.json                    # AI relevance description
        ac-idea/1.bib                     # BibTeX citation (paired with .json)
        ac-imp/
        in-tool/
        non-ai/
      DFT-1002/
        ...
    weaknesses/                           # Standard SOLVE-IT-X structure (no data)
    mitigations/                          # Standard SOLVE-IT-X structure (no data)
scripts/
  add-entry-from-issue.py                # Parse issue form and write entry files
  assess-technique.py                    # Record an assessment for a technique
  init-new-techniques.py                 # Populate new technique folders with subfolders
  init-solve-it-x.py                     # Scaffold new extensions
  update-solve-it-x.py                   # Add folders for newly added SOLVE-IT entries
build_solve-it-x.py                      # Main build orchestration
docs/
  index.html                             # Generated interactive viewer
  ai-applicability-report.html           # Generated standalone report
```

## Updating when SOLVE-IT adds new techniques

```bash
# 1. Create empty folders for any new SOLVE-IT entries
python3 scripts/update-solve-it-x.py --path extensions/ai_applicability_data

# 2. Initialise them with extension_data.json and category subfolders
python3 scripts/init-new-techniques.py
```

The first command creates folders for any techniques added since the extension was last updated. The second populates them with empty assessment metadata and the category subfolders so they're ready to receive entries.
