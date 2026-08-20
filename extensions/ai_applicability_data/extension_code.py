import logging
import subprocess
import sys
from datetime import date, timedelta
from html import escape
from pathlib import Path
from urllib.parse import quote

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
    "non_ai": "Non-AI",
}

CATEGORY_DIR_TO_KEY = {
    "in-tool": "in_tool",
    "ac-imp": "ac_imp",
    "ac-idea": "ac_idea",
    "non-ai": "non_ai",
}

CATEGORY_COLOURS = {
    "in_tool": "#16a34a",
    "ac_imp": "#2563eb",
    "ac_idea": "#7c3aed",
    "non_ai": "#6b7280",
}

CATEGORY_SHORT_LABELS = {
    "in_tool": "In Tools",
    "ac_imp": "Ac. Impl.",
    "ac_idea": "Ac. Idea",
    "non_ai": "Non-AI",
}

CATEGORY_BG_COLOURS = {
    "in_tool": "#dcfce7",
    "ac_imp": "#dbeafe",
    "ac_idea": "#ede9fe",
    "non_ai": "#f3f4f6",
}

CATEGORY_ORDER = ["in_tool", "ac_imp", "ac_idea", "non_ai"]


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
    # Read raw content for "Copy BibTeX" support
    try:
        raw_bib = Path(filepath).read_text(encoding="utf-8").strip()
    except Exception:
        raw_bib = ""

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

        url = fields.get("url") or None
        doi = fields.get("doi") or None
        if not url and doi:
            url = f"https://doi.org/{doi}"

        return {
            "note": fields.get("note"),
            "author": author_str,
            "year": fields.get("year"),
            "title": fields.get("title"),
            "venue": venue,
            "pages": fields.get("pages"),
            "publisher": fields.get("publisher"),
            "url": url,
            "doi": doi,
            "raw_bib": raw_bib,
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


def _parse_entry_json(filepath):
    """Parse an entry .json file and return the parsed dict, or None."""
    try:
        import json as _json
        data = _json.loads(Path(filepath).read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except Exception as e:
        logger.warning("Error reading .json file %s: %s", filepath, e)
        return None


def _read_entries_for_technique(t_id):
    """Read all .json/.bib/.txt files from category subfolders for a technique.

    A .json file provides the note and future metadata.  If a .bib file with
    the same stem exists alongside it, the citation fields come from the .bib
    and the note comes from the .json.  A standalone .json (no matching .bib)
    is treated as a note-only entry.  A standalone .bib still falls back to its
    own ``note`` field for backwards compatibility.
    """
    if t_id in _entries_cache:
        return _entries_cache[t_id]

    technique_dir = _EXTENSION_DIR / "techniques" / t_id
    categories = {}

    for dir_name, cat_key in CATEGORY_DIR_TO_KEY.items():
        entries = []
        cat_path = technique_dir / dir_name
        if cat_path.is_dir():
            files = sorted(cat_path.iterdir())
            # Index .json files by stem for pairing with .bib
            json_by_stem = {}
            for f in files:
                if f.suffix == ".json":
                    json_by_stem[f.stem] = f

            seen_stems = set()
            for f in files:
                if f.suffix == ".bib":
                    parsed = _parse_bib_file(f)
                    if parsed:
                        # Override note with .json if present
                        json_file = json_by_stem.get(f.stem)
                        if json_file:
                            json_data = _parse_entry_json(json_file)
                            if json_data and json_data.get("notes"):
                                parsed["note"] = json_data["notes"]
                            seen_stems.add(f.stem)
                        entries.append(parsed)
                elif f.suffix == ".txt":
                    parsed = _parse_txt_file(f)
                    if parsed:
                        entries.append(parsed)

            # Standalone .json files (no matching .bib)
            for stem, json_file in sorted(json_by_stem.items()):
                if stem not in seen_stems:
                    json_data = _parse_entry_json(json_file)
                    if json_data and json_data.get("notes"):
                        entries.append({
                            "note": json_data["notes"],
                            "author": None,
                            "year": None,
                            "title": None,
                            "venue": None,
                            "pages": None,
                            "publisher": None,
                        })

        categories[cat_key] = entries

    _entries_cache[t_id] = categories
    return categories


def _count_entries(ai_entries):
    """Count total AI applicability entries across all categories."""
    return sum(len(ai_entries.get(cat, [])) for cat in CATEGORY_ORDER)



def _format_harvard(entry):
    """Format a Harvard-style plaintext citation from an entry dict."""
    parts = []
    if entry.get('author'):
        parts.append(entry['author'])
    if entry.get('year'):
        parts.append(f"({entry['year']})")
    if entry.get('title'):
        parts.append(entry['title'])
    if entry.get('venue'):
        parts.append(entry['venue'])
    if entry.get('pages'):
        parts.append(f"pp. {entry['pages']}")
    return ", ".join(parts) if parts else ""


def _esc_attr(s):
    """Escape a string for safe inclusion in an HTML data-* attribute."""
    return escape(s).replace("'", "&#39;").replace('"', "&quot;").replace("\n", "&#10;")


def _render_entry_html(entry):
    """Render a single AI applicability entry as HTML.

    Layout order: author (year) heading, then notes, then reference details below.
    """
    note = escape(entry.get('note', ''))
    title = entry.get('title')
    venue = entry.get('venue')
    author = entry.get('author')
    year = entry.get('year')
    pages = entry.get('pages')
    url = entry.get('url')
    ref_text = entry.get('reference_text')
    raw_bib = entry.get('raw_bib', '')
    harvard_text = _format_harvard(entry)

    html = (
        '<div style="background:#fafafa;border:1px solid #e5e7eb;border-radius:4px;'
        'padding:6px 10px;font-size:.82rem;margin-bottom:3px">\n'
    )

    # -- Author (year) heading with action icons --
    author_year = []
    if author:
        author_year.append(escape(author))
    if year:
        author_year.append(f'({escape(year)})')

    if author_year:
        html += (
            f'<div style="display:flex;align-items:baseline;gap:6px">'
            f'<div style="font-weight:600;font-size:.82rem;flex:1">'
            f'{" ".join(author_year)}</div>'
        )
        if url:
            html += (
                f'<a href="{escape(url)}" target="_blank" rel="noopener noreferrer" '
                f'style="opacity:.4;font-size:.72rem;text-decoration:none" '
                f'title="Open URL" '
                f'onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.4"'
                f'>&#128279;</a>'
            )
        html += (
            f'<span style="cursor:pointer;opacity:.4;font-size:.72rem" '
            f'title="Copy citation text" '
            f'data-cite="{_esc_attr(harvard_text)}" '
            f'onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.4" '
            f'onclick="{_COPY_ONCLICK}">&#128203;</span>'
        )
        if raw_bib:
            html += (
                f'<span style="cursor:pointer;opacity:.4;font-size:.72rem" '
                f'title="Copy BibTeX" '
                f'data-cite="{_esc_attr(raw_bib)}" '
                f'onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=.4" '
                f'onclick="{_COPY_ONCLICK}">&#128218;</span>'
            )
        html += '</div>\n'

    # -- Notes --
    if note:
        html += f'<div style="margin-top:2px">{note}</div>\n'

    # -- Reference details (smaller, expandable) --
    ref_parts = []
    if title:
        ref_parts.append(f'<em>{escape(title)}</em>')
    if venue:
        ref_parts.append(escape(venue))
    if pages:
        ref_parts.append(f'pp. {escape(pages)}')

    if ref_parts:
        html += (
            '<details style="margin-top:4px">'
            '<summary style="font-size:.7rem;color:#9ca3af;cursor:pointer;'
            'user-select:none">Reference details</summary>'
            '<div style="margin-top:4px;font-size:.7rem">'
            f'<div style="color:#6b7280;margin-bottom:4px">{", ".join(ref_parts)}</div>'
        )
        if raw_bib:
            html += (
                f'<pre style="background:#f3f4f6;border:1px solid #e5e7eb;border-radius:3px;'
                f'padding:6px 8px;margin:2px 0 0 0;font-size:.68rem;overflow-x:auto;'
                f'white-space:pre-wrap;word-break:break-all">{escape(raw_bib)}</pre>'
            )
        html += '</div></details>\n'

    elif ref_text:
        html += (
            f'<div style="font-size:.72rem;color:#9ca3af;margin-top:2px">'
            f'{escape(ref_text)}</div>\n'
        )

    html += '</div>\n'
    return html


# Inline onclick handler for copy buttons.  Must be fully self-contained
# because the viewer injects extension HTML via innerHTML (so <script> tags
# won't execute).  The handler reads the text from the button's data-cite
# attribute and shows a brief toast notification.
_COPY_ONCLICK = (
    "navigator.clipboard.writeText(this.dataset.cite).then("
    "(function(m){return function(){"
    "var d=document.createElement('div');d.textContent=m;"
    "d.style.cssText='position:fixed;bottom:20px;left:50%;"
    "transform:translateX(-50%);background:#1e293b;color:#fff;"
    "padding:8px 16px;border-radius:6px;font-size:.82rem;"
    "z-index:9999;opacity:0;transition:opacity .3s';"
    "document.body.appendChild(d);"
    "requestAnimationFrame(function(){d.style.opacity=1});"
    "setTimeout(function(){d.style.opacity=0;"
    "setTimeout(function(){d.remove()},300)},1500)"
    "}})(this.title==='Copy BibTeX'?'BibTeX copied':'Citation copied'))"
)


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
                ref_text = entry.get('reference_text')
                out += f"- {note}\n"
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

def _render_technique_report_section(kb, t_id, objective_id=""):
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

    # Categories present for this technique, written into the markup so the
    # in-page filter can select on them without re-reading the data.
    assessed = _is_assessed(ext)
    ai = _read_entries_for_technique(t_id) if assessed else {}
    present_cats = [c for c in CATEGORY_ORDER if ai.get(c)]
    if assessed:
        status = "recent" if _is_recent(ext) else "assessed"
    else:
        status = "unassessed"

    html = (
        f'<div class="technique" id="{escape(t_id)}" '
        f'data-cats="{" ".join(present_cats)}" '
        f'data-status="{status}" '
        f'data-objective="{escape(objective_id)}">\n'
    )
    html += (
        f'<h3 style="margin:0 0 4px 0;font-size:1rem">{escape(t_id)}: {t_name} '
        f'<span style="font-size:.75rem;font-weight:normal;padding:2px 8px;border-radius:4px;'
        f'background:{bg};color:{fg};border:1px solid {border}">{escape(label)}</span></h3>\n'
    )
    if t_desc:
        html += f'<p style="margin:0 0 8px 0;color:#4b5563;font-size:.85rem">{t_desc}</p>\n'

    if not assessed:
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

    has_any = False

    for cat in CATEGORY_ORDER:
        entries = ai.get(cat, [])
        if not entries:
            continue
        has_any = True
        colour = CATEGORY_COLOURS[cat]
        label = CATEGORY_LABELS[cat]

        html += f'<div class="cat-block" data-cat="{cat}" style="margin-bottom:6px">\n'
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


# CSS and JS for the report's filter controls.  These are kept out of the
# report f-string deliberately: an f-string would require every brace to be
# doubled, which is easy to get wrong and hard to read.
_REPORT_FILTER_CSS = """
  [hidden] { display: none !important; }
  .filters { background: #f9fafb; border: 1px solid #d1d5db; border-radius: 6px;
             padding: 8px 14px; margin-bottom: 16px; }
  .filter-row { display: flex; gap: 8px; flex-wrap: wrap; align-items: center;
                font-size: .8rem; color: #4b5563; }
  .filter-row + .filter-row { margin-top: 8px; padding-top: 8px;
                              border-top: 1px solid #e5e7eb; }
  .pill { display: inline-flex; align-items: center; gap: 6px; cursor: pointer;
          font: inherit; font-size: .78rem; padding: 3px 10px; border-radius: 999px;
          background: #fff; color: #4b5563; border: 1px solid #d1d5db; }
  .pill:hover { border-color: #9ca3af; }
  .pill:focus-visible { outline: 2px solid #2563eb; outline-offset: 2px; }
  .pill[aria-pressed="true"] { background: var(--pill-bg); color: var(--pill-fg);
                               border-color: var(--pill-fg); font-weight: 600; }
  .pill-dot { width: 9px; height: 9px; border-radius: 2px; display: inline-block; }
  .pill-count { color: #6b7280; font-weight: 400; }
  .pill[aria-pressed="true"] .pill-count { color: inherit; }
  .pill-reset { border-style: dashed; }
  .filter-count { margin-left: auto; font-size: .75rem; color: #6b7280; }
  .filter-toggle { display: inline-flex; align-items: center; gap: 6px;
                   font-size: .78rem; color: #4b5563; cursor: pointer; }
  .no-results { display: none; padding: 24px; text-align: center; color: #6b7280;
                font-style: italic; border: 1px dashed #d1d5db; border-radius: 6px; }
  body.no-results-shown .no-results { display: block; }
  /* Objectives hidden: a flat run of techniques, easier to select and copy. */
  body.flat .objective-heading,
  body.flat .objective-desc,
  body.flat .toc { display: none; }
  body.flat .technique { margin-left: 0; padding-left: 0; border-left: none; }
"""

_REPORT_FILTER_JS = """
(function () {
  var body = document.body;
  var pills = Array.prototype.slice.call(document.querySelectorAll('.pill[data-cat]'));
  var reset = document.getElementById('filter-reset');
  var counter = document.getElementById('filter-count');
  var flatToggle = document.getElementById('hide-objectives');
  var techniques = Array.prototype.slice.call(document.querySelectorAll('.technique'));
  var sections = Array.prototype.slice.call(document.querySelectorAll('section.objective'));
  var tocItems = Array.prototype.slice.call(document.querySelectorAll('.toc li[data-objective]'));
  var total = techniques.length;

  function activeCats() {
    return pills
      .filter(function (p) { return p.getAttribute('aria-pressed') === 'true'; })
      .map(function (p) { return p.dataset.cat; });
  }

  function apply() {
    var active = activeCats();
    var filtering = active.length > 0;
    var shown = 0;

    techniques.forEach(function (t) {
      var cats = (t.dataset.cats || '').split(' ').filter(Boolean);
      var match = !filtering || cats.some(function (c) { return active.indexOf(c) !== -1; });
      t.hidden = !match;
      if (match) { shown += 1; }
      Array.prototype.forEach.call(t.querySelectorAll('.cat-block'), function (b) {
        b.hidden = filtering && active.indexOf(b.dataset.cat) === -1;
      });
    });

    sections.forEach(function (s) {
      s.hidden = !s.querySelector('.technique:not([hidden])');
    });
    tocItems.forEach(function (li) {
      var s = document.querySelector('section.objective[data-objective="' + li.dataset.objective + '"]');
      li.hidden = !s || s.hidden;
    });

    if (reset) { reset.hidden = !filtering; }
    if (counter) {
      counter.textContent = filtering
        ? 'Showing ' + shown + ' of ' + total + ' techniques'
        : total + ' techniques';
    }
    body.classList.toggle('no-results-shown', shown === 0);
  }

  pills.forEach(function (p) {
    p.addEventListener('click', function () {
      p.setAttribute('aria-pressed', p.getAttribute('aria-pressed') === 'true' ? 'false' : 'true');
      apply();
    });
  });

  if (reset) {
    reset.addEventListener('click', function () {
      pills.forEach(function (p) { p.setAttribute('aria-pressed', 'false'); });
      apply();
    });
  }

  if (flatToggle) {
    flatToggle.addEventListener('change', function () {
      body.classList.toggle('flat', flatToggle.checked);
    });
  }

  apply();
})();
"""


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

    # Category pills.  Each is a toggle; with none pressed the whole report is
    # shown, otherwise techniques are filtered to the union of the pressed
    # categories and non-matching entries within them are hidden.
    pill_items = ""
    for cat in CATEGORY_ORDER:
        if cat_counts[cat] > 0:
            colour = CATEGORY_COLOURS[cat]
            bg = CATEGORY_BG_COLOURS[cat]
            label = CATEGORY_LABELS[cat]
            pill_items += (
                f'<button type="button" class="pill" data-cat="{cat}" aria-pressed="false" '
                f'style="--pill-fg:{colour};--pill-bg:{bg}">'
                f'<span class="pill-dot" style="background:{colour}"></span>'
                f'{label} <span class="pill-count">{cat_counts[cat]}</span></button>\n'
            )

    objectives = kb.list_objectives()
    objectives.sort(key=lambda o: o.get('sort_order', 999))

    body_html = ""
    toc_html = ""
    rendered = 0

    for obj in objectives:
        o_id = obj.get('id', '')
        o_name = escape(obj.get('name', ''))
        o_desc = escape(obj.get('description', ''))
        t_ids = obj.get('techniques', [])

        if not t_ids:
            continue

        anchor = o_id.lower().replace(' ', '-')

        section_body = ""
        for t_id in t_ids:
            section_body += _render_technique_report_section(kb, t_id, o_id)
            technique = kb.get_technique(t_id)
            if technique:
                for sub in technique.get('subtechniques', []):
                    sub_id = str(sub) if not isinstance(sub, dict) else sub.get('id', '')
                    if sub_id:
                        section_body += _render_technique_report_section(kb, sub_id, o_id)

        rendered += section_body.count('<div class="technique"')

        toc_html += (
            f'<li data-objective="{escape(o_id)}">'
            f'<a href="#{escape(anchor)}">{escape(o_id)}: {o_name}</a></li>\n'
        )

        body_html += f'<section class="objective" id="{escape(anchor)}" data-objective="{escape(o_id)}">\n'
        body_html += (
            f'<h2 class="objective-heading" '
            f'style="margin:24px 0 4px 0;padding-bottom:4px;border-bottom:2px solid #e5e7eb">'
            f'{escape(o_id)}: {o_name}</h2>\n'
        )
        if o_desc:
            body_html += f'<p class="objective-desc" style="color:#4b5563;margin:0 0 12px 0">{o_desc}</p>\n'

        body_html += section_body
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
{_REPORT_FILTER_CSS}
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
    .aicopy {{ display:none; }}
    .filters {{ display: none; }}
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
  <div class="filters">
    <div class="filter-row">
      <strong>Categories</strong>
      {pill_items}
      <button type="button" class="pill pill-reset" id="filter-reset" hidden>Show all</button>
      <span class="filter-count" id="filter-count">{rendered} techniques</span>
    </div>
    <div class="filter-row">
      <label class="filter-toggle">
        <input type="checkbox" id="hide-objectives">
        Hide objective headings (flat list, easier to copy)
      </label>
    </div>
  </div>
</div>

<div class="toc">
  <h2>Objectives</h2>
  <ul>
    {toc_html}
  </ul>
</div>

{body_html}

<p class="no-results">No techniques match the selected categories.</p>

<footer style="margin-top:32px;padding-top:12px;border-top:1px solid #e5e7eb;font-size:.75rem;color:#9ca3af">
  Generated by SOLVE-IT-X: AI Applicability Review extension.
</footer>
<script>
{_REPORT_FILTER_JS}
</script>
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
        technique = kb.get_technique(t_id) if kb else None
        t_name = technique.get('name', '') if technique else ''
        issue_title = quote(f"Add entry to {t_id} {t_name}".strip())
        issue_url = (
            f"https://github.com/SOLVE-IT-DF/solve-it-x-demo-ai-applicability-review"
            f"/issues/new?template=add-ai-entry.yml&technique_id={escape(t_id)}"
            f"&title={issue_title}"
        )
        return (
            '<div style="background:#f9fafb;border:1px solid #d1d5db;border-radius:6px;padding:8px 12px;'
            'font-size:.82rem;color:#4b5563;margin-top:6px">'
            '<strong>[Unassessed]</strong> This technique has not yet been assessed for AI applicability.'
            '</div>'
            f'<div style="margin-top:8px">'
            f'<a href="{issue_url}" target="_blank" rel="noopener noreferrer" '
            f'style="display:inline-block;padding:4px 12px;font-size:.78rem;'
            f'color:#1e40af;background:#eff6ff;border:1px solid #bfdbfe;border-radius:4px;'
            f'text-decoration:none;font-weight:500;cursor:pointer">'
            f'+ Add entry</a></div>'
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

    # "Add entry" button linking to the GitHub issue form, pre-filled with technique ID and title
    technique = kb.get_technique(t_id) if kb else None
    t_name = technique.get('name', '') if technique else ''
    issue_title = quote(f"Add entry to {t_id} {t_name}".strip())
    issue_url = (
        f"https://github.com/SOLVE-IT-DF/solve-it-x-demo-ai-applicability-review"
        f"/issues/new?template=add-ai-entry.yml&technique_id={escape(t_id)}"
        f"&title={issue_title}"
    )
    out += (
        f'<div style="margin-top:8px">'
        f'<a href="{issue_url}" target="_blank" rel="noopener noreferrer" '
        f'style="display:inline-block;padding:4px 12px;font-size:.78rem;'
        f'color:#1e40af;background:#eff6ff;border:1px solid #bfdbfe;border-radius:4px;'
        f'text-decoration:none;font-weight:500;cursor:pointer">'
        f'+ Add entry</a></div>'
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
