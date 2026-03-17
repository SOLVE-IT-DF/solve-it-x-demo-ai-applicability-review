import sys
from pathlib import Path
# Edit these to customise the content added to the SOLVE-IT knowledge base


# This should add the SOLVE-IT library path if any extension needs to make use of it
solve_it_root = Path(__file__).parent.parent.parent
if str(solve_it_root) not in sys.path:
    sys.path.insert(0, str(solve_it_root))


# Markdown Code 
# -------------

"""Markdown text to be added to the main page"""
def get_markdown_generic(kb=None):
    return ""

"""Markdown text to be added to the end of each technique"""
def get_markdown_for_technique(t_id, kb=None):
    return ""

"""Markdown text to be added to the end of each technique name in main page"""
def get_markdown_for_technique_prefix(t_id, kb=None):
    return ""

"""Markdown text to be added to the end of each technique name in main page"""
def get_markdown_for_technique_suffix(t_id, kb=None):
    return ""

"""Markdown text to be added to the end of each weakness"""
def get_markdown_for_weakness(w_id, kb=None):
    return ""

"""Markdown text to be added to the start of each weakness preview"""
def get_markdown_for_weakness_prefix(w_id, kb=None):
    return ""

"""Markdown text to be added to the end of each weakness preview"""
def get_markdown_for_weakness_suffix(w_id, kb=None):
    return ""

"""Markdown text to be added to the end of each mitigation"""
def get_markdown_for_mitigation(m_id, kb=None):
    return ""

"""Markdown text to be added to the start of each mitigation preview"""
def get_markdown_for_mitigation_prefix(m_id, kb=None):
    return ""

"""Markdown text to be added to the end of each mitigation preview"""
def get_markdown_for_mitigation_suffix(m_id, kb=None):
    return ""



# HTML Code
# ---------
"""HTML text to be added to the main page"""
def get_html_generic(kb=None):
    return ""

"""HTML text to be added to the end of each technique detail panel"""
def get_html_for_technique(t_id, kb=None):
    return ""

"""HTML text to be added as a suffix in technique preview cells"""
def get_html_for_technique_suffix(t_id, kb=None):
    return ""

"""HTML text to be added to the end of each weakness detail panel"""
def get_html_for_weakness(w_id, kb=None):
    return ""

"""HTML text to be added as a prefix in weakness preview rows"""
def get_html_for_weakness_prefix(w_id, kb=None):
    return ""

"""HTML text to be added as a suffix in weakness preview rows"""
def get_html_for_weakness_suffix(w_id, kb=None):
    return ""

"""HTML text to be added to the end of each mitigation detail panel"""
def get_html_for_mitigation(m_id, kb=None):
    return ""

"""HTML text to be added as a prefix in mitigation preview rows"""
def get_html_for_mitigation_prefix(m_id, kb=None):
    return ""

"""HTML text to be added as a suffix in mitigation preview rows"""
def get_html_for_mitigation_suffix(m_id, kb=None):
    return ""


# Excel Code
# ----------
"""General modifications to be made to the workbook"""
def get_excel_generic(excel_worksheet, start_row, kb=None):
    return excel_worksheet

"""Modifications to be made to the workbook for each technique"""
def get_excel_for_technique(t_id, excel_worksheet, start_row, kb=None):
    return excel_worksheet

"""Modifications to be made to the workbook for each weakness"""
def get_excel_for_weakness(w_id, excel_worksheet, start_row, kb=None):
    return excel_worksheet

"""Modifications to be made to the workbook for each mitigation"""
def get_excel_for_mitigation(m_id, excel_worksheet, start_row, kb=None):
    return excel_worksheet