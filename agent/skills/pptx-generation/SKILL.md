---
name: pptx-generation
description: Comprehensive skill for authoring modern 16:9 widescreen executive presentation slide decks (.pptx) with KPI callout cards, technical analysis slides, and a Governance & DOA Signature Matrix slide.
version: 2.0.0
triggers:
  - pptx
  - powerpoint
  - slide deck
  - executive presentation
  - management briefing
  - board review
  - visual presentation
tools:
  - generate_powerpoint_deck
  - execute_terminal_command
---

# Professional PowerPoint (.pptx) Deck Generation Skill

## Purpose
Enables KRIYA to author executive 16:9 widescreen presentation slide decks (`.pptx`) for CRPL / MRPL leadership, turnaround committees, and technical directors.

## Primary Execution Method (Fastest & Most Reliable)
Call the built-in **`generate_powerpoint_deck`** tool directly!
It automatically generates:
1. **Slide 1 — Dark Navy Executive Cover Slide (`#0F172A`)**: Cyan accent bar, uppercase title, subtitle, presenter name/designation, and timestamp.
2. **Content Slides (`slides` array)**:
   - Full-width Deep Navy Header Bar (`#1E3A8A`) with slide title
   - Up to 4 **KPI Callout Cards** (`kpis: [{"value": "0.35 mm/yr", "label": "True Corrosion Rate"}]`)
   - Detailed technical bullet points (`bullets: [...]`)
3. **Final Slide — Governance, DOA Authorization & Sign-Off Matrix (`include_signoff_slide=True`)**:
   - Formatted 5-column table (`Authority Tier`, `Officer Name & Designation`, `Department`, `DOA / Approval Scope`, **`Signature & Stamp`**) for executive committee sign-off.

## Recommended 5-Slide Executive Storyline
1. **Slide 1 (Cover)**: Automatically created from `title`, `subtitle`, and `presenter`.
2. **Slide 2 (`Executive Summary & Critical KPIs`)**: Include 3–4 KPI cards (e.g., Current Thickness, True Corrosion Rate, Remaining Life, Repair Cost) + summary bullets.
3. **Slide 3 (`API 510 Ultrasonic Thickness & Corrosion Audit`)**: Detailed comparison of historical CML readings, true metal loss calculation, and turnaround cutoff gap.
4. **Slide 4 (`Commercial Procurement, Budget & Vendor Selection`)**: Rate contract / RFQ comparison, Cost Center `CC-10-CDU` budget availability, and execution timeline.
5. **Slide 5 (`Governance & Sign-Off Matrix`)**: Automatically appended when `include_signoff_slide=True`.

Always conclude your final response with:
`[Deliverable Created]: <Presentation Title> saved to '<filename>.pptx'`
