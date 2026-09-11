1. HERO DEMO — Scanned inspection report → engineering findings → approval note
Prompt shown to judge

“Analyze the attached scanned inspection report for the compressor unit. Extract the key findings, identify observations that require attention, cross-check them against the relevant maintenance SOPs in the internal knowledge base, and prepare a draft approval note in Word format. Include the evidence from the report, applicable SOP references, recommended action, and clearly mark anything that requires human review.”

What the judge sees in front

The UI should immediately become an active workbench, not just chat.

Show:

TASK: Inspection Report → Approval Note
STATUS: Executing

MODEL
Vision → [selected local VLM]
Reasoning → [selected local reasoning model]

SKILL
Inspection Report Analysis

WORKSPACE
/input/inspection_report.pdf
/working/
/output/
/evidence/

LIVE ACTIVITY
✓ Opened scanned PDF
✓ Detected 14 pages
✓ OCR processing...
✓ Visual analysis: pages 3, 6, 9
✓ Searching maintenance SOPs...
⟳ Comparing findings with SOP...

Then show the actual report being understood.

For example:

PAGE 6
┌──────────────────────────┐
│ scanned inspection page  │
│ handwritten annotation   │
│ engineering diagram      │
└──────────────────────────┘

Extracted:
• Valve leakage observed
• Corrosion indication
• Inspector note: "monitor closely"

Then:

EVIDENCE
Finding #1
Source: Inspection Report, Page 6

SOP Match
Maintenance SOP 4.2.3
Relevant requirement: ...

Confidence: 0.91

Finally:

OUTPUT
✓ Approval_Note.docx

[Open artifact]
What happens internally
Task
 ↓
Task classification
 ↓
Load inspection-report skill
 ↓
Select VLM
 ↓
PDF page extraction
 ↓
OCR
 ↓
Vision reasoning
 ↓
structured findings
 ↓
Knowledge-base search
 ↓
SOP retrieval
 ↓
Reasoning model compares evidence
 ↓
Generate approval note
 ↓
DOCX creation
 ↓
Document verification
 ↓
Human-review flags
 ↓
Artifact
Surprise capability

Evidence traceability.

Don't merely say:

“The model found corrosion.”

Make the system show:

Finding
   ↓
source page
   ↓
source region
   ↓
extracted observation
   ↓
SOP reference
   ↓
generated recommendation

That is extremely relevant to industrial users even though the PS doesn't explicitly demand an evidence/provenance system.

It makes the system look considerably more serious.

2. CODING DEMO — Internal tool development with autonomous verification
Prompt

“Create a Python utility that reads the inspection findings generated in this workspace, generates a CSV summary of critical findings, and produces a simple severity report. Run the program in the local sandbox, create test cases, fix any errors you encounter, and provide the verified working code.”

This is particularly useful because the PS explicitly says:

coding task run and verified in a sandbox.

What the judge sees

The UI shows a different model being selected:

TASK TYPE
Coding

MODEL ROUTING
Reasoning model
      ↓
Coding model selected

WORKSPACE
inspection_task/

AGENT ACTIVITY
✓ Inspected previous findings
✓ Generated Python utility
✓ Created test cases
⟳ Running sandbox...
✕ Test failed
⟳ Analyzing failure
⟳ Updating implementation
✓ Tests passed
✓ Output validated

Then show a real terminal panel:

$ python test_report.py

5 tests collected
5 passed

$ python generate_report.py
Output:
critical_findings.csv
severity_summary.csv
Internal flow
Main Agent
 ↓
inspect workspace
 ↓
read previous artifact
 ↓
coding model
 ↓
write code
 ↓
sandbox execution
 ↓
test
 ↓
observe failure
 ↓
modify code
 ↓
execute again
 ↓
verify
 ↓
artifact
Surprise capability

Self-repair loop.

Don't deliberately fake a failure.

Give it a deliberately incomplete or slightly tricky requirement so the model naturally encounters a problem.

Then let judges watch:

FAILED
   ↓
observe
   ↓
reason
   ↓
modify
   ↓
rerun
   ↓
PASS

That visually proves:

This isn't a chatbot generating code. It's actually operating an environment.

That is precisely the conceptual difference between KRIYA and a generic LLM UI.

3. ENGINEERING DRAWING DEMO — Image + vision + domain reasoning

This should be your multimodal “wow” demo.

Prompt

“Inspect the attached P&ID image. Identify the major equipment, valves and labeled process components visible in the drawing, summarize the apparent process flow, and flag any visually identifiable items that should be reviewed by an engineer. Do not infer information that is not visible in the drawing.”

What the judge sees

Show the original drawing on the left:

┌───────────────────────┐
│                       │
│       P & ID          │
│                       │
│  pumps   valves       │
│  pipes   instruments  │
│                       │
└───────────────────────┘

On the right:

VISION ANALYSIS

Detected components
────────────────────
✓ Pump P-101
✓ Valve XV-102
✓ Instrument PT-104
✓ Vessel V-201

Process flow
────────────────────
P-101 → V-201 → XV-102

REVIEW FLAGS
────────────────────
⚠ Label partially unreadable
⚠ Drawing region requires human verification

And ideally highlight image regions corresponding to the extracted elements.

Internally
Image
 ↓
Vision model
 ↓
visual observations
 ↓
structured representation
 ↓
reasoning model
 ↓
engineering summary
Surprise capability

“Don't know” / uncertainty handling.

This is actually a very strong industrial feature.

Instead of allowing the model to hallucinate:

Component: XV-102
Confidence: 0.96

versus:

Component label: partially legible
Confidence: 0.41
Action: requires human verification

You are demonstrating controlled AI, rather than merely intelligent AI.

That maps beautifully to sensitive industrial environments.

4. BOARD / MANAGEMENT WORK — Internal documents → spreadsheet → PPT

This demonstrates that your workbench isn't just an engineering chatbot.

Prompt

“Using the inspection findings and cost summary available in this workspace, prepare a management-ready presentation covering the issue, impact, recommended action, estimated cost, and next steps. Use the existing organization presentation template and include the supporting data in an Excel workbook.”

Now you demonstrate:

Existing workspace
       ↓
documents
       ↓
spreadsheet
       ↓
reasoning
       ↓
PowerPoint
       ↓
Excel
What the judge sees

A task panel:

TASK
Management Presentation

INPUTS
✓ Inspection findings
✓ Cost summary
✓ Existing PPT template

MODEL
Reasoning → Model A

TOOLS DISCOVERED
presentation.*
spreadsheet.*
document.*

Then:

LIVE EXECUTION

✓ Read findings
✓ Read cost data
✓ Loaded presentation template
✓ Calculated summary values
✓ Generated Excel workbook
✓ Generated presentation
✓ Cross-checked numbers
✓ Verified presentation structure

OUTPUT
📊 Inspection_Cost_Analysis.xlsx
📑 Management_Review.pptx

Then actually open the generated presentation.

Surprise capability

Cross-artifact consistency checking.

This is excellent.

Have KRIYA verify:

Excel total = ₹X
        ↕
PPT total = ₹X
        ✓ MATCH

and:

Number of critical findings
Excel: 7
PPT: 7
        ✓ MATCH

That is a capability not explicitly demanded by the PS, but it is extremely useful in real knowledge work.

It also demonstrates that your agent understands that its outputs form one coherent work product.