---
name: docx-generation
description: Comprehensive skill for authoring official corporate Word (.docx) technical approval notes, specifications, and engineering dossiers using python-docx with enterprise styling.
version: 1.0.0
triggers:
  - docx
  - word document
  - technical note
  - approval note
  - specification document
  - engineering dossier
  - written report
tools:
  - execute_terminal_command
---

# Professional Word (.docx) Document Generation Skill

## Purpose
Enables KRIYA to author beautifully formatted, corporate-grade Microsoft Word (`.docx`) documents for official refinery engineering sign-offs, technical approval notes, and inspection dossiers.

## Environment & Tooling
- **Runtime**: Python 3 with `python-docx` (pre-installed).
- **Execution**: Write a Python script in the active workspace and execute it using `execute_terminal_command` (e.g. `python3 make_doc.py`).
- **Target Output Directory**: Save directly to `./` (the active chat workspace) or `./documents/`.

## Document Design Standards

### 1. Document Typography & Palette
- **Document Title**: 24pt Bold, Dark Navy (`#1E3A8A` or RGB `30, 58, 138`).
- **Heading 1**: 16pt Bold, Navy (`#1E3A8A`), with a bottom border or underline.
- **Heading 2**: 13pt Semi-Bold, Slate (`#334155` or RGB `51, 65, 85`).
- **Body Text**: 10.5pt Calibri or Arial, Off-Black (`#1F2937`), 1.15 line spacing, 6pt after.
- **Header & Footer**: Subdued grey, includes Document ID, Date, Confidentiality notice, and Page Number.

### 2. Standard Approval Note Structure
1. **Header Block / Metadata Table**:
   - Project / Asset: (e.g. `CDU-II / 01-C-101 Overhead Vapor Line`)
   - Document Ref: (e.g. `MRPL/ENG/2026/AN-402`)
   - Date & Revision: (e.g. `2026-09-28 | Rev 1.0`)
   - Target Signatories: Lead Process Engineer, Head of Asset Integrity, Refinery Director.
2. **Executive Summary**: Clear 1-2 paragraph description of the finding, urgency, and recommended action.
3. **Technical Findings & NDT Data**: Formatted table displaying inspection results, measured thickness, minimum allowable thickness, corrosion rates, and category defect levels.
4. **SOP Compliance Matrix**: Exact citations to MRPL standard operating procedures (e.g. `SOP-MRPL-4.2.3`).
5. **Cost & Schedule Impact Summary**: Brief summary with cross-reference to accompanying Excel workbooks.
6. **Formal Sign-off Block**: Sign-off signature boxes for approval.

### 3. Implementation Python Script Blueprint

```python
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

doc = docx.Document()

# Set standard 1-inch margins
for section in doc.sections:
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)
    section.left_margin = Inches(1)
    section.right_margin = Inches(1)

# Title
title_p = doc.add_paragraph()
title_run = title_p.add_run("TECHNICAL APPROVAL NOTE")
title_run.font.size = Pt(22)
title_run.font.bold = True
title_run.font.color.rgb = RGBColor(30, 58, 138)

# Table Styling Helper
def style_table(table, col_widths, headers, data):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Header Row
    hdr_cells = table.rows[0].cells
    for i, title in enumerate(headers):
        hdr_cells[i].text = title
        p = hdr_cells[i].paragraphs[0]
        p.runs[0].font.bold = True
        p.runs[0].font.color.rgb = RGBColor(255, 255, 255)
        # Background color
        shading = parse_xml(r'<w:shd {} w:fill="1E3A8A"/>'.format(nsdecls('w')))
        hdr_cells[i]._tc.get_or_add_tcPr().append(shading)
    
    # Data Rows
    for r_idx, row_data in enumerate(data):
        row_cells = table.add_row().cells
        bg_color = "F8FAFC" if r_idx % 2 == 1 else "FFFFFF"
        for c_idx, val in enumerate(row_data):
            row_cells[c_idx].text = str(val)
            shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{bg_color}"/>')
            row_cells[c_idx]._tc.get_or_add_tcPr().append(shading)

# Save output
doc.save("Approval_Note.docx")
print("Saved Approval_Note.docx successfully.")
```

## Workflow Execution
1. Identify all required data (equipment tags, readings, recommendations).
2. Author the Python generation script in the workspace (using `execute_terminal_command`).
3. Run `python3 generate_docs.py`.
4. Verify file existence and size using `execute_terminal_command(command="ls -lh *.docx")`.
