---
name: pid-inspection
description: Specialized multimodal skill for inspecting Piping & Instrumentation Diagrams (P&IDs), detecting labeled valves, pumps, instruments, and process flow lines, and flagging low-confidence or ambiguous drawing regions for mandatory human engineer review.
version: 1.0.0
triggers:
  - p&id
  - piping and instrumentation diagram
  - schematic
  - drawing inspection
  - process flow
  - instrument tag
tools:
  - inspect_engineering_drawing
  - query_refinery_telemetry
---

# P&ID Engineering Drawing & Uncertainty Handling Skill

## Purpose
Enables KRIYA to process technical schematics and P&IDs without hallucinations, providing strict uncertainty management for safety-critical plant operations.

## Operational Workflow
1. **Component Extraction**:
   - Identify Pumps (e.g. `P-101A/B`), Columns (e.g. `C-101`), Compressors (`K-201`), Transmitters (`PT-104`, `TT-105`), and Control/ESD Valves (`XV-102`).
   - Extract line numbers, pipe diameters, and flow direction arrows.
2. **Process Flow Topology**:
   - Trace sequence of equipment connections: e.g. `P-101 -> E-101 -> C-101 Overhead -> Condenser`.
3. **Controlled Uncertainty & Review Flags**:
   - High Confidence (>= 0.90): Catalog item and cross-verify with SCADA equipment inventory.
   - Low Confidence or Blurred Text (< 0.60): **Do NOT guess or infer**. Flag explicitly:
     * `[REVIEW REQUIRED]`: Label partially legible on bypass line upstream of XV-102. Action: Requires site engineer verification.
