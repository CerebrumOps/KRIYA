---
name: inspection-report
description: Specialized skill for analyzing scanned plant inspection reports, extracting corrosion & thickness findings, cross-checking MRPL maintenance SOPs, and drafting Word (.docx) approval notes with evidence provenance.
version: 1.0.0
triggers:
  - inspection report
  - scanned pdf
  - corrosion indication
  - ultrasonic thickness
  - approval note
  - sop 4.2.3
tools:
  - query_refinery_telemetry
  - search_refinery_sops
  - generate_docx_approval_note
---

# Inspection Report Analysis & SOP Verification Skill

## Purpose
Enables KRIYA to process refinery inspection logs, scanned reports, and ultrasonic thickness surveys for Mangalore Refinery & Petrochemicals Limited (MRPL).

## Operational Workflow
1. **Extraction & Evidence Traceability**:
   - Extract page numbers, observation tags, and physical measurements (e.g., wall thickness in mm, corrosion rate in mm/year).
   - Record exact provenance: Page #, Region/Nozzle, Inspector Notes, Confidence score.
2. **SOP Cross-Check**:
   - Query MRPL knowledge base using `search_refinery_sops` (e.g., `SOP-MRPL-4.2.3`).
   - Compare measured wall thickness against minimum permissible limit (e.g., 6.5 mm).
   - If thickness < 6.5 mm, immediately flag as **Category-A Defect requiring engineering intervention**.
3. **Approval Note Synthesis**:
   - Draft formal corporate Approval Note.
   - Include: Background, Executive Findings, SOP Compliance Matrix, Risk Evaluation, Recommended Remedial Actions (e.g. amine injection rate adjustment, bypass spool fabrication).
4. **Deliverable Generation**:
   - Invoke `generate_docx_approval_note` to produce `Approval_Note.docx`.
