# ==============================================================================
# KRIYA Tool: Enterprise Document & Deliverable Generators (DOCX, XLSX, PPTX)
# ==============================================================================
# Provides rich, corporate-grade document generation tools with:
# - Document Control Metadata Blocks
# - Auto-parsed Markdown & Structured Engineering Tables
# - Formal Multi-Tier Authorization & Signature Columns / Sign-Off Blocks
# - Automatic registration in the active chat workspace for UI Download & Host Share
# ==============================================================================

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml
from docx.oxml.ns import nsdecls

import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from pptx import Presentation
from pptx.util import Inches as PptInches, Pt as PptPt
from pptx.dml.color import RGBColor as PptRGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE


def _get_output_path(filename: str, default_ext: str) -> Path:
    """Resolves target output path inside the active chat workspace."""
    clean_name = Path(filename or f"KRIYA_Deliverable.{default_ext}").name
    if not clean_name.lower().endswith(f".{default_ext}"):
        clean_name = f"{clean_name}.{default_ext}"

    try:
        from agent.workspace.workspace_manager import get_active_workspace_dir
        ws_dir = get_active_workspace_dir()
    except Exception:
        ws_dir = Path("/app/workspace/chats/default_chat")

    ws_dir.mkdir(parents=True, exist_ok=True)
    return ws_dir / clean_name


def _set_cell_background(cell: Any, hex_color: str) -> None:
    """Sets background shading on a python-docx table cell."""
    shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
    cell._tc.get_or_add_tcPr().append(shading)


