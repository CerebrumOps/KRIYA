---
name: inspection-report
description: Specialized skill for analyzing plant inspection reports, ultrasonic CML thickness readings, API 510/570 corrosion rates, and generating comprehensive Word (.docx) approval dossiers with formal Signature & Stamp columns.
version: 2.0.0
triggers:
  - inspection report
  - scanned pdf
  - corrosion indication
  - ultrasonic thickness
  - approval note
  - api 510
tools:
  - ocr_extract_text
  - generate_word_document
  - generate_excel_spreadsheet
  - execute_terminal_command
---

# Inspection Report Analysis, API 510 Verification & Approval Dossier Skill

## Purpose
Enables KRIYA to process refinery inspection logs, uploaded photos/PDFs (via `ocr_extract_text`), and enterprise MCP ultrasonic thickness records for Coastal Refinery & Petrochemicals Ltd (CRPL / MRPL), producing comprehensive corporate Approval Notes with full signature columns.

## Operational Workflow
1. **Data & Document Extraction**:
   - If the user attached a photo or PDF, call `ocr_extract_text(file_path)` first.
   - Query live equipment specs (`get_equipment`), CML ultrasonic thickness history (`get_thickness_history`), inspection dossiers (`get_inspection_reports`), and turnaround plans (`get_turnaround_plan`).
2. **API 510 / API 570 True Corrosion & Remaining Life Verification**:
   - Calculate Metal Loss: $\Delta t = t_{\text{prev}} - t_{\text{curr}}$.
   - Calculate True Corrosion Rate: $CR = \Delta t / \Delta \text{Years}$.
   - Calculate True Remaining Life: $RL = (t_{\text{curr}} - t_{\text{min}}) / CR$.
   - Cross-check against contractor summary reports (`get_document_content`) to detect understated corrosion traps.
   - Compare $RL$ against the scheduled turnaround date.
3. **Commercial, Budget & DOA Routing**:
   - Check vendor rate contracts (`get_rate_contracts`), departmental budget (`get_department_budget`), and Delegation of Authority (`get_delegation_of_authority`).
4. **Comprehensive Deliverable Generation**:
   - Call **`generate_word_document`** with:
     - Full Document Control Metadata (`document_id`, `asset_tag`, `department`, `prepared_by`)
     - Detailed Markdown sections and structured `tables` (Equipment Design Specs, CML Thickness & Corrosion Audit, Financial & Budget Breakdown, Risk & SOP Compliance)
     - `include_signature_block=True` so the document ends with the **6-column Authorization, Concurrence & Official Signature Block** (`Authority Tier`, `Officer Name & Designation`, `Department`, `DOA Scope`, **`Signature & Official Stamp`**, `Date`).
   - Always conclude your response with:
     `[Deliverable Created]: <Document Title> saved to '<filename>.docx'`
