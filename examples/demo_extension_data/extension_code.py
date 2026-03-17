
from html import escape
from pathlib import Path
import sys

# This should add the SOLVE-IT library path if any extension needs to make use of it
solve_it_root = Path(__file__).parent.parent.parent
if str(solve_it_root) not in sys.path:
    sys.path.insert(0, str(solve_it_root))


# Edit these functions to customise the content added to the SOLVE-IT knowledge base

# --------
# Markdown
# --------

def get_markdown_generic(kb=None):
    """
    This demo fetches stats on the number of techniques, weaknesses and
    mitigations, and adds that to the start of the main markdown report.

    Args:
        kb: KnowledgeBase instance (passed by library).
    """
    if kb is None:
        raise ValueError("kb is None")

    out_str = f"## SOLVE-IT stats (added by SOLVE-IT-X demo)\n"
    out_str += f"objectives: {len(kb.list_objectives())}\n"
    out_str += f"techniques: {len(kb.list_techniques())}\n"
    out_str += f"weaknesses: {len(kb.list_weaknesses())}\n"
    out_str += f"mitigations: {len(kb.list_mitigations())}\n"

    return out_str

def get_markdown_for_technique(t_id, kb=None):
    '''Gets markdown for adding to the SOLVE-IT-X for a specific technique

    Args:
        t_id: Technique ID
        kb: KnowledgeBase instance (passed by library, optional)
    '''
    if type(t_id) is not str:
         raise TypeError(f'id type is {type(t_id)}')

    if kb is None:
        raise ValueError("kb is None")

    # Get extension data for this technique
    technique = kb.get_technique(t_id)
    if not technique:
        return ""

    demo_ext_data = technique.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        out_str = "**Extras (from demo extension):**\n\n"
        out_str += demo_ext_data.get('extras')
        return out_str

    return ""


"""Markdown text to be added to the end of each technique preview"""
def get_markdown_for_technique_suffix(t_id, kb=None):
    if type(t_id) is not str:
         raise TypeError(f'id type is {type(t_id)}')

    if kb is None:
        raise ValueError("kb is None")

    # Get extension data for this technique
    technique = kb.get_technique(t_id)
    if not technique:
        return ""

    demo_ext_data = technique.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return " (🧩)"

    return ""


"""Gets markdown for adding to the SOLVE-IT-X for a specific weakness"""
def get_markdown_for_weakness(w_id, kb=None):
    '''Gets markdown for adding to the SOLVE-IT-X for a specific weakness

    Args:
        w_id: Weakness ID
        kb: KnowledgeBase instance (passed by library, optional)
    '''
    if type(w_id) is not str:
         raise TypeError(f'id type is {type(w_id)}')

    if kb is None:
        raise ValueError("kb is None")

    # Get extension data for this weakness
    weakness = kb.get_weakness(w_id)
    if not weakness:
        return ""

    demo_ext_data = weakness.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return f"**Extras (from demo extension):**\n\n{demo_ext_data['extras']}"

    return ""


"""Markdown text to be added to the start of each weakness preview"""
def get_markdown_for_weakness_prefix(w_id, kb=None):

    # This example checks if there is extension data for this weakness and adds a prefix if so

    weakness = kb.get_weakness(w_id)
    if not weakness:
        return ""
    demo_ext_data = weakness.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return f"(🧩) "
    return ""


"""Markdown text to be added to the end of each weakness preview"""
def get_markdown_for_weakness_suffix(w_id, kb=None):

    # This example adds a suffix to a weakness showing how many mitigations it has

    weakness = kb.get_weakness(w_id)
    if not weakness:
        return ""
    mitigations = weakness.get('mitigations', [])
    return f" ({len(mitigations)} mitigations)"



def get_markdown_for_mitigation(m_id, kb=None):
    '''Gets markdown for adding to the SOLVE-IT-X for a specific mitigation

    Args:
        m_id: Mitigation ID
        kb: KnowledgeBase instance (passed by library, optional)
    '''
    if type(m_id) is not str:
         raise TypeError(f'id type is {type(m_id)}')

    if kb is None:
        raise ValueError("kb is None")

    # Get extension data for this mitigation
    mitigation = kb.get_mitigation(m_id)
    if not mitigation:
        return ""

    demo_ext_data = mitigation.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return f"**Extras (from demo extension):**\n\n{demo_ext_data['extras']}"

    return ""


"""Markdown text to be added to the start of each mitigation preview"""
def get_markdown_for_mitigation_prefix(m_id, kb=None):

    # This example checks if there is extension data for this mitigation and adds a prefix if so.

    mitigation = kb.get_mitigation(m_id)
    if not mitigation:
        return ""
    demo_ext_data = mitigation.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return f"(🧩) "
    return ""


"""Markdown text to be added to the end of each mitigation preview"""
def get_markdown_for_mitigation_suffix(m_id, kb=None):
    return ""



# These formats are not yet available for customisation

# ----
# HTML
# ----

