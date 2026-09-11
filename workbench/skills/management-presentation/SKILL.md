---
name: management-presentation
description: Specialized skill for synthesizing multi-source refinery findings and cost summaries into an executive PowerPoint (.pptx) presentation deck and supporting Excel (.xlsx) workbook, with automated cross-artifact consistency verification.
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
  - generate_xlsx_cost_workbook
  - generate_pptx_deck
  - verify_artifact_consistency
---

# Management Presentation & Cross-Artifact Synthesis Skill

## Purpose
Synthesizes complex technical data, inspection anomalies, and maintenance expenditure into executive-ready deliverables for MRPL leadership and board presentations.

## Operational Workflow
1. **Source Data Aggregation**:
   - Ingest inspection findings, severity levels, equipment downtime impact, and procurement line items.
2. **Spreadsheet Modeling (`.xlsx`)**:
   - Construct multi-tab workbook with equipment breakdown, labor estimates, contingency buffers, and automated `SUM` formulas.
   - Example: Total estimated overhaul cost = ₹1,045,000.00 across 2 critical units.
3. **Executive Presentation Deck (`.pptx`)**:
   - Slide 1: Executive Briefing & Plant Safety Status
   - Slide 2: Critical Operational Findings (K-201 Vibration, CDU Overhead Thinning)
   - Slide 3: Financial Exposure & Remediation Cost Summary
   - Slide 4: Strategic Action Plan & Timeline
4. **Cross-Artifact Consistency Verification**:
   - Validate numerical equality between the Excel sheet and the PowerPoint slides:
     * Check: `Excel Total (₹1,045,000) == PPT Total (₹1,045,000)` -> `✓ MATCH`
     * Check: `Critical Findings Count (2) == PPT Findings (2)` -> `✓ MATCH`