def _set_cell_margins(cell: Any, top: int = 100, bottom: int = 100, left: int = 140, right: int = 140) -> None:
    """Sets internal padding (in dxa) for a python-docx table cell."""
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(
        f'<w:tcMar {nsdecls("w")}>'
        f'<w:top w:w="{top}" w:type="dxa"/>'
        f'<w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'<w:left w:w="{left}" w:type="dxa"/>'
        f'<w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    tcPr.append(tcMar)


def _style_docx_table(
    table: Any,
    headers: List[str],
    rows: List[List[Any]],
    header_bg: str = "1E3A8A",
    row_height_inches: Optional[float] = None,
) -> None:
    """Applies corporate navy headers, zebra striping, and cell padding to a Word table."""
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.autofit = True

    # Style Header Row
    hdr_cells = table.rows[0].cells
    for i, h_text in enumerate(headers):
        if i >= len(hdr_cells):
            break
        hdr_cells[i].text = ""
        p = hdr_cells[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        run = p.add_run(str(h_text))
        run.font.name = "Calibri"
        run.font.size = Pt(10)
        run.font.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        _set_cell_background(hdr_cells[i], header_bg)
        _set_cell_margins(hdr_cells[i], top=120, bottom=120, left=140, right=140)
        hdr_cells[i].vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    # Style Data Rows
    for r_idx, r_data in enumerate(rows):
        row_obj = table.add_row()
        if row_height_inches:
            row_obj.height = Inches(row_height_inches)
        row_cells = row_obj.cells
        bg = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(r_data):
            if c_idx >= len(row_cells):
                break
            row_cells[c_idx].text = ""
            p = row_cells[c_idx].paragraphs[0]
            run = p.add_run(str(val if val is not None else ""))
            run.font.name = "Calibri"
            run.font.size = Pt(9.5)
            run.font.color.rgb = RGBColor(30, 41, 59)
            if c_idx == 0:
                run.font.bold = True
            _set_cell_background(row_cells[c_idx], bg)
            _set_cell_margins(row_cells[c_idx], top=100, bottom=100, left=140, right=140)
            row_cells[c_idx].vertical_alignment = WD_ALIGN_VERTICAL.CENTER


def _add_formatted_runs(paragraph: Any, text: str) -> None:
    """Parses inline **bold** markers into formatted Word runs."""
    parts = re.split(r"(\*\*.*?\*\*)", text)
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            run = paragraph.add_run(part[2:-2])
            run.font.bold = True
        else:
            run = paragraph.add_run(part)
        run.font.name = "Calibri"
        run.font.size = Pt(10.5)
        run.font.color.rgb = RGBColor(31, 41, 55)


def _render_markdown_block_to_docx(doc: Any, text: str) -> None:
    """Renders markdown-like text (headings, bullets, markdown tables, paragraphs) into a Word doc."""
    if not text:
        return

    lines = text.splitlines()
    idx = 0
    while idx < len(lines):
        raw_line = lines[idx].strip()
        if not raw_line:
            idx += 1
            continue

        # Detect Markdown Table
        if raw_line.startswith("|") and raw_line.endswith("|") and idx + 1 < len(lines):
            next_line = lines[idx + 1].strip()
            if re.match(r"^\|[\s\-:|]+\|$", next_line):
                headers = [c.strip() for c in raw_line.strip("|").split("|")]
                idx += 2
                table_rows = []
                while idx < len(lines):
                    row_line = lines[idx].strip()
                    if row_line.startswith("|") and row_line.endswith("|"):
                        cells = [c.strip() for c in row_line.strip("|").split("|")]
                        table_rows.append(cells)
                        idx += 1
                    else:
                        break
                if headers:
                    t = doc.add_table(rows=1, cols=len(headers))
                    t.style = "Table Grid"
                    _style_docx_table(t, headers, table_rows)
                    doc.add_paragraph()
                continue

        # Headings
        if raw_line.startswith("### "):
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(4)
            r = h.add_run(raw_line[4:].strip())
            r.font.name = "Calibri"
            r.font.size = Pt(12)
            r.font.bold = True
            r.font.color.rgb = RGBColor(51, 65, 85)
        elif raw_line.startswith("## ") or raw_line.startswith("# "):
            clean_h = raw_line.lstrip("#").strip()
            h = doc.add_paragraph()
            h.paragraph_format.space_before = Pt(14)
            h.paragraph_format.space_after = Pt(6)
            r = h.add_run(clean_h)
            r.font.name = "Calibri"
            r.font.size = Pt(14)
            r.font.bold = True
            r.font.color.rgb = RGBColor(30, 58, 138)
        elif raw_line.startswith("- ") or raw_line.startswith("* "):
            p = doc.add_paragraph(style="List Bullet")
            p.paragraph_format.space_after = Pt(3)
            _add_formatted_runs(p, raw_line[2:].strip())
        elif re.match(r"^\d+\.\s+", raw_line):
            clean_item = re.sub(r"^\d+\.\s+", "", raw_line)
            p = doc.add_paragraph(style="List Number")
            p.paragraph_format.space_after = Pt(3)
            _add_formatted_runs(p, clean_item)
        else:
            p = doc.add_paragraph()
            p.paragraph_format.space_after = Pt(6)
            p.paragraph_format.line_spacing = 1.15
            _add_formatted_runs(p, raw_line)

        idx += 1


# ==============================================================================
# 1. WORD DOCUMENT GENERATOR (.docx)
# ==============================================================================

def generate_word_document(
    filename: str = "Engineering_Approval_Dossier.docx",
    title: str = "TECHNICAL INSPECTION & APPROVAL DOSSIER",
    subtitle: Optional[str] = "Coastal Refinery & Petrochemicals Ltd (CRPL) — Asset Integrity & Engineering Division",
    document_id: Optional[str] = None,
    asset_tag: Optional[str] = None,
    department: Optional[str] = "Mechanical Maintenance & Inspection",
    prepared_by: Optional[str] = "KRIYA Sovereign AI Engineering Workbench",
    content: Optional[str] = None,
    sections: Optional[List[Dict[str, Any]]] = None,
    tables: Optional[List[Dict[str, Any]]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    include_signature_block: bool = True,
    signatories: Optional[List[Dict[str, str]]] = None,
    **kwargs: Any,
) -> str:
    """
    Generates a comprehensive, corporate-styled Microsoft Word (.docx) engineering report,
    approval note, or inspection dossier complete with Document Control Metadata,
    formatted data tables, and a formal Authorization & Signature Block table.
    """
    target_path = _get_output_path(filename, "docx")
    doc = docx.Document()

    # Configure page margins (0.85 inch for wide tables and signature columns)
    for section in doc.sections:
        section.top_margin = Inches(0.85)
        section.bottom_margin = Inches(0.85)
        section.left_margin = Inches(0.85)
        section.right_margin = Inches(0.85)

        # Configure Corporate Header
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("COASTAL REFINERY & PETROCHEMICALS LTD (CRPL)  |  SOVEREIGN AIR-GAPPED DOSSIER")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = RGBColor(100, 116, 139)

        # Configure Corporate Footer
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        frun = fp.add_run(
            f"CONFIDENTIAL — INTERNAL REFINERY ENGINEERING USE ONLY  |  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  API 510 / API 570 Compliant"
        )
        frun.font.name = "Calibri"
        frun.font.size = Pt(8.5)
        frun.font.color.rgb = RGBColor(100, 116, 139)

    # 1. Corporate Banner & Title Block
    kicker = doc.add_paragraph()
    kicker.paragraph_format.space_after = Pt(2)
    k_run = kicker.add_run("COASTAL REFINERY & PETROCHEMICALS LTD (CRPL — MANGALORE COMPLEX)")
    k_run.font.name = "Calibri"
    k_run.font.size = Pt(9.5)
    k_run.font.bold = True
    k_run.font.color.rgb = RGBColor(2, 132, 199)

    title_p = doc.add_paragraph()
    title_p.paragraph_format.space_after = Pt(4)
    t_run = title_p.add_run(title.upper())
    t_run.font.name = "Calibri"
    t_run.font.size = Pt(20)
    t_run.font.bold = True
    t_run.font.color.rgb = RGBColor(30, 58, 138)

    if subtitle:
        sub_p = doc.add_paragraph()
        sub_p.paragraph_format.space_after = Pt(12)
        s_run = sub_p.add_run(subtitle)
        s_run.font.name = "Calibri"
        s_run.font.size = Pt(11)
        s_run.font.italic = True
        s_run.font.color.rgb = RGBColor(71, 85, 105)

    # 2. Document Control Metadata Grid
    doc_ref = document_id or (metadata or {}).get("document_id") or f"CRPL/ENG/{datetime.now().strftime('%Y')}/AN-{datetime.now().strftime('%m%d')}"
    eq_tag = asset_tag or (metadata or {}).get("asset_tag") or (metadata or {}).get("equipment_tag") or "Refinery Process Asset"
    dept_val = department or (metadata or {}).get("department") or "Mechanical Maintenance & Inspection"
    prep_val = prepared_by or (metadata or {}).get("prepared_by") or "KRIYA Sovereign AI Workbench"
    date_val = (metadata or {}).get("date") or datetime.now().strftime("%d %b %Y")
    rev_val = (metadata or {}).get("revision") or "Rev 1.0 (Final)"
    std_val = (metadata or {}).get("standards") or "API 510 / API 570 / ASME Sec. VIII Div. 1"
    sec_val = (metadata or {}).get("clearance") or "CONFIDENTIAL — Sovereign Air-Gapped"

    meta_table = doc.add_table(rows=4, cols=4)
    meta_table.style = "Table Grid"
    meta_table.alignment = WD_TABLE_ALIGNMENT.CENTER
    meta_pairs = [
        ("Document Ref No.", doc_ref, "Date & Revision", f"{date_val} | {rev_val}"),
        ("Asset / Equipment Tag", eq_tag, "Department / Unit", dept_val),
        ("Prepared By", prep_val, "Governing Standards", std_val),
        ("Security Classification", sec_val, "Document Status", "FOR OFFICIAL REVIEW & SIGN-OFF"),
    ]
    for r_i, (k1, v1, k2, v2) in enumerate(meta_pairs):
        cells = meta_table.rows[r_i].cells
        for c_i, text_val in enumerate([k1, v1, k2, v2]):
            cells[c_i].text = ""
            p = cells[c_i].paragraphs[0]
            run = p.add_run(str(text_val))
            run.font.name = "Calibri"
            run.font.size = Pt(9)
            if c_i in (0, 2):
                run.font.bold = True
                run.font.color.rgb = RGBColor(30, 58, 138)
                _set_cell_background(cells[c_i], "EFF6FF")
            else:
                run.font.color.rgb = RGBColor(30, 41, 59)
                _set_cell_background(cells[c_i], "FFFFFF")
            _set_cell_margins(cells[c_i], top=75, bottom=75, left=100, right=100)

    doc.add_paragraph()

    # 3. Render Main Content / Markdown Body
    if content:
        _render_markdown_block_to_docx(doc, content)

    # 4. Render Structured Sections
    if sections and isinstance(sections, list):
        for sec_idx, sec in enumerate(sections, 1):
            if isinstance(sec, str):
                _render_markdown_block_to_docx(doc, sec)
                continue
            if not isinstance(sec, dict):
                continue

            heading_text = sec.get("heading") or sec.get("title") or f"Section {sec_idx}"
            h_p = doc.add_paragraph()
            h_p.paragraph_format.space_before = Pt(14)
            h_p.paragraph_format.space_after = Pt(6)
            h_run = h_p.add_run(heading_text)
            h_run.font.name = "Calibri"
            h_run.font.size = Pt(13.5)
            h_run.font.bold = True
            h_run.font.color.rgb = RGBColor(30, 58, 138)

            body_text = sec.get("content") or sec.get("body") or sec.get("text") or ""
            if body_text:
                _render_markdown_block_to_docx(doc, str(body_text))

            bullets = sec.get("bullets") or sec.get("items") or []
            for b_item in bullets:
                bp = doc.add_paragraph(style="List Bullet")
                bp.paragraph_format.space_after = Pt(3)
                _add_formatted_runs(bp, str(b_item))

            sec_table = sec.get("table")
            if isinstance(sec_table, dict):
                t_headers = sec_table.get("headers") or []
                t_rows = sec_table.get("rows") or []
                if t_headers:
                    tbl = doc.add_table(rows=1, cols=len(t_headers))
                    tbl.style = "Table Grid"
                    _style_docx_table(tbl, t_headers, t_rows)
                    doc.add_paragraph()

    # 5. Render Standalone Tables
    if tables and isinstance(tables, list):
        for tbl_spec in tables:
            if not isinstance(tbl_spec, dict):
                continue
            t_title = tbl_spec.get("title") or tbl_spec.get("caption")
            if t_title:
                tp = doc.add_paragraph()
                tp.paragraph_format.space_before = Pt(12)
                tp.paragraph_format.space_after = Pt(4)
                tr = tp.add_run(str(t_title))
                tr.font.name = "Calibri"
                tr.font.size = Pt(12)
                tr.font.bold = True
                tr.font.color.rgb = RGBColor(30, 58, 138)

            t_headers = tbl_spec.get("headers") or []
            t_rows = tbl_spec.get("rows") or []
            if t_headers:
                tbl = doc.add_table(rows=1, cols=len(t_headers))
                tbl.style = "Table Grid"
                _style_docx_table(tbl, t_headers, t_rows)
                doc.add_paragraph()

    # 6. Render Formal Multi-Tier Authorization & Signature Block
    if include_signature_block:
        sig_heading = doc.add_paragraph()
        sig_heading.paragraph_format.space_before = Pt(16)
        sig_heading.paragraph_format.space_after = Pt(6)
        sh_run = sig_heading.add_run("AUTHORIZATION, CONCURRENCE & FORMAL SIGN-OFF BLOCK")
        sh_run.font.name = "Calibri"
        sh_run.font.size = Pt(13)
        sh_run.font.bold = True
        sh_run.font.color.rgb = RGBColor(30, 58, 138)

        sig_note = doc.add_paragraph()
        sig_note.paragraph_format.space_after = Pt(6)
        sn_run = sig_note.add_run(
            "In accordance with the Corporate Delegation of Authority (DOA) Matrix and Refinery Asset Integrity SOPs, "
            "the undersigned officers have reviewed and verified the technical calculations, budget allocations, and safety compliance herein:"
        )
        sn_run.font.name = "Calibri"
        sn_run.font.size = Pt(9.5)
        sn_run.font.italic = True
        sn_run.font.color.rgb = RGBColor(71, 85, 105)

        default_signatories = [
            {
                "role": "Prepared & Inspected By (Level 2)",
                "name": "Arun V. Rao (EMP-1008)\nPlant / Inspection Engineer",
                "department": "Inspection & Asset Reliability",
                "scope": "Technical NDT & API 510 Verification",
                "signature": "[ Space for Signature & Seal ]",
                "date": "____ / ____ / 2026",
            },
            {
                "role": "Reviewed & Recommended By (Level 3)",
                "name": "Rajesh K. Sharma (EMP-1005)\nAssistant General Manager (AGM)",
                "department": "Mechanical Maintenance Dept",
                "scope": "DOA Limit: Up to ₹5,00,000 / Scope Review",
                "signature": "[ Space for Signature & Seal ]",
                "date": "____ / ____ / 2026",
            },
            {
                "role": "Financial Concurrence (Level 4)",
                "name": "Sunita Deshpande (EMP-1003)\nGeneral Manager (Finance)",
                "department": "Finance & Accounts",
                "scope": "Cost Center Budget & Rate Contract Audit",
                "signature": "[ Space for Signature & Seal ]",
                "date": "____ / ____ / 2026",
            },
            {
                "role": "Final Approving Authority (Level 4)",
                "name": "K. V. Ramanathan (EMP-1002)\nGeneral Manager (O&M)",
                "department": "Operations & Maintenance",
                "scope": "DOA Limit: Up to ₹25,00,000 (Sanctioned)",
                "signature": "[ Space for Signature & Seal ]",
                "date": "____ / ____ / 2026",
            },
        ]

        active_sigs = signatories if (signatories and isinstance(signatories, list)) else default_signatories
        sig_headers = [
            "Authority Tier / Action",
            "Officer Name & Designation",
            "Department",
            "DOA / Approval Scope",
            "Signature & Official Stamp",
            "Date",
        ]
        sig_rows = []
        for s in active_sigs:
            if isinstance(s, dict):
                sig_rows.append([
                    s.get("role") or s.get("tier") or "Approving Officer",
                    s.get("name") or s.get("officer") or "Designated Signatory",
                    s.get("department") or dept_val,
                    s.get("scope") or s.get("doa") or "Official Sign-Off",
                    s.get("signature") or "[ Space for Signature & Stamp ]",
                    s.get("date") or "____ / ____ / 2026",
                ])

        sig_table = doc.add_table(rows=1, cols=len(sig_headers))
        sig_table.style = "Table Grid"
        _style_docx_table(sig_table, sig_headers, sig_rows, header_bg="0F172A", row_height_inches=0.55)

    doc.save(str(target_path))
    try:
        os.chmod(str(target_path), 0o666)
    except Exception:
        pass

    size_kb = round(target_path.stat().st_size / 1024, 1)
    return (
        f"Successfully generated corporate Word document '{target_path.name}' ({size_kb} KB) "
        f"with Document Control Metadata, formatted engineering tables, and formal Signature & Authorization Block.\n"
        f"[Deliverable Created]: {title} saved to '{target_path.name}'"
    )


# ==============================================================================
# 2. EXCEL WORKBOOK GENERATOR (.xlsx)
# ==============================================================================

def generate_excel_spreadsheet(
    filename: str = "Engineering_Cost_Analysis.xlsx",
    title: str = "CRPL REFINERY — ENGINEERING & FINANCIAL ANALYSIS WORKBOOK",
    sheets: Optional[List[Dict[str, Any]]] = None,
    headers: Optional[List[str]] = None,
    rows: Optional[List[List[Any]]] = None,
    sheet_name: str = "Analysis Summary",
    metadata: Optional[Dict[str, Any]] = None,
    include_signature_block: bool = True,
    signatories: Optional[List[Dict[str, str]]] = None,
    **kwargs: Any,
) -> str:
    """
    Generates a corporate multi-tab Microsoft Excel (.xlsx) workbook with navy header blocks,
    zebra striping, formatted numerical/currency cells, automatic totals, auto-fitted column widths,
    and a formal Verification & Signature sign-off block at the bottom of the sheet.
    """
    target_path = _get_output_path(filename, "xlsx")
    wb = openpyxl.Workbook()
    # Remove default sheet once we add custom sheets
    default_ws = wb.active

    # Normalize input into a list of sheet definitions
    sheet_defs: List[Dict[str, Any]] = []
    if sheets and isinstance(sheets, list):
        sheet_defs = sheets
    elif headers or rows:
        sheet_defs = [{
            "name": sheet_name or "Summary",
            "title": title,
            "headers": headers or [],
            "rows": rows or [],
        }]
    else:
        sheet_defs = [{
            "name": "Summary",
            "title": title,
            "headers": ["Parameter / Item", "Specification / Value", "Unit", "Status / Remarks"],
            "rows": [["Document Initialized", datetime.now().strftime("%Y-%m-%d"), "-", "Verified"]],
        }]

    NAVY_FILL = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    DARK_FILL = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")
    SUB_FILL = PatternFill(start_color="EFF6FF", end_color="EFF6FF", fill_type="solid")
    ZEBRA_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    TOTAL_FILL = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")

    WHITE_BOLD = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    TITLE_FONT = Font(name="Calibri", size=14, bold=True, color="1E3A8A")
    SUB_FONT = Font(name="Calibri", size=10, italic=True, color="475569")
    BOLD_FONT = Font(name="Calibri", size=10.5, bold=True, color="0F172A")
    REG_FONT = Font(name="Calibri", size=10.5, color="1E293B")

    thin_border = Border(
        left=Side(style="thin", color="CBD5E1"),
        right=Side(style="thin", color="CBD5E1"),
        top=Side(style="thin", color="CBD5E1"),
        bottom=Side(style="thin", color="CBD5E1"),
    )

    for s_idx, s_def in enumerate(sheet_defs):
        if not isinstance(s_def, dict):
            continue
        raw_s_name = str(s_def.get("name") or s_def.get("sheet_name") or f"Sheet_{s_idx+1}")[:31]
        ws = default_ws if s_idx == 0 else wb.create_sheet(title=raw_s_name)
        ws.title = raw_s_name
        ws.views.sheetView[0].showGridLines = True

        s_title = s_def.get("title") or title
        s_headers = s_def.get("headers") or s_def.get("columns") or []
        s_rows = s_def.get("rows") or s_def.get("data") or []

        # If rows are dicts, convert to lists matching headers
        if s_rows and isinstance(s_rows[0], dict):
            if not s_headers:
                s_headers = list(s_rows[0].keys())
            s_rows = [[r.get(h, "") for h in s_headers] for r in s_rows]

        num_cols = max(len(s_headers), 6)
        last_col_letter = get_column_letter(num_cols)

        # Row 1: Title Banner
        ws.merge_cells(f"A1:{last_col_letter}1")
        ws["A1"] = s_title.upper()
        ws["A1"].font = TITLE_FONT
        ws["A1"].fill = SUB_FILL
        ws["A1"].alignment = Alignment(horizontal="left", vertical="center", indent=1)
        ws.row_dimensions[1].height = 28

        # Row 2: Metadata Subtitle
        ws.merge_cells(f"A2:{last_col_letter}2")
        doc_ref = (metadata or {}).get("document_id") or f"CRPL-WB-{datetime.now().strftime('%Y%m%d')}"
        ws["A2"] = f"Coastal Refinery & Petrochemicals Ltd (CRPL)  |  Ref: {doc_ref}  |  Generated: {datetime.now().strftime('%d %b %Y %H:%M')}  |  Sovereign Air-Gapped"
        ws["A2"].font = SUB_FONT
        ws.row_dimensions[2].height = 20

        # Row 4: Table Headers
        header_row = 4
        if s_headers:
            ws.row_dimensions[header_row].height = 24
            for c_idx, h_val in enumerate(s_headers, 1):
                cell = ws.cell(row=header_row, column=c_idx, value=str(h_val))
                cell.fill = NAVY_FILL
                cell.font = WHITE_BOLD
                cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
                cell.border = thin_border

        # Data Rows
        current_row = header_row + 1
        for r_offset, r_vals in enumerate(s_rows):
            ws.row_dimensions[current_row].height = 20
            is_zebra = r_offset % 2 == 1
            for c_idx, val in enumerate(r_vals, 1):
                cell = ws.cell(row=current_row, column=c_idx, value=val)
                cell.font = BOLD_FONT if c_idx == 1 else REG_FONT
                cell.border = thin_border
                if is_zebra:
                    cell.fill = ZEBRA_FILL
                if isinstance(val, (int, float)):
                    cell.alignment = Alignment(horizontal="right", vertical="center")
                    if any(k in str(s_headers[c_idx-1]).lower() for k in ["cost", "rate", "budget", "inr", "price", "amount", "bid", "₹"]) if c_idx <= len(s_headers) else False:
                        cell.number_format = "₹#,##0.00"
                    elif isinstance(val, float):
                        cell.number_format = "#,##0.00"
                    else:
                        cell.number_format = "#,##0"
                else:
                    cell.alignment = Alignment(horizontal="left", vertical="center", wrap_text=True)
            current_row += 1

        # Add Sign-Off / Signature Block on the first sheet (or if requested)
        if include_signature_block and s_idx == 0:
            current_row += 2
            ws.merge_cells(f"A{current_row}:{last_col_letter}{current_row}")
            ws.cell(row=current_row, column=1, value="AUTHORIZATION, VERIFICATION & SIGN-OFF BLOCK").font = Font(
                name="Calibri", size=11, bold=True, color="1E3A8A"
            )
            current_row += 1

            sig_headers = ["Authority Role", "Officer Name & Designation", "Department", "Approval Scope / DOA", "Signature & Stamp", "Date"]
            ws.row_dimensions[current_row].height = 22
            for c_i, sh in enumerate(sig_headers, 1):
                scell = ws.cell(row=current_row, column=c_i, value=sh)
                scell.fill = DARK_FILL
                scell.font = WHITE_BOLD
                scell.alignment = Alignment(horizontal="center", vertical="center")
                scell.border = thin_border
            current_row += 1

            default_sigs = signatories or [
                {"role": "Prepared & Verified By", "name": "Arun V. Rao (EMP-1008) — Inspection Eng.", "dept": "Inspection & Reliability", "scope": "Technical Data & Calculations", "sig": "[ Signed / Verified ]", "date": datetime.now().strftime("%Y-%m-%d")},
                {"role": "Reviewed By (AGM)", "name": "Rajesh K. Sharma (EMP-1005) — AGM Maint.", "dept": "Mechanical Maintenance", "scope": "DOA Limit: ₹5,00,000", "sig": "[ Space for Signature ]", "date": "____/____/2026"},
                {"role": "Finance Concurrence", "name": "Sunita Deshpande (EMP-1003) — GM Finance", "dept": "Finance & Accounts", "scope": "Budget & Rate Contract Check", "sig": "[ Space for Signature ]", "date": "____/____/2026"},
                {"role": "Approved By (GM O&M)", "name": "K. V. Ramanathan (EMP-1002) — GM O&M", "dept": "Operations & Maintenance", "scope": "DOA Limit: ₹25,00,000", "sig": "[ Space for Signature ]", "date": "____/____/2026"},
            ]
            for s_item in default_sigs:
                ws.row_dimensions[current_row].height = 28
                vals = [
                    s_item.get("role", "Approver"),
                    s_item.get("name", ""),
                    s_item.get("department") or s_item.get("dept", ""),
                    s_item.get("scope", "Official Sign-Off"),
                    s_item.get("signature") or s_item.get("sig", "[ Space for Signature & Stamp ]"),
                    s_item.get("date", "____/____/2026"),
                ]
                for c_i, v in enumerate(vals, 1):
                    c = ws.cell(row=current_row, column=c_i, value=v)
                    c.font = BOLD_FONT if c_i == 1 else REG_FONT
                    c.border = thin_border
                    c.alignment = Alignment(horizontal="center" if c_i in (5, 6) else "left", vertical="center")
                current_row += 1

        # Auto-fit columns cleanly
        for col in ws.columns:
            col_letter = get_column_letter(col[0].column)
            max_len = 0
            for cell in col:
                if cell.row in (1, 2):
                    continue
                val_str = str(cell.value or "")
                max_len = max(max_len, len(val_str))
            ws.column_dimensions[col_letter].width = max(min(max_len + 4, 42), 14)

        ws.freeze_panes = "A5"

    wb.save(str(target_path))
    try:
        os.chmod(str(target_path), 0o666)
    except Exception:
        pass

    size_kb = round(target_path.stat().st_size / 1024, 1)
    return (
        f"Successfully generated corporate Excel workbook '{target_path.name}' ({size_kb} KB) "
        f"with {len(sheet_defs)} tab(s) and formal Verification & Signature Block.\n"
        f"[Deliverable Created]: {title} saved to '{target_path.name}'"
    )


# ==============================================================================
# 3. POWERPOINT PRESENTATION GENERATOR (.pptx)
# ==============================================================================

def generate_powerpoint_deck(
    filename: str = "Executive_Engineering_Briefing.pptx",
    title: str = "EXECUTIVE ASSET INTEGRITY & REMEDIATION BRIEFING",
    subtitle: str = "Coastal Refinery & Petrochemicals Ltd (CRPL) — Engineering & Finance Review",
    presenter: str = "K. V. Ramanathan (GM O&M) & Arun V. Rao (Inspection Engineer)",
    slides: Optional[List[Dict[str, Any]]] = None,
    include_signoff_slide: bool = True,
    **kwargs: Any,
) -> str:
    """
    Generates a 16:9 widescreen executive PowerPoint (.pptx) presentation deck
    with a dark navy cover slide, structured content/table/KPI slides, and a
    Governance & Sign-Off Authority slide.
    """
    target_path = _get_output_path(filename, "pptx")
    prs = Presentation()
    prs.slide_width = PptInches(13.333)
    prs.slide_height = PptInches(7.5)
    blank_layout = prs.slide_layouts[6]

    # 1. Cover Slide (Dark Navy Theme)
    s1 = prs.slides.add_slide(blank_layout)
    bg = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(7.5))
    bg.fill.solid()
    bg.fill.fore_color.rgb = PptRGBColor(15, 23, 42)
    bg.line.fill.background()

    accent = s1.shapes.add_shape(MSO_SHAPE.RECTANGLE, PptInches(1.0), PptInches(1.8), PptInches(0.12), PptInches(3.6))
    accent.fill.solid()
    accent.fill.fore_color.rgb = PptRGBColor(56, 189, 248)
    accent.line.fill.background()

    tb = s1.shapes.add_textbox(PptInches(1.35), PptInches(1.75), PptInches(10.8), PptInches(4.2))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "COASTAL REFINERY & PETROCHEMICALS LTD (CRPL)"
    p0.font.size = PptPt(13)
    p0.font.bold = True
    p0.font.color.rgb = PptRGBColor(56, 189, 248)

    p1 = tf.add_paragraph()
    p1.text = title.upper()
    p1.font.size = PptPt(34)
    p1.font.bold = True
    p1.font.color.rgb = PptRGBColor(255, 255, 255)

    p2 = tf.add_paragraph()
    p2.text = subtitle
    p2.font.size = PptPt(18)
    p2.font.color.rgb = PptRGBColor(203, 213, 225)

    p3 = tf.add_paragraph()
    p3.text = f"\nPrepared By: {presenter}  |  Date: {datetime.now().strftime('%d %b %Y')}  |  Sovereign Air-Gapped Appliance"
    p3.font.size = PptPt(12)
    p3.font.color.rgb = PptRGBColor(148, 163, 184)

    # 2. Content Slides
    slide_list = slides if (slides and isinstance(slides, list)) else []
    for sl_spec in slide_list:
        if not isinstance(sl_spec, dict):
            continue
        sl = prs.slides.add_slide(blank_layout)

        # Header Bar
        hbar = sl.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(1.05))
        hbar.fill.solid()
        hbar.fill.fore_color.rgb = PptRGBColor(30, 58, 138)
        hbar.line.fill.background()

        htb = sl.shapes.add_textbox(PptInches(0.7), PptInches(0.22), PptInches(11.8), PptInches(0.65))
        hp = htb.text_frame.paragraphs[0]
        hp.text = str(sl_spec.get("title") or sl_spec.get("heading") or "Engineering Analysis")
        hp.font.size = PptPt(22)
        hp.font.bold = True
        hp.font.color.rgb = PptRGBColor(255, 255, 255)

        y_cursor = 1.35

        # Optional KPI Cards
        kpis = sl_spec.get("kpis") or []
        if kpis and isinstance(kpis, list):
            for k_idx, kpi in enumerate(kpis[:4]):
                if not isinstance(kpi, dict):
                    continue
                card_w = 2.85
                x_pos = 0.7 + k_idx * 3.05
                card = sl.shapes.add_shape(
                    MSO_SHAPE.ROUNDED_RECTANGLE,
                    PptInches(x_pos),
                    PptInches(y_cursor),
                    PptInches(card_w),
                    PptInches(1.35),
                )
                card.fill.solid()
                card.fill.fore_color.rgb = PptRGBColor(248, 250, 252)
                card.line.color.rgb = PptRGBColor(2, 132, 199)
                card.line.width = PptPt(1.5)

                ctf = card.text_frame
                ctf.word_wrap = True
                vp = ctf.paragraphs[0]
                vp.text = str(kpi.get("value") or "")
                vp.font.size = PptPt(22)
                vp.font.bold = True
                vp.font.color.rgb = PptRGBColor(30, 58, 138)
                vp.alignment = PP_ALIGN.CENTER

                lp = ctf.add_paragraph()
                lp.text = str(kpi.get("label") or "")
                lp.font.size = PptPt(10.5)
                lp.font.color.rgb = PptRGBColor(71, 85, 105)
                lp.alignment = PP_ALIGN.CENTER
            y_cursor += 1.6

        # Bullets / Text Content
        bullets = sl_spec.get("bullets") or sl_spec.get("points") or sl_spec.get("content") or []
        if isinstance(bullets, str):
            bullets = [line.strip("- *") for line in bullets.splitlines() if line.strip()]
        if bullets and isinstance(bullets, list):
            btb = sl.shapes.add_textbox(PptInches(0.75), PptInches(y_cursor), PptInches(11.8), PptInches(4.8))
            btf = btb.text_frame
            btf.word_wrap = True
            for b_i, b_text in enumerate(bullets):
                bp = btf.paragraphs[0] if b_i == 0 else btf.add_paragraph()
                bp.text = f"•  {str(b_text)}"
                bp.font.size = PptPt(15)
                bp.font.color.rgb = PptRGBColor(30, 41, 59)
                bp.space_after = PptPt(10)

    # 3. Governance & Sign-Off Slide
    if include_signoff_slide:
        sl_gov = prs.slides.add_slide(blank_layout)
        hbar = sl_gov.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, PptInches(13.333), PptInches(1.05))
        hbar.fill.solid()
        hbar.fill.fore_color.rgb = PptRGBColor(15, 23, 42)
        hbar.line.fill.background()

        htb = sl_gov.shapes.add_textbox(PptInches(0.7), PptInches(0.22), PptInches(11.8), PptInches(0.65))
        hp = htb.text_frame.paragraphs[0]
        hp.text = "GOVERNANCE, DOA AUTHORIZATION & SIGN-OFF MATRIX"
        hp.font.size = PptPt(22)
        hp.font.bold = True
        hp.font.color.rgb = PptRGBColor(255, 255, 255)

        rows_data = [
            ["Authority Tier", "Officer Name & Designation", "Department", "DOA / Approval Scope", "Signature & Stamp"],
            ["Prepared By (L2)", "Arun V. Rao (EMP-1008)", "Inspection & Reliability", "API 510 / NDT Verification", "[ Verified ]"],
            ["Reviewed By (L3)", "Rajesh K. Sharma (EMP-1005)", "Mechanical Maintenance", "AGM Maintenance (Up to ₹5L)", "[ Space for Sign ]"],
            ["Finance Audit (L4)", "Sunita Deshpande (EMP-1003)", "Finance & Accounts", "Budget & Rate Contract Concurrence", "[ Space for Sign ]"],
            ["Final Approval (L4)", "K. V. Ramanathan (EMP-1002)", "Operations & Maintenance", "GM O&M Sanction (Up to ₹25L)", "[ Space for Sign ]"],
        ]
        tbl_shape = sl_gov.shapes.add_table(len(rows_data), 5, PptInches(0.7), PptInches(1.6), PptInches(11.9), PptInches(4.5))
        ppt_tbl = tbl_shape.table
        for r_i, r_list in enumerate(rows_data):
            for c_i, val in enumerate(r_list):
                cell = ppt_tbl.cell(r_i, c_i)
                cell.text = val
                p = cell.text_frame.paragraphs[0]
                p.font.size = PptPt(12 if r_i == 0 else 11)
                p.font.bold = (r_i == 0 or c_i == 0)
                if r_i == 0:
                    p.font.color.rgb = PptRGBColor(255, 255, 255)
                    cell.fill.solid()
                    cell.fill.fore_color.rgb = PptRGBColor(30, 58, 138)
                else:
                    p.font.color.rgb = PptRGBColor(30, 41, 59)

    prs.save(str(target_path))
    try:
        os.chmod(str(target_path), 0o666)
    except Exception:
        pass

    size_kb = round(target_path.stat().st_size / 1024, 1)
    return (
        f"Successfully generated corporate 16:9 PowerPoint presentation '{target_path.name}' ({size_kb} KB) "
        f"with {len(prs.slides)} slides including Governance & Sign-Off Matrix.\n"
        f"[Deliverable Created]: {title} saved to '{target_path.name}'"
    )


