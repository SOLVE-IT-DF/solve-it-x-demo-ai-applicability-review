import logging
import subprocess
import sys
from datetime import date, timedelta
from html import escape
from pathlib import Path

from pybtex.database.input import bibtex
from pybtex.scanner import TokenRequired

# This should add the SOLVE-IT library path if any extension needs to make use of it
solve_it_root = Path(__file__).parent.parent.parent
if str(solve_it_root) not in sys.path:
    sys.path.insert(0, str(solve_it_root))

logger = logging.getLogger(__name__)

# Path to this extension's data directory (contains techniques/, weaknesses/, etc.)
_EXTENSION_DIR = Path(__file__).parent

EXTENSION_NAME = "AI Applicability"

# Assessments within this many days of today are considered "recent"
RECENT_THRESHOLD_DAYS = 90

CATEGORY_LABELS = {
    "in_tool": "In Tools",
    "ac_imp": "Academic Implementation",
    "ac_idea": "Academic Idea",
    "app_env": "Application Envisioned",
    "non_ai": "Non-AI",
}

CATEGORY_DIR_TO_KEY = {
    "in-tool": "in_tool",
    "ac-imp": "ac_imp",
    "ac-idea": "ac_idea",
    "app-env": "app_env",
    "non-ai": "non_ai",
}

CATEGORY_COLOURS = {
    "in_tool": "#16a34a",
    "ac_imp": "#2563eb",
    "ac_idea": "#7c3aed",
    "app_env": "#d97706",
    "non_ai": "#6b7280",
}

CATEGORY_SHORT_LABELS = {
    "in_tool": "In Tools",
    "ac_imp": "Ac. Impl.",
    "ac_idea": "Ac. Idea",
    "app_env": "Envisioned",
    "non_ai": "Non-AI",
}

CATEGORY_BG_COLOURS = {
    "in_tool": "#dcfce7",
    "ac_imp": "#dbeafe",
    "ac_idea": "#ede9fe",
    "app_env": "#fef3c7",
    "non_ai": "#f3f4f6",
}

CATEGORY_ORDER = ["in_tool", "ac_imp", "ac_idea", "app_env", "non_ai"]


# ---------------------------------------------------------------------------
# Assessment helpers
# ---------------------------------------------------------------------------

def _parse_date(date_str):
    """Parse an ISO date string (YYYY-MM-DD or YYYY-MM) into a date object."""
    if not date_str:
        return None
    try:
        parts = date_str.split("-")
        if len(parts) == 3:
            return date(int(parts[0]), int(parts[1]), int(parts[2]))
        elif len(parts) == 2:
            return date(int(parts[0]), int(parts[1]), 1)
        elif len(parts) == 1:
            return date(int(parts[0]), 1, 1)
    except (ValueError, IndexError):
        pass
    return None


def _get_ext(kb, t_id):
    """Get extension metadata (from extension_data.json) for a technique."""
    technique = kb.get_technique(t_id)
    if not technique:
        return {}
    return technique.get('extension_data', {}).get(EXTENSION_NAME, {})


def _get_assessments(ext):
    """Return the assessments list from extension data."""
    return ext.get('assessments', [])


def _most_recent_assessment(ext):
    """Return (date, entry) for the most recent assessment, or (None, None)."""
    best_date = None
    best_entry = None
    for a in _get_assessments(ext):
        d = _parse_date(a.get('date', ''))
        if d and (best_date is None or d > best_date):
            best_date = d
            best_entry = a
    return best_date, best_entry


def _is_assessed(ext):
    """Return True if the technique has any assessments."""
    return len(_get_assessments(ext)) > 0


def _get_solve_it_sync_date():
    """Get the date of the HEAD commit of the cloned SOLVE-IT repo."""
    repo_root = Path(__file__).parent.parent.parent  # solve-it-clone/
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ci"],
            capture_output=True, text=True, cwd=str(repo_root), check=True,
        )
        # Output like "2026-03-15 14:23:01 +0100" -- take just the date
        return result.stdout.strip().split(" ")[0]
    except Exception:
        return None


def _is_recent(ext):
    """Return True if the most recent assessment is within the threshold."""
    latest, _ = _most_recent_assessment(ext)
    if latest is None:
        return False
    cutoff = date.today() - timedelta(days=RECENT_THRESHOLD_DAYS)
    return latest >= cutoff


