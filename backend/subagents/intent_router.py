# ==============================================================================
# KRIYA Intent Parsing & Action Router Subagent
# ==============================================================================
# Analyzes incoming user requests to determine:
# 1. Task Classification (INQUIRY, MULTI_STEP_INDUSTRIAL, CODING_SANDBOX, DRAWING_INSPECTION, MANAGEMENT_DECK)
# 2. Optimal Local Model Profile (Reasoning vs Coding vs Vision)
# 3. Dynamic Workbench Skill to activate
# 4. Whether Multi-Step Planning & Human-in-the-Loop approval is required
# ==============================================================================

import re
from typing import Any, Dict, List, Optional


def classify_intent(user_prompt: str, history: Optional[List[Any]] = None) -> Dict[str, Any]:
    """
    Classifies user intent and routes execution to the appropriate subagent,
    skill, and local model profile.
    """
    prompt_lower = user_prompt.lower()

    # 1. Management Presentation / Board Review (Demo 4)
    if any(k in prompt_lower for k in ["management presentation", "powerpoint", "pptx", "board review", "cost summary", "excel workbook", "presentation template"]):
        return {
            "task_type": "MANAGEMENT_DECK",
            "task_title": "Executive Management Presentation & Cost Synthesis",
            "recommended_skill": "management-presentation",
            "model_profile": "reasoning",
            "requires_planning": True,
            "requires_human_approval": True,
            "description": "Synthesizes multi-source inspection data, builds Excel cost workbook, generates PowerPoint slides, and validates cross-artifact consistency."
        }

    # 2. Scanned Inspection Report & Approval Note (Demo 1)
    if any(k in prompt_lower for k in ["inspection report", "approval note", "scanned", "compressor unit", "corrosion", "ultrasonic", "sop 4.2.3", "word format"]):
        return {
            "task_type": "MULTI_STEP_INDUSTRIAL",
            "task_title": "Inspection Report Analysis → Evidence Matrix → Word Approval Note",
            "recommended_skill": "inspection-report",
            "model_profile": "reasoning",
            "requires_planning": True,
            "requires_human_approval": True,
            "description": "Extracts scanned report findings, links evidence to source pages, verifies MRPL maintenance SOPs, and drafts an official .docx approval note."
        }

    # 3. Coding Demo & Sandbox Self-Repair (Demo 2)
    if any(k in prompt_lower for k in ["python utility", "sandbox", "test cases", "self-repair", "fix any errors", "verified working code", "write a python"]):
        return {
            "task_type": "CODING_SANDBOX",
            "task_title": "Autonomous Tool Development & Sandbox Self-Repair",
            "recommended_skill": "code-sandbox",
            "model_profile": "coding",
            "requires_planning": True,
            "requires_human_approval": True,
            "description": "Develops Python tool in isolated sandbox, generates unit tests, captures tracebacks, and executes self-repair iterations until all tests pass."
        }

    # 4. P&ID Schematics & Visual Drawing Inspection (Demo 3)
    if any(k in prompt_lower for k in ["p&id", "pid", "drawing", "schematic", "process flow", "labeled process", "instrument tag"]):
        return {
            "task_type": "DRAWING_INSPECTION",
            "task_title": "P&ID Drawing Inspection & Controlled Uncertainty Analysis",
            "recommended_skill": "pid-inspection",
            "model_profile": "vision",
            "requires_planning": True,
            "requires_human_approval": True,
            "description": "Multimodal analysis of engineering schematics, mapping equipment flow, and flagging ambiguous labels for human verification without hallucinations."
        }

    # 5. Simple Tool or Conversational Inquiry
    return {
        "task_type": "INQUIRY",
        "task_title": "Direct Engineering Inquiry",
        "recommended_skill": None,
        "model_profile": "reasoning",
        "requires_planning": False,
        "requires_human_approval": False,
        "description": "Direct conversational analysis or single-step tool execution."
    }