# ==============================================================================
# OPENAI FUNCTION SCHEMAS
# ==============================================================================

GENERATE_WORD_DOCUMENT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_word_document",
        "description": (
            "Generates a detailed, enterprise-styled Microsoft Word (.docx) technical report, approval note, "
            "or inspection dossier complete with a Corporate Header, Document Control Metadata Table, "
            "formatted engineering/financial tables, and a formal Multi-Tier Authorization & Signature Block table "
            "(with Signature & Official Stamp columns). Prefer this tool whenever creating .docx deliverables."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Output filename ending in .docx (e.g. '10-E-101_Approval_Note.docx')"
                },
                "title": {
                    "type": "string",
                    "description": "Main document title (e.g. 'TECHNICAL APPROVAL NOTE: EXCHANGER 10-E-101 TUBE BUNDLE REPLACEMENT')"
                },
                "subtitle": {
                    "type": "string",
                    "description": "Document subtitle or division header"
                },
                "document_id": {
                    "type": "string",
                    "description": "Document reference number (e.g. 'CRPL/ENG/2026/AN-101')"
                },
                "asset_tag": {
                    "type": "string",
                    "description": "Target equipment or asset tag (e.g. '10-E-101 (CDU-1 Crude Pre-Heat Exchanger)')"
                },
                "department": {
                    "type": "string",
                    "description": "Responsible department (e.g. 'Mechanical Maintenance & Inspection')"
                },
                "prepared_by": {
                    "type": "string",
                    "description": "Author name and designation (e.g. 'Arun V. Rao (EMP-1008) / K. V. Ramanathan (EMP-1002)')"
                },
                "content": {
                    "type": "string",
                    "description": (
                        "Comprehensive Markdown content for the report body. Supports ## Headings, **bold**, "
                        "bullet points (- ), numbered lists, and Markdown tables (| Col1 | Col2 |). "
                        "Include thorough Executive Summary, Technical Specifications, Ultrasonic Thickness & Corrosion Calculations, "
                        "Financial/Budget Analysis, and Recommendations."
                    )
                },
                "tables": {
                    "type": "array",
                    "description": "Optional list of structured tables to render with corporate navy styling: [{'title': '...', 'headers': ['Col1', 'Col2'], 'rows': [['v1', 'v2']]}]",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "headers": {"type": "array", "items": {"type": "string"}},
                            "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}
                        }
                    }
                },
                "include_signature_block": {
                    "type": "boolean",
                    "description": "Whether to append the formal Authorization, DOA & Signature Block table at the bottom (default: true)"
                },
                "signatories": {
                    "type": "array",
                    "description": "Optional custom rows for the Signature table: [{'role': '...', 'name': '...', 'department': '...', 'scope': '...', 'signature': '[ Space for Signature ]', 'date': '...'}]",
                    "items": {
                        "type": "object",
                        "properties": {
                            "role": {"type": "string"},
                            "name": {"type": "string"},
                            "department": {"type": "string"},
                            "scope": {"type": "string"},
                            "signature": {"type": "string"},
                            "date": {"type": "string"}
                        }
                    }
                }
            },
            "required": ["filename", "title"]
        }
    }
}