def _status_label(ext):
    """Return a human-readable status label."""
    if not _is_assessed(ext):
        return "Unassessed"
    if _is_recent(ext):
        latest, _ = _most_recent_assessment(ext)
        return f"Recently assessed ({latest.isoformat()})"
    latest, _ = _most_recent_assessment(ext)
    return f"Previously assessed ({latest.isoformat()})" if latest else "Previously assessed"


def _status_colours(ext):
    """Return (fg, bg, border) for a technique's status."""
    if not _is_assessed(ext):
        return ("#4b5563", "#f9fafb", "#d1d5db")
    if _is_recent(ext):
        return ("#166534", "#f0fdf4", "#bbf7d0")
    return ("#1e40af", "#eff6ff", "#bfdbfe")


# ---------------------------------------------------------------------------
# File reading: .bib and .txt support
# ---------------------------------------------------------------------------

def _parse_bib_file(filepath):
    """Parse a .bib file and return a dict with extracted fields."""
    parser = bibtex.Parser()
    try:
        bib_data = parser.parse_file(str(filepath))
    except (TokenRequired, Exception) as e:
        logger.warning("Error parsing .bib file %s: %s", filepath, e)
        return None

    for key in bib_data.entries:
        entry = bib_data.entries[key]
        fields = entry.fields
        persons = entry.persons

        authors = persons.get("author", [])
        author_str = " and ".join(str(a) for a in authors) if authors else None
        venue = fields.get("booktitle") or fields.get("journal") or None

        return {
            "note": fields.get("note"),
            "author": author_str,
            "year": fields.get("year"),
            "title": fields.get("title"),
            "venue": venue,
            "pages": fields.get("pages"),
            "publisher": fields.get("publisher"),
        }
    return None


def _parse_txt_file(filepath):
    """Parse a .txt file and return a dict.

    Format:
      Line(s) before '---' separator = note (AI relevance description)
      Line(s) after '---' separator  = Harvard-style reference (optional)
    """
    try:
        text = Path(filepath).read_text(encoding="utf-8").strip()
    except Exception as e:
        logger.warning("Error reading .txt file %s: %s", filepath, e)
        return None

    if not text:
        return None

    if "\n---" in text:
        parts = text.split("\n---", 1)
        note = parts[0].strip()
        reference = parts[1].strip() if len(parts) > 1 else None
    else:
        note = text
        reference = None

    return {
        "note": note,
        "author": None,
        "year": None,
        "title": None,
        "venue": None,
        "pages": None,
        "publisher": None,
        "reference_text": reference,
    }


_entries_cache = {}


def _read_entries_for_technique(t_id):
    """Read all .bib and .txt files from category subfolders for a technique."""
    if t_id in _entries_cache:
        return _entries_cache[t_id]

    technique_dir = _EXTENSION_DIR / "techniques" / t_id
    categories = {}

    for dir_name, cat_key in CATEGORY_DIR_TO_KEY.items():
        entries = []
        cat_path = technique_dir / dir_name
        if cat_path.is_dir():
            for f in sorted(cat_path.iterdir()):
                if f.suffix == ".bib":
                    parsed = _parse_bib_file(f)
                    if parsed:
                        entries.append(parsed)
                elif f.suffix == ".txt":
                    parsed = _parse_txt_file(f)
                    if parsed:
                        entries.append(parsed)
        categories[cat_key] = entries

    _entries_cache[t_id] = categories
    return categories


def _count_entries(ai_entries):
    """Count total AI applicability entries across all categories."""
    return sum(len(ai_entries.get(cat, [])) for cat in CATEGORY_ORDER)


def _format_citation(entry):
    """Format an inline citation from an entry dict."""
    author_str = entry.get('author')
    year = entry.get('year')

    if not author_str and not year:
        return ""

    if author_str:
        authors = [a.strip() for a in author_str.split(' and ')]
        last_names = []
        for a in authors:
            if ',' in a:
                last_names.append(a.split(',')[0].strip())
            else:
                parts = a.strip().split()
                last_names.append(parts[-1] if parts else a)

        if len(last_names) == 1:
            name_part = last_names[0]
        elif len(last_names) == 2:
            name_part = f"{last_names[0]} & {last_names[1]}"
        else:
            name_part = f"{last_names[0]} et al"
    else:
        name_part = ""

    if year:
        return f"({name_part} {year})" if name_part else f"({year})"
    return f"({name_part})" if name_part else ""