def get_html_generic(kb=None):
    """HTML banner with KB stats, mirroring the markdown version."""
    if kb is None:
        raise ValueError("kb is None")

    return (
        '<div style="background:#e8f5e9;border:1px solid #a5d6a7;border-radius:6px;padding:10px 14px;'
        'font-size:.82rem;color:#2e7d32;text-align:center;margin-bottom:6px">'
        'This is the hello world example showing the customisation of the SOLVE-IT Explorer with SOLVE-IT-X.'
        '</div>'
        '<div style="background:#f0f4ff;border:1px solid #c7d2fe;border-radius:6px;padding:10px 14px;'
        'font-size:.82rem;color:#4338ca;display:flex;gap:16px;align-items:center;flex-wrap:wrap">'
        '<strong>SOLVE-IT Stats (added by SOLVE-IT-X)</strong>'
        f'<span>Objectives: {len(kb.list_objectives())}</span>'
        f'<span>Techniques: {len(kb.list_techniques())}</span>'
        f'<span>Weaknesses: {len(kb.list_weaknesses())}</span>'
        f'<span>Mitigations: {len(kb.list_mitigations())}</span>'
        '</div>'
    )


def get_html_for_technique(t_id, kb=None):
    """Render extras content for a technique if present."""
    if type(t_id) is not str:
        raise TypeError(f'id type is {type(t_id)}')
    if kb is None:
        raise ValueError("kb is None")

    technique = kb.get_technique(t_id)
    if not technique:
        return ""

    demo_ext_data = technique.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return (
            '<div style="background:#fefce8;border:1px solid #fde68a;border-radius:6px;padding:8px 12px;'
            'font-size:.82rem;margin-top:6px">'
            '<strong>Extras (demo):</strong> '
            f'{escape(demo_ext_data["extras"])}'
            '</div>'
        )
    return ""


def get_html_for_technique_suffix(t_id, kb=None):
    """Return puzzle badge if extras exist."""
    if type(t_id) is not str:
        raise TypeError(f'id type is {type(t_id)}')
    if kb is None:
        raise ValueError("kb is None")

    technique = kb.get_technique(t_id)
    if not technique:
        return ""

    demo_ext_data = technique.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return '<span style="font-size:.7rem" title="Has extension data">🧩</span>'
    return ""


def get_html_for_weakness(w_id, kb=None):
    """Render extras content for a weakness if present."""
    if type(w_id) is not str:
        raise TypeError(f'id type is {type(w_id)}')
    if kb is None:
        raise ValueError("kb is None")

    weakness = kb.get_weakness(w_id)
    if not weakness:
        return ""

    demo_ext_data = weakness.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return (
            '<div style="background:#fefce8;border:1px solid #fde68a;border-radius:6px;padding:8px 12px;'
            'font-size:.82rem;margin-top:6px">'
            '<strong>Extras (demo):</strong> '
            f'{escape(demo_ext_data["extras"])}'
            '</div>'
        )
    return ""


def get_html_for_weakness_prefix(w_id, kb=None):
    """Return puzzle badge if extras exist."""
    weakness = kb.get_weakness(w_id)
    if not weakness:
        return ""
    demo_ext_data = weakness.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return '<span style="font-size:.7rem" title="Has extension data">🧩</span> '
    return ""


def get_html_for_weakness_suffix(w_id, kb=None):
    """Return mitigation count."""
    weakness = kb.get_weakness(w_id)
    if not weakness:
        return ""
    mitigations = weakness.get('mitigations', [])
    return (
        f' <span class="cat-tag" style="background:#f0fdf4;color:#166534">'
        f'{len(mitigations)} mitigations</span>'
    )


def get_html_for_mitigation(m_id, kb=None):
    """Render extras content for a mitigation if present."""
    if type(m_id) is not str:
        raise TypeError(f'id type is {type(m_id)}')
    if kb is None:
        raise ValueError("kb is None")

    mitigation = kb.get_mitigation(m_id)
    if not mitigation:
        return ""

    demo_ext_data = mitigation.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return (
            '<div style="background:#fefce8;border:1px solid #fde68a;border-radius:6px;padding:8px 12px;'
            'font-size:.82rem;margin-top:6px">'
            '<strong>Extras (demo):</strong> '
            f'{escape(demo_ext_data["extras"])}'
            '</div>'
        )
    return ""


def get_html_for_mitigation_prefix(m_id, kb=None):
    """Return puzzle badge if extras exist."""
    mitigation = kb.get_mitigation(m_id)
    if not mitigation:
        return ""
    demo_ext_data = mitigation.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        return '<span style="font-size:.7rem" title="Has extension data">🧩</span> '
    return ""


# Excel Code
# ----------
"""General modifications to be made to the workbook"""
def get_excel_generic(excel_worksheet, start_row, kb=None):
    excel_worksheet.row(1, 20)
    return excel_worksheet

"""Modifications to be made to the workbook for each technique"""
def get_excel_for_technique(t_id, excel_worksheet, start_row, kb=None):

    if type(t_id) is not str:
        raise TypeError(f'id type is {type(t_id)}')

    if kb is None:
        raise ValueError("kb is None")

    # Get technique and check for extension data
    technique = kb.get_technique(t_id)
    if not technique:
        return excel_worksheet

    demo_ext_data = technique.get('extension_data', {}).get('Demo extension')
    if demo_ext_data and 'extras' in demo_ext_data:
        excel_worksheet.write_string(start_row, 0, "Demo extension data:")
        excel_worksheet.write_string(start_row+1, 0, "extras:")
        excel_worksheet.write_string(start_row+2, 0, demo_ext_data.get('extras'))

    return excel_worksheet

"""Modifications to be made to the workbook for each weakness"""
def get_excel_for_weakness(w_id, excel_worksheet, start_row, kb=None):
    return excel_worksheet

"""Modifications to be made to the workbook for each mitigation"""
def get_excel_for_mitigation(m_id, excel_worksheet, start_row, kb=None):
    return excel_worksheet