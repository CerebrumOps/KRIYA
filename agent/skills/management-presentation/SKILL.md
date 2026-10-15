---
name: management-presentation
description: Specialized skill for synthesizing multi-source refinery findings, vendor bids, and cost summaries into an executive PowerPoint (.pptx) deck and supporting Excel (.xlsx) workbook with formal DOA Signature columns.
version: 2.0.0
triggers:
  - management presentation
  - powerpoint
  - pptx
  - excel workbook
  - xlsx
  - board review
  - cost analysis
tools:
  - generate_powerpoint_deck
  - generate_excel_spreadsheet
  - generate_word_document
  - execute_terminal_command
---

# Management Presentation & Cross-Artifact Synthesis Skill

## Purpose
Synthesizes technical inspection anomalies, API 510 remaining-life calculations, vendor bids, and maintenance expenditure into executive-ready deliverables for CRPL / MRPL leadership and board committees.

## Operational Workflow
1. **Source Data Aggregation**:
   - Retrieve equipment specs, CML thickness readings, turnaround schedules, vendor rate contracts/bids, department budgets, and DOA thresholds via the FastMCP tools.
2. **Detailed Spreadsheet Workbook (`.xlsx`)**:
   - Call **`generate_excel_spreadsheet`** with multiple `sheets` (`Executive Budget Summary`, `CML Corrosion Data`, `Vendor Bid Comparison`) and `include_signature_block=True` so the summary sheet includes the full **Verification, Concurrence & Signature Block**.
3. **Executive Presentation Deck (`.pptx`)**:
   - Call **`generate_powerpoint_deck`** with structured `slides` (KPI Callout Cards + Technical/Financial Bullet Slides) and `include_signoff_slide=True` so the deck concludes with the **Governance & DOA Signature Matrix** slide.
4. **Cross-Artifact Consistency & Registration**:
   - Ensure identical numerical figures across all generated files (e.g., `0.35 mm/yr` corrosion rate, `2.00 Years` remaining life, `₹12,50,000` Apex PetroTech cost, `₹18,50,000` `CC-10-CDU` budget).
   - Output a `[Deliverable Created]: <Title> saved to '<filename>'` line for every generated artifact so each file renders an in-chat download card.
