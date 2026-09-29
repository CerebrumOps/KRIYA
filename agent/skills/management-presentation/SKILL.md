---
name: management-presentation
description: Specialized skill for synthesizing multi-source refinery findings and cost summaries into an executive PowerPoint (.pptx) presentation deck and supporting Excel (.xlsx) workbook, with cross-artifact numerical consistency.
version: 1.0.0
triggers:
  - management presentation
  - powerpoint
  - pptx
  - excel workbook
  - xlsx
  - board review
  - cost analysis
tools:
  - execute_terminal_command
  - load_skill
---

# Management Presentation & Cross-Artifact Synthesis Skill

## Purpose
Synthesizes complex technical data, inspection anomalies, and maintenance expenditure into executive-ready deliverables for MRPL leadership and board presentations.

## Operational Workflow
1. **Source Data Aggregation**:
   - Ingest inspection findings, severity levels, equipment downtime impact, and procurement line items.
2. **Spreadsheet Modeling (`.xlsx`)**:
   - Load `xlsx-generation` skill via `load_skill("xlsx-generation")`.
   - Write and run Python script with `openpyxl` to build itemized cost spreadsheet with formulas.
3. **Executive Presentation Deck (`.pptx`)**:
   - Load `pptx-generation` skill via `load_skill("pptx-generation")`.
   - Write and run Python script with `python-pptx` to build 16:9 widescreen presentation deck.
4. **Cross-Artifact Consistency Verification**:
   - Validate numerical equality between the Excel sheet and the PowerPoint slides by inspecting both artifacts with Python:
     * Check: `Excel Total == PPT Total`
     * Check: `Critical Findings Count == PPT Findings Count`
