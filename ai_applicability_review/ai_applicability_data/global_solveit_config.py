"""
Global config for the AI Applicability Review extension.

Categorises techniques by their most recent assessment date:
  - Recently assessed (green) -- assessed within the last 3 months
  - Previously assessed (blue) -- assessed more than 3 months ago
  - Unassessed (grey) -- no assessment recorded
"""

from datetime import date, timedelta

EXTENSION_NAME = "AI Applicability"

# Assessments within this many days of today are considered "recent"
RECENT_THRESHOLD_DAYS = 90


def _get_ext_data(kb, t_id):
    """Get extension data for a technique."""
    t = kb.get_technique(t_id)
    if not t:
        return {}
    return t.get('extension_data', {}).get(EXTENSION_NAME, {})


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


def _most_recent_assessment(ext):
    """Return the most recent assessment date, or None."""
    assessments = ext.get('assessments', [])
    if not assessments:
        return None
    best = None
    for a in assessments:
        d = _parse_date(a.get('date', ''))
        if d and (best is None or d > best):
            best = d
    return best


def get_status_for_technique(kb, t_id):
    """Return status based on most recent assessment date."""
    ext = _get_ext_data(kb, t_id)
    latest = _most_recent_assessment(ext)
    if latest is None:
        return "placeholder"
    cutoff = date.today() - timedelta(days=RECENT_THRESHOLD_DAYS)
    if latest >= cutoff:
        return "complete"
    return "partial"


def get_status_labels(kb):
    return {
        "complete": "Recently assessed",
        "partial": "Previously assessed",
        "placeholder": "Unassessed",
    }


def get_status_colours(kb):
    return {
        "complete": {"fg": "#166534", "bg": "#f0fdf4", "border": "#bbf7d0"},
        "partial": {"fg": "#1e40af", "bg": "#eff6ff", "border": "#bfdbfe"},
        "placeholder": {"fg": "#4b5563", "bg": "#f9fafb", "border": "#d1d5db"},
    }


def get_colour_for_technique(kb, t_id):
    ext = _get_ext_data(kb, t_id)
    latest = _most_recent_assessment(ext)
    if latest is None:
        return "#f9fafb"
    cutoff = date.today() - timedelta(days=RECENT_THRESHOLD_DAYS)
    if latest >= cutoff:
        return "#f0fdf4"
    return "#eff6ff"


def get_title(kb):
    return "SOLVE-IT-X: AI Applicability Review"


def get_technique_prefix(kb, t_id):
    return ""


def get_technique_suffix(kb, t_id):
    return ""