GENERATE_EXCEL_SPREADSHEET_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_excel_spreadsheet",
        "description": (
            "Generates a professional, multi-tab Microsoft Excel (.xlsx) engineering or financial workbook "
            "with corporate Navy headers, zebra striping, currency/numerical formatting, auto-fitted columns, "
            "and a formal Verification & Signature Block at the bottom."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Output filename ending in .xlsx (e.g. 'E101_Thickness_and_Cost_Analysis.xlsx')"
                },
                "title": {
                    "type": "string",
                    "description": "Main workbook banner title"
                },
                "sheet_name": {
                    "type": "string",
                    "description": "Primary worksheet tab name (if passing headers and rows directly)"
                },
                "headers": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Column headers for the primary worksheet"
                },
                "rows": {
                    "type": "array",
                    "items": {"type": "array", "items": {}},
                    "description": "2D array of row values matching headers"
                },
                "sheets": {
                    "type": "array",
                    "description": "Optional multi-tab definition: [{'name': 'Tab1', 'title': '...', 'headers': [...], 'rows': [[...]]}]",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "title": {"type": "string"},
                            "headers": {"type": "array", "items": {"type": "string"}},
                            "rows": {"type": "array", "items": {"type": "array", "items": {}}}
                        }
                    }
                },
                "include_signature_block": {
                    "type": "boolean",
                    "description": "Whether to append the formal Verification & Signature Block at the bottom of the sheet (default: true)"
                }
            },
            "required": ["filename", "title"]
        }
    }
}

