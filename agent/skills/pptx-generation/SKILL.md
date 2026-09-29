---
name: pptx-generation
description: Comprehensive skill for authoring modern 16:9 widescreen executive presentation slide decks (.pptx) with python-pptx, KPI callout cards, and formatted tables.
version: 1.0.0
triggers:
  - pptx
  - powerpoint
  - slide deck
  - executive presentation
  - management briefing
  - board review
  - visual presentation
tools:
  - execute_terminal_command
---

# Professional PowerPoint (.pptx) Deck Generation Skill

## Purpose
Enables KRIYA to author executive presentation slide decks (`.pptx`) for MRPL leadership, turnaround committees, and technical directors with 16:9 widescreen formatting, KPI cards, and clear visual hierarchy.

## Environment & Tooling
- **Runtime**: Python 3 with `python-pptx` (pre-installed).
- **Execution**: Write a Python script in the active workspace and execute it using `execute_terminal_command` (e.g. `python3 make_deck.py`).
- **Target Output Directory**: Save directly to `./` (the active chat workspace) or `./documents/`.

## Deck Design Standards

### 1. Slide Geometry & Typography
- **Dimensions**: 16:9 Widescreen (`13.333` inches wide × `7.5` inches high).
  ```python
  prs.slide_width = Inches(13.333)
  prs.slide_height = Inches(7.5)
  ```
- **Palette**:
  - Dark Primary (Title Slide & Header Bars): Dark Navy (`#0F172A` or `#1E3A8A`)
  - Accent / Highlights: Amber / Orange (`#F59E0B`), Cyan (`#06B6D4`), Emerald (`#10B981`)
  - Background (Content Slides): Off-White / Pure White (`#FFFFFF` / `#F8FAFC`)
  - Text: Dark Charcoal (`#1E293B`)
- **Structure**:
  1. Title Slide: Dark theme, high contrast, project title, asset ID, date, author.
  2. Context & Executive Summary: 3 KPI stat cards across the top + summary bullet points.
  3. Technical Inspection Findings: Side-by-side comparison or high-density NDT data table.
  4. Remediation Strategy & Financial Impact: Schedule milestones and budget allocation.
  5. Action Items & Governance: Decision request and approval committee next steps.

### 2. Implementation Python Script Blueprint

```python
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
blank_layout = prs.slide_layouts[6]

# Slide 1: Dark Title Slide
slide1 = prs.slides.add_slide(blank_layout)

# Dark Background
bg = slide1.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg.fill.solid()
bg.fill.fore_color.rgb = RGBColor(15, 23, 42)  # #0F172A
bg.line.fill.background()

# Title text box
tb = slide1.shapes.add_textbox(Inches(1.5), Inches(2.2), Inches(10.3), Inches(3.0))
tf = tb.text_frame
tf.word_wrap = True

p1 = tf.paragraphs[0]
p1.text = "CDU-II OVERHEAD LINE INTEGRITY"
p1.font.size = Pt(40)
p1.font.bold = True
p1.font.color.rgb = RGBColor(255, 255, 255)

p2 = tf.add_paragraph()
p2.text = "Critical Ultrasonic Thickness Survey & Rapid Remediation Plan"
p2.font.size = Pt(20)
p2.font.color.rgb = RGBColor(56, 189, 248)  # Light cyan

p3 = tf.add_paragraph()
p3.text = "\nMRPL Mangalore Complex | Ref: 01-C-101 | September 2026"
p3.font.size = Pt(13)
p3.font.color.rgb = RGBColor(148, 163, 184)

# Slide 2: Content Slide with KPI Cards
slide2 = prs.slides.add_slide(blank_layout)

# Slide Header
header_box = slide2.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.8))
hp = header_box.text_frame.paragraphs[0]
hp.text = "Executive Summary & Asset Risk Status"
hp.font.size = Pt(24)
hp.font.bold = True
hp.font.color.rgb = RGBColor(30, 58, 138)

# 3 KPI Stat Cards
kpis = [
    ("4.8 mm", "Measured Wall Thickness", RGBColor(239, 68, 68)),   # Red alert
    ("6.5 mm", "Minimum Permissible Limit", RGBColor(100, 116, 139)), # Neutral
    ("₹8.25 L", "Estimated Remediation Cost", RGBColor(16, 185, 129)) # Emerald
]

for idx, (stat, label, color) in enumerate(kpis):
    x = Inches(0.8 + idx * 3.9)
    card = slide2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, x, Inches(1.5), Inches(3.6), Inches(1.8))
    card.fill.solid()
    card.fill.fore_color.rgb = RGBColor(248, 250, 252)
    card.line.color.rgb = color
    card.line.width = Pt(1.5)
    
    ctf = card.text_frame
    ctf.word_wrap = True
    sp = ctf.paragraphs[0]
    sp.text = stat
    sp.font.size = Pt(32)
    sp.font.bold = True
    sp.font.color.rgb = color
    sp.alignment = PP_ALIGN.CENTER
    
    lp = ctf.add_paragraph()
    lp.text = label
    lp.font.size = Pt(11)
    lp.font.color.rgb = RGBColor(71, 85, 105)
    lp.alignment = PP_ALIGN.CENTER

prs.save("Executive_Presentation.pptx")
print("Saved Executive_Presentation.pptx successfully.")
```

## Workflow Execution
1. Structure the storyline: Title -> Findings -> Data -> Plan -> Approvals.
2. Author the Python presentation script in the active chat workspace.
3. Run `python3 generate_deck.py`.
4. Verify slide count and layout consistency.
