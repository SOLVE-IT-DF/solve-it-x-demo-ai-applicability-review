# SOLVE-IT-X: AI Applicability Review

A [SOLVE-IT-X](https://github.com/SOLVE-IT-DF/solve-it-x) extension that overlays an **AI applicability review** onto the [SOLVE-IT](https://github.com/SOLVE-IT-DF/solve-it) digital forensic knowledge base.

For each SOLVE-IT technique, the review records whether AI has been applied (or could be applied), categorised by maturity level:

| Category | Description |
|----------|-------------|
| **In Tools** | AI capability already integrated into forensic tools |
| **Academic Implementation** | Published academic work with a working implementation |
| **Academic Idea** | Proposed in academic literature but not yet implemented |
| **Application Envisioned** | Potential AI application identified but not yet explored |

Each entry includes the AI relevance note and, where applicable, a supporting citation.

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

## Adding or updating entries

Each technique folder contains category subfolders where you can drop citation files:

```
examples/ai_applicability_data/techniques/
  DFT-1001/
    extension_data.json   # assessment history
    ac-idea/
      1.bib               # BibTeX entry
    ac-imp/
    app-env/
    in-tool/
    non-ai/
```

Two file formats are supported:

### BibTeX (`.bib`)

Standard BibTeX with a `note` field containing the AI relevance description:

```bibtex
@inproceedings{du2020sok,
  title={SoK: Exploring the state of the art and the future potential of AI in digital forensic investigation},
  author={Du, Xiaoyu and Hargreaves, Chris and Sheppard, John and others},
  booktitle={Proceedings of the 15th ARES conference},
  pages={1--10},
  year={2020},
  note="Identifying the most relevant devices from a set could potentially be improved with AI"
}
```

### Plaintext (`.txt`)

A lightweight alternative -- the note on the first line(s), optionally followed by `---` and a Harvard-style reference:

```
Perhaps speaker identification could be improved with AI
---
Smith, J. and Jones, A., 2024. Automated forensic triage using machine learning. Digital Investigation, 45, pp.301-315.
```

If no reference is needed, just the note text is sufficient:

```
Perhaps detection of AI generated speech
```

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

Requires Python 3 and `pybtex` (`pip install pybtex`). Using a virtual environment is recommended:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 build_solve-it-x.py
```

This clones the main SOLVE-IT repo, copies in the extension data, reads all `.bib`/`.txt` files from category subfolders at build time, generates the HTML viewer and report, and places both in `docs/`.

The included GitHub Actions workflow (`build.yml`) builds automatically on push to main.

## Repository structure

```
examples/
  extension_config.json                   # Extension registration and field visibility
  ai_applicability_data/
    extension_code.py                     # Rendering logic (HTML, Markdown, Excel)
    global_solveit_config.py              # Status labels, colours, and title
    techniques/
      DFT-1001/
        extension_data.json               # Assessment history
        ac-idea/1.bib                     # AI applicability entries as .bib or .txt
        ac-imp/
        app-env/
        in-tool/
        non-ai/
      DFT-1002/
        ...
    weaknesses/                           # Standard SOLVE-IT-X structure (no data)
    mitigations/                          # Standard SOLVE-IT-X structure (no data)
scripts/
  assess-technique.py                    # Record an assessment for a technique
  init-new-techniques.py                 # Populate new technique folders with subfolders
  init-solve-it-x.py                     # Scaffold new extensions
  update-solve-it-x.py                   # Add folders for newly added SOLVE-IT entries
  migrate_bibtex_to_json.py              # One-time migration from the original BibTeX source
build_solve-it-x.py                      # Main build orchestration
docs/
  index.html                             # Generated interactive viewer
  ai-applicability-report.html           # Generated standalone report
```

## Migration from the original source

The original AI applicability data was maintained as BibTeX files in [solve-it-ai-applications](https://github.com/SOLVE-IT-DF/solve-it-ai-applications). The migration script copies those `.bib` files into the category subfolders and generates metadata in `extension_data.json`:

```bash
python3 scripts/migrate_bibtex_to_json.py \
    --source /path/to/solve-it-ai-applications/data \
    --target ./examples/ai_applicability_data/techniques
```

## Updating when SOLVE-IT adds new techniques

```bash
# 1. Create empty folders for any new SOLVE-IT entries
python3 scripts/update-solve-it-x.py --path examples/ai_applicability_data

# 2. Initialise them with extension_data.json and category subfolders
python3 scripts/init-new-techniques.py
```

The first command creates folders for any techniques added since the extension was last updated. The second populates them with empty assessment metadata and the category subfolders so they're ready to receive entries.