GENERATE_POWERPOINT_DECK_SCHEMA = {
    "type": "function",
    "function": {
        "name": "generate_powerpoint_deck",
        "description": (
            "Generates a 16:9 widescreen executive PowerPoint (.pptx) presentation deck with a dark navy cover slide, "
            "KPI callout cards, technical bullet slides, and a Governance & DOA Signature Matrix slide."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "filename": {
                    "type": "string",
                    "description": "Output filename ending in .pptx (e.g. '10-E-101_Executive_Presentation.pptx')"
                },
                "title": {
                    "type": "string",
                    "description": "Presentation main title"
                },
                "subtitle": {
                    "type": "string",
                    "description": "Presentation subtitle"
                },
                "presenter": {
                    "type": "string",
                    "description": "Author / presenter name and designation"
                },
                "slides": {
                    "type": "array",
                    "description": "List of content slides: [{'title': '...', 'kpis': [{'value': '0.35 mm/yr', 'label': 'Corrosion Rate'}], 'bullets': ['Point 1', 'Point 2']}]",
                    "items": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "kpis": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "value": {"type": "string"},
                                        "label": {"type": "string"}
                                    }
                                }
                            },
                            "bullets": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "include_signoff_slide": {
                    "type": "boolean",
                    "description": "Whether to include the final Governance & Signature Matrix slide (default: true)"
                }
            },
            "required": ["filename", "title"]
        }
    }
}
