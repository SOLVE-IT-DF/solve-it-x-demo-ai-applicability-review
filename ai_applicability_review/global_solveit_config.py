"""
Default global config for SOLVE-IT-X.

Uses the standard SOLVE-IT maturity-based status labels and colours.
This provides a reasonable default for any extension. If you need custom
status labels or colours, create a separate global config file and
reference it in your extension_config.json using the "global_config" field.
"""


def get_status_for_technique(kb, t_id):
    """Use the maturity status from the knowledge base."""
    t = kb.get_technique(t_id)
    if not t:
        return "placeholder"
    return t.get('status', 'placeholder')


def get_status_labels(kb):
    """Standard SOLVE-IT status labels."""
    return {
        "complete": "stable",
        "partial": "partial",
        "placeholder": "placeholder",
    }


def get_status_colours(kb):
    """Standard SOLVE-IT status colours."""
    return {
        "complete": {"fg": "#1a7a4a", "bg": "#f0faf5", "border": "#a8dfc0"},
        "partial": {"fg": "#b7741a", "bg": "#fdf8ee", "border": "#f0d8a0"},
        "placeholder": {"fg": "#c0392b", "bg": "#fdf3f2", "border": "#f0c8c4"},
    }


def get_colour_for_technique(kb, t_id):
    """Colour technique cells based on maturity status."""
    status = get_status_for_technique(kb, t_id)
    colours = {
        "complete": "#f0faf5",
        "partial": "#fdf8ee",
        "placeholder": "#fdf3f2",
    }
    return colours.get(status, "#f9fafb")


def get_title(kb):
    return "SOLVE-IT-X"


def get_technique_prefix(kb, t_id):
    return ""


def get_technique_suffix(kb, t_id):
    return ""
