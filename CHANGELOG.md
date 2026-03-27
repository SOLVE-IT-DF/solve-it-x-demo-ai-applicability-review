# Changelog

## 2026-03-27

### Data format changes

- **Separated notes from BibTeX citations**: AI relevance descriptions are now stored in `.json` files (with a `notes` field) alongside `.bib` citation files, rather than embedded as `note` fields within BibTeX entries. This cleanly separates the "why is AI relevant" description from the formal citation.
- **Reclassified "Application Envisaged" entries**: All 24 techniques previously classified as "Application Envisaged" have been reclassified to "Academic Idea" since they were suggested in Hargreaves et al. (2025). The original descriptive notes for each technique have been preserved.  That category has now been removed. The four remaining categories are: In Tools, Academic Implementation, Academic Idea, and Non-AI.

### Features

- **Copy citation buttons**: Each reference entry now includes clipboard copy buttons for both plaintext (Harvard-style) citation and raw BibTeX.

### Housekeeping

- Renamed `examples/` folder to `extensions/` for consistency with SOLVE-IT-X conventions.
- Updated all scripts and GitHub Actions workflows to use the `extensions/` path.
- Removed the one-time `migrate_bibtex_to_json.py` migration script (migration from the original repository is complete).
- Removed `.txt` file format from documentation (`.json` + `.bib` is now the documented format).
- Updated README with improved structure, correct prerequisites, and clearer explanation of the Non-AI vs Unassessed distinction.

## 2026-03-26

- Added link to GitHub Pages HTML version in README.

## 2026-03-19

- Fixed compatibility with new JSON weakness format in SOLVE-IT.

## 2026-03-18

- Updated internal folder structure to mirror other SOLVE-IT-X examples.

## 2026-03-17

- Initial commit: migrated AI applicability data from the [original BibTeX-based repository](https://github.com/SOLVE-IT-DF/solve-it-applications-ai-review) into the SOLVE-IT-X extension format.
- Includes assessment data for DFT-1001 through DFT-1105, covering 50 technique entries across four categories.
- Build script, HTML viewer, and standalone report generation.
- GitHub Actions workflows for automated builds and SOLVE-IT sync.
