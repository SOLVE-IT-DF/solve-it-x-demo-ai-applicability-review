"""
Global config for the Demo extension.

Categorises techniques by whether they have extension data from the
Demo extension, rather than the default maturity-based status.
"""

EXTENSION_NAME = "Demo extension"


def _has_extension_data(kb, t_id):
    """Check if a technique has data from the Demo extension."""
    t = kb.get_technique(t_id)
    if not t:
        return False
    ext_data = t.get('extension_data', {}).get(EXTENSION_NAME)
    if ext_data:
        return True
    return False


def get_status_for_technique(kb, t_id):
    """Return 'complete' if extension data exists, 'placeholder' otherwise."""
    if _has_extension_data(kb, t_id):
        return "complete"
    else:
        return "placeholder"


def get_status_labels(kb):
    """Override the filter bar labels."""
    return {
        "complete": "has extension data",
        "partial": "partial",              # required by HTML generator, unused
        "placeholder": "no extension data",
    }


def get_status_colours(kb):
    """Override the filter bar colours."""
    return {
        "complete": {"fg": "#4338ca", "bg": "#f0f4ff", "border": "#c7d2fe"},
        "partial": {"fg": "#6b7280", "bg": "#f9fafb", "border": "#d1d5db"},  # required, unused
        "placeholder": {"fg": "#c0392b", "bg": "#fdf3f2", "border": "#f0c8c4"},
    }


def get_colour_for_technique(kb, t_id):
    """Colour technique cells based on extension data availability."""
    if _has_extension_data(kb, t_id):
        return "#f0f4ff"   # blue tint — has extension data
    else:
        return "#fdf3f2"   # red tint — no extension data


def get_title(kb):
    return "SOLVE-IT-X: Hello world!"


def get_technique_prefix(kb, t_id):
    return ""


def get_technique_suffix(kb, t_id):
    return ""