def _render_entry_html(entry):
    """Render a single AI applicability entry as HTML."""
    note = escape(entry.get('note', ''))
    citation = escape(_format_citation(entry))
    title = entry.get('title')
    venue = entry.get('venue')
    author = entry.get('author')
    year = entry.get('year')
    pages = entry.get('pages')
    ref_text = entry.get('reference_text')

    html = (
        '<div style="background:#fafafa;border:1px solid #e5e7eb;border-radius:4px;'
        'padding:6px 10px;font-size:.82rem;margin-bottom:3px">\n'
        f'<div>{note}'
    )
    if citation:
        html += f' <span style="color:#6b7280">{citation}</span>'
    html += '</div>\n'

    ref_parts = []
    if author:
        ref_parts.append(escape(author))
    if year:
        ref_parts.append(f'({escape(year)})')
    if title:
        ref_parts.append(f'<em>{escape(title)}</em>')
    if venue:
        ref_parts.append(escape(venue))
    if pages:
        ref_parts.append(f'pp. {escape(pages)}')

    if ref_parts:
        html += (
            f'<div style="font-size:.72rem;color:#9ca3af;margin-top:2px">'
            f'{", ".join(ref_parts)}</div>\n'
        )
    elif ref_text:
        html += (
            f'<div style="font-size:.72rem;color:#9ca3af;margin-top:2px">'
            f'{escape(ref_text)}</div>\n'
        )

    html += '</div>\n'
    return html


def _render_assessments_html(ext):
    """Render the assessment history as a small HTML block."""
    assessments = _get_assessments(ext)
    if not assessments:
        return ""

    items = ""
    for a in assessments:
        d = escape(a.get('date', ''))
        by = escape(a.get('by', ''))
        if by:
            items += f'<span>{d} ({by})</span>'
        else:
            items += f'<span>{d}</span>'

    fg, bg, border = _status_colours(ext)
    return (
        f'<div style="background:{bg};border:1px solid {border};border-radius:6px;padding:6px 12px;'
        f'font-size:.78rem;color:{fg};margin-top:6px;display:flex;gap:12px;flex-wrap:wrap">'
        f'<strong>Assessments:</strong> {items}'
        '</div>'
    )


# --------
# Markdown
# --------

def get_markdown_generic(kb=None):
    if kb is None:
        return ""
    techniques = kb.list_techniques()
    assessed = 0
    recent = 0
    with_data = 0
    unassessed = 0
    for t_id in techniques:
        ext = _get_ext(kb, t_id)
        if not _is_assessed(ext):
            unassessed += 1
        else:
            assessed += 1
            if _is_recent(ext):
                recent += 1
            ai = _read_entries_for_technique(t_id)
            if _count_entries(ai) > 0:
                with_data += 1

    out = "## AI Applicability Review Summary\n\n"
    out += f"- **{assessed}** techniques assessed ({with_data} with AI applicability data)\n"
    out += f"  - **{recent}** recently assessed\n"
    out += f"- **{unassessed}** techniques unassessed\n"
    return out


def get_markdown_for_technique(t_id, kb=None):
    if type(t_id) is not str:
        raise TypeError(f'id type is {type(t_id)}')
    if kb is None:
        return ""

    ext = _get_ext(kb, t_id)
    if not ext:
        return ""

    if not _is_assessed(ext):
        return "**[Unassessed]** This technique has not yet been assessed for AI applicability.\n"

    out = ""
    assessments = _get_assessments(ext)
    if assessments:
        parts = []
        for a in assessments:
            d = a.get('date', '')
            by = a.get('by', '')
            parts.append(f"{d} ({by})" if by else d)
        out += f"**Assessments:** {', '.join(parts)}\n\n"

    ai = _read_entries_for_technique(t_id)
    has_any = False
    for cat in CATEGORY_ORDER:
        entries = ai.get(cat, [])
        if entries:
            has_any = True
            out += f"### {CATEGORY_LABELS[cat]}\n\n"
            for entry in entries:
                note = entry.get('note', '')
                citation = _format_citation(entry)
                ref_text = entry.get('reference_text')
                out += f"- {note}"
                if citation:
                    out += f" {citation}"
                out += "\n"
                title = entry.get('title')
                venue = entry.get('venue')
                if title:
                    ref_line = f"  *{title}*"
                    if venue:
                        ref_line += f", {venue}"
                    out += ref_line + "\n"
                elif ref_text:
                    out += f"  {ref_text}\n"
            out += "\n"

    if not has_any:
        out += "No AI applicability identified during review.\n"

    return out


