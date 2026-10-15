---
name: xlsx-generation
description: Comprehensive skill for authoring multi-tab, professional financial and engineering Excel (.xlsx) workbooks with corporate navy styling, currency formatting, auto-sizing, and formal Verification & Signature columns.
version: 2.0.0
triggers:
  - xlsx
  - excel workbook
  - cost spreadsheet
  - budget analysis
  - capex opex
  - turnaround cost
  - financial model
tools:
  - generate_excel_spreadsheet
  - execute_terminal_command
---

# Professional Excel (.xlsx) Workbook Generation Skill

## Purpose
Enables KRIYA to author structured, multi-tab Microsoft Excel (`.xlsx`) workbooks for turnaround estimation, ultrasonic thickness tracking, equipment repair cost analysis, vendor bid comparison, and asset integrity budgets.

## Primary Execution Method (Fastest & Most Reliable)
Call the built-in **`generate_excel_spreadsheet`** tool directly!
It automatically creates:
1. Corporate Title Banner & Metadata Subtitle row (`CRPL | Ref ID | Timestamp | Sovereign Air-Gapped`)
2. Deep Steel Navy (`#1E3A8A`) Table Headers with White Bold text
3. Alternating Zebra-Striped Data Rows (`#F8FAFC` / `#FFFFFF`) with thin borders and INR (`₹#,##0.00`) or decimal formatting
4. Multi-tab support via the `sheets` array parameter (`[{"name": "Tab1", "title": "...", "headers": [...], "rows": [[...]]}]`)
5. **Formal Verification, DOA & Signature Block** (`include_signature_block=True`) at the bottom of the summary sheet with explicit columns:
   `Authority Role` | `Officer Name & Designation` | `Department` | `Approval Scope / DOA` | **`Signature & Stamp`** | `Date`

## Recommended Multi-Tab Workbook Structure
When generating detailed engineering/financial workbooks, pass multiple tabs in `sheets`:
- **Tab 1 (`Executive Summary & Budget`)**: Cost Center allocation (`CC-10-CDU`), Allocated Budget, Committed Spend, Current Repair Estimate, Net Available Balance, and DOA Sign-Off Block.
- **Tab 2 (`CML Thickness & Corrosion`)**: Equipment Tag, CML ID, Nominal Thickness ($t_{nom}$), Previous Reading, Current Reading, Min Required ($t_{min}$), Metal Loss ($\Delta t$), Corrosion Rate ($\text{mm/yr}$), Remaining Life ($\text{Years}$), and Next Turnaround Status.
- **Tab 3 (`Vendor Rate & Bid Comparison`)**: Contract/RFQ Ref, Vendor Name, Scope of Work, Quoted Price (INR), Delivery Lead Time, Technical Qualification, and Selection Status.

Always conclude your final response with:
`[Deliverable Created]: <Workbook Title> saved to '<filename>.xlsx'`
