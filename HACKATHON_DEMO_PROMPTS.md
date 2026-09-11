# KRIYA - High-Impact Hackathon Demonstration Prompts
### Sovereign Industrial AI Workbench for MRPL (Mangalore Refinery and Petrochemicals Limited)

These demonstration prompts are specifically designed for the **Smart India Hackathon (SIH) / MRPL Industry Jury**. Each prompt triggers multi-step autonomous planning, industrial database queries, mathematical execution in the Python sandbox, deliverable artifact generation (`.docx`, `.xlsx`, `.pptx`), and cross-artifact consistency verification.

---

## 🎯 Demonstration Highlights to Show the Jury:
1. **Interactive Planning Agent**: When you enter a prompt and toggle **Plan**, the dedicated Planner Agent wakes up, analyzes the plant state, generates a structured plan and checklist, and pops up the **Task Queue Modal** for human-in-the-loop approval.
2. **Tool Execution Side Panel**: During tool execution (database queries, Python sandbox runs, deliverable creation), the side drawer slides open with real-time arguments and telemetry, waits 1 second on completion, and slides back smoothly.
3. **Workspace Isolation & Real Deliverables**: All documents are generated on disk in the isolated user and chat workspace (`workspace/users/{employee_id}/{chat_id}/`). Click the **Deliverables** button in the header to view and directly download the real `.docx`, `.xlsx`, and `.pptx` files.
4. **Mathematical Provenance & Zero Hallucination**: The cross-artifact verifier validates that numbers in slides match the underlying spreadsheet cells down to the exact rupee and decimal place.

---

## Prompt 1: Refinery Unit Corrosion & Metallurgical Root Cause Analysis with Formal Word Approval Note (.docx)
> **Demonstrates**: Database queries + Maintenance SOP matching + ASME B31.3 calculation loop + Word document generation + Isolated chat workspace.

### Copy-Paste Prompt:
```text
Perform a comprehensive asset integrity assessment for the CDU-II Atmospheric Column C-101 overhead vapor line. 

Please perform the following steps:
1. Query the asset database and maintenance records for recent ultrasonic thickness (UT) inspection readings and amine dosing history.
2. Cross-reference the observed corrosion rate against MRPL Standard Operating Procedure SOP-MRPL-4.2.3.
3. Use a Python script in our execution sandbox to calculate the remaining service life according to ASME B31.3 minimum required wall thickness formulas.
4. Generate an official executive Microsoft Word Approval Note (.docx) complete with the evidence provenance matrix and engineering recommendations.
```

### Jury Talking Points:
- Explain that KRIYA operates **100% on-premise** with confidential refinery telemetry.
- Point out the Planner Agent breaking the engineering task into distinct phases.
- Open the **Deliverables Drawer** and download `CDU2_Corrosion_Approval_Note.docx` to show the jury the official formatted document with sign-off blocks.

---

## Prompt 2: FCCU Wet Gas Compressor Vibration Tripping & Multi-Tab Financial Cost Workbook (.xlsx)
> **Demonstrates**: Telemetry frequency analysis + ISO 10816/API 617 standards + Dynamic financial modeling + Multi-tab Excel generation with active formulas.

### Copy-Paste Prompt:
```text
Analyze the emergency radial vibration anomaly on FCCU Wet Gas Compressor K-201. 

Please execute this turnaround investigation:
1. Inspect the vibration sensor telemetry in our database and check the 1X/2X harmonics against API 617 and ISO 10816-3 severity thresholds.
2. Identify the root cause between dynamic unbalance, shaft misalignment, and journal bearing clearance degradation.
3. Formulate a comprehensive equipment remediation budget including dry gas seal replacements, rotor balancing, dynamic testing, and specialized contractor labor.
4. Generate a multi-tab Microsoft Excel Cost Workbook (.xlsx) with dynamic formulas calculating total capital requirements.
```

### Jury Talking Points:
- Watch the side drawer show tool calls interacting with the plant database.
- Download `Inspection_Cost_Analysis.xlsx` from the Deliverables panel. Open it to show the jury real Excel formulas (`=SUM(...)`, `=E4+F4`) with zero hardcoded values.

---

## Prompt 3: Executive Turnaround Review & Multi-Artifact Consistency Verification (PowerPoint + Excel Audit)
> **Demonstrates**: Multi-artifact generation + PowerPoint deck creation + Mathematical cross-artifact validation tool (`verify_artifact_consistency`).

### Copy-Paste Prompt:
```text
Prepare an executive turnaround review package for the MRPL Refinery Operations Committee covering CDU-II and FCCU units.

1. Query all critical and high-severity equipment anomalies across the refinery database.
2. Generate an executive 3-slide widescreen PowerPoint Presentation (.pptx) summarizing unit health, mechanical degradation modes, and capital expenditure.
3. Generate the companion detailed Excel Cost Workbook (.xlsx) backing each line item.
4. Execute the cross-artifact consistency verifier tool to mathematically prove that the financial numbers in the PowerPoint deck match the Excel workbook with 100% precision and zero hallucination.
```