def get_markdown_for_technique_prefix(t_id, kb=None):
    return ""


def get_markdown_for_technique_suffix(t_id, kb=None):
    if kb is None:
        return ""
    ext = _get_ext(kb, t_id)
    if not _is_assessed(ext):
        return " [?]"
    ai = _read_entries_for_technique(t_id)
    count = _count_entries(ai)
    if count > 0:
        return f" [AI: {count}]"
    return ""


def get_markdown_for_weakness(w_id, kb=None):
    return ""

def get_markdown_for_weakness_prefix(w_id, kb=None):
    return ""

def get_markdown_for_weakness_suffix(w_id, kb=None):
    return ""

def get_markdown_for_mitigation(m_id, kb=None):
    return ""

def get_markdown_for_mitigation_prefix(m_id, kb=None):
    return ""

def get_markdown_for_mitigation_suffix(m_id, kb=None):
    return ""


# ---------------
# Report generation
# ---------------

def _render_technique_report_section(kb, t_id):
    """Render a single technique's AI applicability as HTML for the report."""
    technique = kb.get_technique(t_id)
    if not technique:
        return ""
    ext = _get_ext(kb, t_id)
    if not ext:
        return ""

    t_name = escape(technique.get('name', t_id))
    t_desc = escape(technique.get('description', ''))
    label = _status_label(ext)
    fg, bg, border = _status_colours(ext)

    html = f'<div class="technique" id="{escape(t_id)}">\n'
    html += (
        f'<h3 style="margin:0 0 4px 0;font-size:1rem">{escape(t_id)}: {t_name} '
        f'<span style="font-size:.75rem;font-weight:normal;padding:2px 8px;border-radius:4px;'
        f'background:{bg};color:{fg};border:1px solid {border}">{escape(label)}</span></h3>\n'
    )
    if t_desc:
        html += f'<p style="margin:0 0 8px 0;color:#4b5563;font-size:.85rem">{t_desc}</p>\n'

    if not _is_assessed(ext):
        html += (
            '<p style="color:#6b7280;font-style:italic;font-size:.85rem">'
            'This technique has not yet been assessed for AI applicability.</p>\n'
            '</div>\n'
        )
        return html

    # Assessment history
    assessments = _get_assessments(ext)
    if assessments:
        items = ""
        for a in assessments:
            d = escape(a.get('date', ''))
            by = escape(a.get('by', ''))
            items += f'<span>{d} ({by})</span> ' if by else f'<span>{d}</span> '
        html += (
            f'<div style="font-size:.75rem;color:#6b7280;margin-bottom:6px">'
            f'Assessments: {items}</div>\n'
        )

    ai = _read_entries_for_technique(t_id)
    has_any = False

    for cat in CATEGORY_ORDER:
        entries = ai.get(cat, [])
        if not entries:
            continue
        has_any = True
        colour = CATEGORY_COLOURS[cat]
        label = CATEGORY_LABELS[cat]

        html += f'<div style="margin-bottom:6px">\n'
        html += f'<div style="font-size:.8rem;font-weight:600;color:{colour};margin-bottom:2px">{escape(label)}</div>\n'
        for entry in entries:
            html += _render_entry_html(entry)
        html += '</div>\n'

    if not has_any:
        html += (
            '<p style="color:#9ca3af;font-style:italic;font-size:.85rem">'
            'No AI applicability identified during review.</p>\n'
        )

    html += '</div>\n'
    return html


