---
name: xlsx-generation
description: Comprehensive skill for authoring multi-tab, professional financial and engineering Excel (.xlsx) workbooks with openpyxl, formatting, formulas, and auto-sizing.
version: 1.0.0
triggers:
  - xlsx
  - excel workbook
  - cost spreadsheet
  - budget analysis
  - capex opex
  - turnaround cost
  - financial model
tools:
  - execute_terminal_command
---

# Professional Excel (.xlsx) Workbook Generation Skill

## Purpose
Enables KRIYA to author structured, multi-tab Microsoft Excel (`.xlsx`) workbooks for turnaround estimation, equipment repair cost analysis, and asset integrity budgets with real Excel formulas and corporate styling.

## Environment & Tooling
- **Runtime**: Python 3 with `openpyxl` and `pandas` (pre-installed).
- **Execution**: Write a Python script in the active workspace and execute it using `execute_terminal_command` (e.g. `python3 make_sheet.py`).
- **Target Output Directory**: Save directly to `./` (the active chat workspace) or `./documents/`.

## Workbook Design Standards

### 1. Structure & Layout
- **Multi-Tab Organization**:
  - `Tab 1: Summary`: High-level CAPEX/OPEX figures, KPI cards, turnaround schedule estimates.
  - `Tab 2: Cost Breakdown`: Itemized materials, fabrication, labor, scaffolding, and NDT inspection costs.
  - `Tab 3: Equipment Data`: Dimensional measurements, TML readings, and vendor catalogue prices.
- **Visual Palette**:
  - Primary Header: Deep Steel Navy (`#1E3A8A` or hex `1E3A8A`), font color White (`FFFFFF`).
  - Total / Accent Row: Soft Slate (`#E2E8F0`), font bold.
  - Zebra Striping: Alternating rows `#F8FAFC` and `#FFFFFF`.
- **Formatting Rules**:
  - **Formulas**: Always use UPPERCASE formula names: `=SUM(E4:E12)`, `=AVERAGE(D4:D20)`. Never hardcode calculations where a formula is appropriate.
  - **Currency**: Explicit format `#,,##0` or `[$₹-4009] #,##0.00` for INR values.
  - **Column Width**: Auto-fit column widths with padding so cells never display `###`.
  - **Freeze Panes**: Freeze header rows (`ws.freeze_panes = "A4"`).

### 2. Implementation Python Script Blueprint

```python
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Cost Analysis"
ws.views.sheetView[0].showGridLines = True

# Palettes
NAVY_FILL = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
ZEBRA_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
TOTAL_FILL = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
WHITE_FONT_BOLD = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
BOLD_FONT = Font(name="Calibri", size=11, bold=True)
REG_FONT = Font(name="Calibri", size=11)

thin_border = Border(
    left=Side(style='thin', color='CBD5E1'),
    right=Side(style='thin', color='CBD5E1'),
    top=Side(style='thin', color='CBD5E1'),
    bottom=Side(style='thin', color='CBD5E1')
)

# 1. Title Block
ws.merge_cells("A1:F1")
ws["A1"] = "MRPL REFINERY — CDU-II ASSET REMEDIATION COST ANALYSIS"
ws["A1"].font = Font(name="Calibri", size=14, bold=True, color="1E3A8A")

# 2. Table Headers
headers = ["Item #", "Description", "Qty", "Unit", "Rate (INR)", "Total Cost (INR)"]
row_start = 3
for col_idx, h in enumerate(headers, 1):
    cell = ws.cell(row=row_start, column=col_idx, value=h)
    cell.fill = NAVY_FILL
    cell.font = WHITE_FONT_BOLD
    cell.alignment = Alignment(horizontal="center", vertical="center")

# 3. Data Rows
items = [
    ("1.1", "Seamless CS Pipe Spool 18\" (ASTM A106 Gr. B)", 24, "Meters", 18500),
    ("1.2", "Long Radius 90-Deg Elbows 18\" Sch 40", 4, "Nos", 42000),
    ("1.3", "Ultrasonic Thickness & Radiography Testing", 1, "Lot", 125000),
    ("1.4", "Field Rigging, Scaffolding & Mechanical Labor", 1, "Lot", 480000),
]

for idx, item in enumerate(items, start=row_start + 1):
    ws.cell(row=idx, column=1, value=item[0]).alignment = Alignment(horizontal="center")
    ws.cell(row=idx, column=2, value=item[1])
    ws.cell(row=idx, column=3, value=item[2]).number_format = "#,##0"
    ws.cell(row=idx, column=4, value=item[3]).alignment = Alignment(horizontal="center")
    ws.cell(row=idx, column=5, value=item[4]).number_format = "₹#,##0.00"
    # Dynamic formula: Qty * Rate
    ws.cell(row=idx, column=6, value=f"=C{idx}*E{idx}").number_format = "₹#,##0.00"
    
    fill = ZEBRA_FILL if idx % 2 == 0 else PatternFill(fill_type=None)
    for c in range(1, 7):
        ws.cell(row=idx, column=c).border = thin_border
        if fill.fill_type:
            ws.cell(row=idx, column=c).fill = fill

# 4. Total Row
tot_row = row_start + len(items) + 1
ws.cell(row=tot_row, column=2, value="TOTAL ESTIMATED EXPENDITURE").font = BOLD_FONT
ws.cell(row=tot_row, column=6, value=f"=SUM(F{row_start+1}:F{tot_row-1})").font = BOLD_FONT
ws.cell(row=tot_row, column=6).number_format = "₹#,##0.00"
for c in range(1, 7):
    ws.cell(row=tot_row, column=c).fill = TOTAL_FILL

# 5. Auto-fit column widths
for col in ws.columns:
    max_len = max(len(str(cell.value or '')) for cell in col)
    col_letter = get_column_letter(col[0].column)
    ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

ws.freeze_panes = "A4"
wb.save("Remediation_Cost_Analysis.xlsx")
print("Saved Remediation_Cost_Analysis.xlsx successfully.")
```

## Workflow Execution
1. Calculate line items, quantities, and cost rates.
2. Author the Python workbook generator in the chat workspace.
3. Run `python3 generate_sheets.py`.
4. Inspect created `.xlsx` file and verify formulas work cleanly.