### Jury Talking Points:
- Emphasize the **Cross-Artifact Consistency Engine**: in industrial refinery operations, an AI that hallucinates numbers between a slide deck and a budget workbook can cause fatal capital misallocations.
- Show how KRIYA uses deterministic Python AST checks and openpyxl inspection to guarantee cross-document fidelity before presenting to management.

---

## Prompt 4: Diesel Hydrotreater (DHT) Reactor Bed Pressure Drop Runaway & Iterative Sandbox Self-Repair
> **Demonstrates**: Scientific simulation (Ergun equation) + Python sandbox execution + Autonomous error recovery and iterative code refinement.

### Copy-Paste Prompt:
```text
Investigate the catalyst bed pressure drop runaway on DHT Reactor R-301, where bed differential pressure is increasing at 0.38 bar per week toward the hydraulic pinning threshold of 3.2 bar.

1. Write and execute a Python simulation in our sandbox to model the Ergun equation for two-phase trickle-bed flow under operating temperature (365°C) and pressure (65 bar).
2. Calculate the exact projected operating days remaining before feed rate curtailment must be initiated.
3. If the initial code encounters numerical convergence issues or syntax adjustments, automatically inspect the traceback, self-repair the script, and re-run until convergence is reached.
4. Output a summary table with weekly ΔP projections and recommended skimming schedule.
```

### Jury Talking Points:
- Highlight the **Docker / Subprocess Air-Gapped Sandbox**: KRIYA writes real Python code, executes it safely with no internet connectivity, and reads back the standard output.
- Highlight resilience: the model monitors exit codes and self-corrects if calculations need parameter adjustments.

---

## Prompt 5: Pressure Safety Valve PSV-304 Relief Sizing Audit & Flare Capacity Check
> **Demonstrates**: Safety compliance + API 520 / API 521 sizing + Process safety engineering calculations + Workspace documentation.

### Copy-Paste Prompt:
```text
Conduct a safety relief sizing audit for Pressure Safety Valve PSV-304 installed on HP Separator Drum V-202 following recent changes in the flare header backpressure.

1. Query our process design database for the maximum credible relief scenarios: external pool fire vs control valve failure blocked outlet.
2. Using API 520 Part I relief area equations, calculate the required effective discharge area (A in mm²) for supercritical vapor relief.
3. Determine the required standard API letter designation (e.g. 1.5J2, 2K3) and verify if the existing 2.0" orifice provides adequate discharge margin.
4. Save the full calculation script into our workspace as `psv_304_sizing_audit.py` and state the safety sign-off verdict.
```

### Jury Talking Points:
- Shows safety-critical engineering domain depth suitable for PSUs (Public Sector Undertakings) like ONGC / MRPL.
- Demonstrates how the generated Python audit script is stored directly in the active chat workspace.

---

## Prompt 6: Turnaround (TAR-2026) Critical Path Schedule & Multi-Unit Milestone Sequencing
> **Demonstrates**: Turnaround operations + Critical Path Method (CPM) algorithm + Planner task checklist + Official shutdown approval note.

### Copy-Paste Prompt:
```text
Develop a 14-day Critical Path Method (CPM) overhaul schedule for the upcoming CDU-II mini-turnaround (TAR-2026-Q4).

1. Retrieve all open work orders for column C-101 internal tray inspection, heat exchanger E-104 bundle extraction, and furnace F-101 steam-air decoking.
2. Run a Python script in our sandbox to compute the early start, early finish, total float, and critical path activities across the 45 interdependent work orders.
3. Break down the sequence using the planning agent checklist into Pre-Shutdown, Steaming/De-inventory, Mechanical Overhaul, and Catalyst Passivation phases.
4. Generate the official turnaround scope note (.docx) and summarize the critical path bottlenecks that could risk turnaround overruns.
```

### Jury Talking Points:
- Demonstrates enterprise-scale project management integrated with refinery asset databases.
- Shows how human managers can review the plan in the **Task Queue Modal**, approve or reject steps, and monitor execution phase by phase.

---

## 💡 Quick Tips for the Demonstration:
1. **Login First**: Log in with `ADMIN-1001` or `EMP-1001` (Password: `Mrpl@2026#Secure`). Both support 2FA (dev OTP is displayed on screen).
2. **Switch Accounts**: Demonstrate isolation by logging out and logging in as another user—conversations and deliverables are strictly isolated per employee.
3. **Toggle the "Plan" Button**: Show the jury how the Planner Agent formulates checklists before executing heavy engineering tasks.
4. **Inspect Deliverables**: Click **Deliverables** in the top navigation bar to showcase the live files generated in the background.