def _generate_report(kb):
    """Generate a standalone HTML report organised by objective and technique."""
    docs_dir = Path(__file__).parent.parent.parent.parent / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    report_path = docs_dir / "ai-applicability-report.html"

    sync_date = _get_solve_it_sync_date()

    techniques_all = kb.list_techniques()
    total = len(techniques_all)
    assessed = 0
    recent = 0
    with_data = 0
    unassessed = 0
    cat_counts = {cat: 0 for cat in CATEGORY_ORDER}

    for t_id in techniques_all:
        ext = _get_ext(kb, t_id)
        if not _is_assessed(ext):
            unassessed += 1
        else:
            assessed += 1
            if _is_recent(ext):
                recent += 1
            ai = _read_entries_for_technique(t_id)
            if any(ai.get(cat, []) for cat in CATEGORY_ORDER):
                with_data += 1
            for cat in CATEGORY_ORDER:
                cat_counts[cat] += len(ai.get(cat, []))

    legend_items = ""
    for cat in CATEGORY_ORDER:
        if cat_counts[cat] > 0:
            colour = CATEGORY_COLOURS[cat]
            label = CATEGORY_LABELS[cat]
            legend_items += (
                f'<span style="display:inline-flex;align-items:center;gap:4px">'
                f'<span style="width:10px;height:10px;border-radius:2px;background:{colour};'
                f'display:inline-block"></span>'
                f'{label}: {cat_counts[cat]}</span>\n'
            )

    objectives = kb.list_objectives()
    objectives.sort(key=lambda o: o.get('sort_order', 999))

    body_html = ""
    toc_html = ""

    for obj in objectives:
        o_id = obj.get('id', '')
        o_name = escape(obj.get('name', ''))
        o_desc = escape(obj.get('description', ''))
        t_ids = obj.get('techniques', [])

        if not t_ids:
            continue

        anchor = o_id.lower().replace(' ', '-')
        toc_html += f'<li><a href="#{escape(anchor)}">{escape(o_id)}: {o_name}</a></li>\n'

        body_html += f'<section class="objective" id="{escape(anchor)}">\n'
        body_html += f'<h2 style="margin:24px 0 4px 0;padding-bottom:4px;border-bottom:2px solid #e5e7eb">{escape(o_id)}: {o_name}</h2>\n'
        if o_desc:
            body_html += f'<p style="color:#4b5563;margin:0 0 12px 0">{o_desc}</p>\n'

        for t_id in t_ids:
            body_html += _render_technique_report_section(kb, t_id)
            technique = kb.get_technique(t_id)
            if technique:
                for sub in technique.get('subtechniques', []):
                    sub_id = str(sub) if not isinstance(sub, dict) else sub.get('id', '')
                    if sub_id:
                        body_html += _render_technique_report_section(kb, sub_id)

        body_html += '</section>\n'

    report_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SOLVE-IT-X: AI Applicability Report</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         max-width: 960px; margin: 0 auto; padding: 24px 16px; color: #1f2937;
         line-height: 1.5; }}
  a {{ color: #2563eb; text-decoration: none; }}
  a:hover {{ text-decoration: underline; }}
  .header {{ margin-bottom: 24px; }}
  .header h1 {{ font-size: 1.5rem; margin-bottom: 8px; }}
  .stats {{ display: flex; gap: 16px; flex-wrap: wrap; font-size: .85rem;
            background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 6px;
            padding: 10px 14px; color: #1e40af; margin-bottom: 8px; }}
  .legend {{ display: flex; gap: 16px; flex-wrap: wrap; font-size: .8rem;
             background: #f9fafb; border: 1px solid #d1d5db; border-radius: 6px;
             padding: 8px 14px; color: #4b5563; margin-bottom: 16px; }}
  .toc {{ background: #f9fafb; border: 1px solid #e5e7eb; border-radius: 6px;
          padding: 12px 16px; margin-bottom: 24px; }}
  .toc h2 {{ font-size: 1rem; margin-bottom: 6px; }}
  .toc ul {{ margin: 0; padding-left: 20px; font-size: .85rem; columns: 2; column-gap: 24px; }}
  .toc li {{ margin-bottom: 2px; break-inside: avoid; }}
  .technique {{ margin: 8px 0 16px 16px; padding: 8px 12px; border-left: 3px solid #e5e7eb; }}
  @media (max-width: 640px) {{
    .toc ul {{ columns: 1; }}
    .technique {{ margin-left: 4px; }}
  }}
  @media print {{
    .technique {{ break-inside: avoid; }}
    section.objective {{ break-before: page; }}
  }}
</style>
</head>
<body>
<div class="header">
  <h1>SOLVE-IT-X: AI Applicability Report</h1>
  <p style="font-size:.85rem;color:#6b7280;margin-bottom:12px">
    A structured review of AI applicability across SOLVE-IT digital forensic techniques,
    organised by investigative objective.
    <a href="index.html">Back to interactive viewer</a>
  </p>
  <div class="stats">
    <strong>Summary</strong>
    <span>Total techniques: {total}</span>
    <span>Assessed: {assessed} ({with_data} with data)</span>
    <span>Recently assessed: {recent}</span>
    <span>Unassessed: {unassessed}</span>
    <span style="color:#6b7280;font-size:.75rem">SOLVE-IT synced: {sync_date or 'unknown'}</span>
  </div>
  <div class="legend">
    <strong>Categories</strong>
    {legend_items}
  </div>
</div>

<div class="toc">
  <h2>Objectives</h2>
  <ul>
    {toc_html}
  </ul>
</div>

{body_html}

<footer style="margin-top:32px;padding-top:12px;border-top:1px solid #e5e7eb;font-size:.75rem;color:#9ca3af">
  Generated by SOLVE-IT-X: AI Applicability Review extension.
</footer>
</body>
</html>"""

    try:
        report_path.write_text(report_html, encoding='utf-8')
        logger.info("AI Applicability Report written to: %s", report_path)
        return True
    except Exception as e:
        logger.warning("Failed to write AI Applicability Report: %s", e)
        return False


# ----
# HTML
# ----

def get_html_generic(kb=None):
    if kb is None:
        return ""
    techniques = kb.list_techniques()
    assessed = 0
    recent = 0
    with_data = 0
    unassessed = 0
    cat_counts = {cat: 0 for cat in CATEGORY_ORDER}

    for t_id in techniques:
        ext = _get_ext(kb, t_id)
        if not _is_assessed(ext):
            unassessed += 1
        else:
            assessed += 1
            if _is_recent(ext):
                recent += 1
            ai = _read_entries_for_technique(t_id)
            for cat in CATEGORY_ORDER:
                entries = ai.get(cat, [])
                if entries:
                    cat_counts[cat] += len(entries)
            if _count_entries(ai) > 0:
                with_data += 1

    cat_spans = ""
    for cat in CATEGORY_ORDER:
        if cat_counts[cat] > 0:
            colour = CATEGORY_COLOURS[cat]
            label = CATEGORY_LABELS[cat]
            cat_spans += (
                f'<span style="color:{colour};font-weight:500">'
                f'{label}: {cat_counts[cat]}</span>'
            )

    _generate_report(kb)

    sync_date = _get_solve_it_sync_date()
    sync_html = (
        f'<span style="color:#9ca3af;font-size:.7rem">SOLVE-IT synced: {escape(sync_date)}</span>'
        if sync_date else ""
    )

    return (
        '<div style="background:#d69e2e;padding:6px 16px;'
        'font-size:12px;font-weight:500;color:#1a1a1a;text-align:center;margin-bottom:6px">'
        'This is a <strong>SOLVE-IT-X extension</strong> to the '
        '<a href="https://github.com/SOLVE-IT-DF/solve-it" style="color:#1a1a1a;font-weight:700;text-decoration:underline">SOLVE-IT repository</a> '
        'and there may be deviations from the standard content.'
        '</div>'
        '<div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:6px;padding:10px 14px;'
        'font-size:.82rem;color:#1e40af;display:flex;gap:16px;align-items:center;flex-wrap:wrap">'
        '<strong>AI Applicability Review</strong>'
        f'<span>Assessed: {assessed} ({with_data} with data)</span>'
        f'<span>Recently assessed: {recent}</span>'
        f'<span>Unassessed: {unassessed}</span>'
        f'{sync_html}'
        '<a href="ai-applicability-report.html" '
        'style="margin-left:auto;padding:3px 10px;background:#1e40af;color:#fff;'
        'border-radius:4px;font-size:.75rem;text-decoration:none;font-weight:500"'
        '>Full Report</a>'
        '</div>'
        '<div style="background:#f9fafb;border:1px solid #d1d5db;border-radius:6px;padding:8px 14px;'
        'font-size:.78rem;color:#4b5563;display:flex;gap:16px;align-items:center;flex-wrap:wrap;margin-top:4px">'
        f'{cat_spans}'
        '</div>'
    )


def get_html_for_technique(t_id, kb=None):
    if type(t_id) is not str:
        raise TypeError(f'id type is {type(t_id)}')
    if kb is None:
        return ""

    ext = _get_ext(kb, t_id)
    if not ext:
        return ""

    if not _is_assessed(ext):
        return (
            '<div style="background:#f9fafb;border:1px solid #d1d5db;border-radius:6px;padding:8px 12px;'
            'font-size:.82rem;color:#4b5563;margin-top:6px">'
            '<strong>[Unassessed]</strong> This technique has not yet been assessed for AI applicability.'
            '</div>'
        )

    out = ""

    # Assessment history
    out += _render_assessments_html(ext)

    # AI applicability entries from subfolders
    ai = _read_entries_for_technique(t_id)
    has_any = False

    for cat in CATEGORY_ORDER:
        entries = ai.get(cat, [])
        if not entries:
            continue
        has_any = True
        colour = CATEGORY_COLOURS[cat]
        label = escape(CATEGORY_LABELS[cat])

        out += (
            f'<div style="margin-top:6px">'
            f'<div style="font-size:.78rem;font-weight:600;color:{colour};'
            f'margin-bottom:2px">{label}</div>'
        )
        for entry in entries:
            out += _render_entry_html(entry)
        out += '</div>'

    if not has_any:
        out += (
            '<div style="background:#f9fafb;border:1px solid #e5e7eb;border-radius:6px;padding:8px 12px;'
            'font-size:.82rem;color:#9ca3af;margin-top:6px">'
            'No AI applicability identified during review.'
            '</div>'
        )

    return out


def get_html_for_technique_suffix(t_id, kb=None):
    if type(t_id) is not str:
        raise TypeError(f'id type is {type(t_id)}')
    if kb is None:
        return ""

    ext = _get_ext(kb, t_id)
    if not _is_assessed(ext):
        return '<span class="cat-tag" style="background:#f3f4f6;color:#6b7280" title="Unassessed">?</span>'

    ai = _read_entries_for_technique(t_id)
    tags = ""
    for cat in CATEGORY_ORDER:
        entries = ai.get(cat, [])
        if entries:
            colour = CATEGORY_COLOURS[cat]
            bg = CATEGORY_BG_COLOURS[cat]
            label = CATEGORY_SHORT_LABELS[cat]
            count = len(entries)
            tags += (
                f'<span class="cat-tag" style="background:{bg};color:{colour};'
                f'font-size:.6rem;margin-top:2px;display:inline-block" '
                f'title="{CATEGORY_LABELS[cat]}: {count}">'
                f'{label}: {count}</span> '
            )
    return tags


def get_html_for_weakness(w_id, kb=None):
    return ""

def get_html_for_weakness_prefix(w_id, kb=None):
    return ""

def get_html_for_weakness_suffix(w_id, kb=None):
    return ""

def get_html_for_mitigation(m_id, kb=None):
    return ""

def get_html_for_mitigation_prefix(m_id, kb=None):
    return ""

def get_html_for_mitigation_suffix(m_id, kb=None):
    return ""


# ----------
# Excel Code
# ----------

def get_excel_generic(excel_worksheet, start_row, kb=None):
    return excel_worksheet


def get_excel_for_technique(t_id, excel_worksheet, start_row, kb=None):
    if type(t_id) is not str:
        raise TypeError(f'id type is {type(t_id)}')
    if kb is None:
        return excel_worksheet

    ext = _get_ext(kb, t_id)
    if not ext:
        return excel_worksheet

    row = start_row

    if not _is_assessed(ext):
        excel_worksheet.write_string(row, 0, "[Unassessed]")
        return excel_worksheet

    # Write assessment history
    assessments = _get_assessments(ext)
    if assessments:
        parts = []
        for a in assessments:
            d = a.get('date', '')
            by = a.get('by', '')
            parts.append(f"{d} ({by})" if by else d)
        excel_worksheet.write_string(row, 0, f"Assessments: {', '.join(parts)}")
        row += 1

    ai = _read_entries_for_technique(t_id)
    for cat in CATEGORY_ORDER:
        entries = ai.get(cat, [])
        for entry in entries:
            excel_worksheet.write_string(row, 0, CATEGORY_LABELS[cat])
            excel_worksheet.write_string(row, 1, entry.get('note', ''))
            excel_worksheet.write_string(row, 2, entry.get('author', '') or '')
            excel_worksheet.write_string(row, 3, entry.get('year', '') or '')
            excel_worksheet.write_string(row, 4, entry.get('title', '') or '')
            excel_worksheet.write_string(row, 5, entry.get('venue', '') or entry.get('reference_text', '') or '')
            row += 1

    return excel_worksheet


def get_excel_for_weakness(w_id, excel_worksheet, start_row, kb=None):
    return excel_worksheet

def get_excel_for_mitigation(m_id, excel_worksheet, start_row, kb=None):
    return excel_worksheet
