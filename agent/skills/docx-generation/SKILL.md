---
name: docx-generation
description: Comprehensive skill for authoring official corporate Word (.docx) technical approval notes, specifications, and engineering dossiers with Document Control Metadata, multi-table findings, and formal Multi-Tier Signature & Stamp columns.
version: 2.0.0
triggers:
  - docx
  - word document
  - technical note
  - approval note
  - specification document
  - engineering dossier
  - written report
tools:
  - generate_word_document
  - execute_terminal_command
---

# Professional Word (.docx) Document Generation Skill

## Purpose
Enables KRIYA to author richly detailed, corporate-grade Microsoft Word (`.docx`) documents for official CRPL / MRPL refinery engineering sign-offs, technical approval notes, and inspection dossiers.

## Primary Execution Method (Fastest & Most Reliable)
Call the built-in **`generate_word_document`** tool directly! It automatically creates:
1. Corporate Page Headers & Confidentiality Footers
2. 4-Column Document Control Metadata Grid (Document Ref, Date/Revision, Asset Tag, Department, Standards, Classification)
3. Rich Markdown Sections (`## Headings`, bullet lists, bold callouts, and Markdown tables)
4. Styled Corporate Navy Tables (`#1E3A8A` headers, `#F8FAFC` zebra striping, cell margins)
5. **Formal Multi-Tier Authorization, Concurrence & Signature Block Table** (`include_signature_block=True`) with explicit columns:
   `Authority Tier / Action` | `Officer Name & Designation` | `Department` | `DOA / Approval Scope` | **`Signature & Official Stamp`** | `Date`

### Required Document Structure for Detailed Engineering Dossiers
When calling `generate_word_document(filename, title, asset_tag, document_id, content, tables, include_signature_block=True, signatories=...)`, always structure `content` and `tables` with these comprehensive sections:
1. **1. Executive Summary & Operational Urgency**: High-level summary of equipment condition, remaining life vs. turnaround window, and expenditure request.
2. **2. Equipment Design & Operating Specifications**: Table of design pressure, temperature, metallurgy, nominal thickness ($t_{nom}$), minimum required thickness ($t_{min}$), and service fluid.
3. **3. Ultrasonic Thickness (CML) & Corrosion Rate Analysis (API 510 / 570)**:
   - Table comparing previous inspection thickness, current thickness, metal loss ($\Delta t$), true corrosion rate ($CR = \Delta t / \text{years}$), and true remaining life ($RL = (t_{curr} - t_{min}) / CR$).
   - Flag any discrepancy if historical contractor reports understated the corrosion rate.
4. **4. Financial Estimate, Rate Contract & Budget Verification**:
   - Itemized cost breakdown or approved vendor rate contract reference (e.g., `RC-2026-EXCH-04`), cost center budget check (e.g., `CC-10-CDU`), and net remaining balance.
5. **5. Risk Assessment, HSE & SOP Compliance Matrix**:
   - Citations to governing standards (`API 510`, `API 570`, `ASME Sec. VIII`) and PTW/MOC requirements.
6. **6. Formal Multi-Tier DOA Authorization & Signature Matrix**:
   - Ensure `include_signature_block=True` and pass `signatories` mapped to the Corporate Delegation of Authority (DOA) tiers:
     - **Prepared & Inspected By (Level 2):** Plant / Inspection Engineer (e.g. `Arun V. Rao, EMP-1008`)
     - **Reviewed & Recommended By (Level 3):** AGM Mechanical Maintenance (e.g. `Rajesh K. Sharma, EMP-1005` — DOA up to ₹5,00,000)
     - **Financial Concurrence (Level 4):** GM Finance & Accounts (e.g. `Sunita Deshpande, EMP-1003`)
     - **Final Approving Authority (Level 4):** General Manager O&M (e.g. `K. V. Ramanathan, EMP-1002` — DOA up to ₹25,00,000) or Director (`Dr. Arvind Swaminathan, EMP-1001`).

## Fallback Custom Python Script Blueprint (If Custom Scripting via `execute_terminal_command`)
If writing a custom script using `python-docx`, always include both the Document Control Metadata table at the top and the 6-column **Authorization & Signature Block** (`Authority Tier`, `Officer Name & Designation`, `Department`, `DOA Scope`, `Signature & Official Stamp`, `Date`) at the bottom, and conclude your response with:
`[Deliverable Created]: <Document Title> saved to '<filename>.docx'`
