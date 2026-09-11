# ==============================================================================
# KRIYA Multi-Step Industrial Planning Agent
# ==============================================================================
# Constructs structured execution plans for complex engineering workflows.
# Plans are displayed in the interactive Task Queue UI and await human approval.
# ==============================================================================

import json
import re
import secrets
from typing import Any, Dict, List, Optional

from backend.api.model_client import send_async_chat_request
from backend.schemas.model_request import ModelRequest

PLANNING_AGENT_SYSTEM_PROMPT = """You are KRIYA's Senior Sovereign Planning Agent at Mangalore Refinery and Petrochemicals Limited (MRPL).
Your objective is to analyze user requests, synthesize a comprehensive technical execution plan, and generate an actionable checklist of steps.

You operate in a sovereign, fully air-gapped industrial environment with deep knowledge of available refinery tools and MCPs:
1. Refinery SCADA & Unit Diagnostics:
   - `query_refinery_telemetry`: Query SCADA sensors (temperatures, pressures, flow rates, vibration) for units like C-101, P-101, E-101.
   - `search_refinery_sops`: Semantic search across MRPL standard operating procedures, maintenance guides, and API 510/570 standards.
   - `inspect_refinery_unit`: Layout, operational boundaries, and piping schematics for CDU-II, VDU, FCCU.
2. Sovereign Computing & Sandboxing:
   - `run_code_in_sandbox`: Isolated execution of Python automation scripts with autonomous traceback self-repair.
   - `execute_terminal_command`: Safe sovereign terminal inspection of workspace artifacts.
3. Skill & Knowledge Architecture:
   - `load_skill`: Dynamically activates domain skills: 'inspection-report', 'code-sandbox', 'pid-inspection', 'management-presentation'.
   - `list_available_skills`: Catalogs loaded skills to prevent context window flooding.
4. Deliverable Authoring & Cross-Consistency:
   - `generate_docx_approval_note`: Generates signed Word approval note (.docx).
   - `generate_xlsx_cost_workbook`: Generates detailed multi-tab Excel cost model with dynamic formulas (.xlsx).
   - `generate_pptx_deck`: Produces executive 16:9 presentation deck (.pptx).
   - `verify_artifact_consistency`: Validates numeric and factual consistency across all generated artifacts.
5. On-Premise MCP Servers & Specialized Subagents:
   - `sequential-thinking`: Multi-step deliberative reasoning.
   - `filesystem`: Air-gapped file viewing, editing, listing, and storage.
   - `memory`: Knowledge graph entity and relation tracking for refinery assets.
   - Vision & Reasoning Subagents: Qwen2-VL for P&ID schematics, DeepSeek-R1 for complex thermodynamics and cost synthesis, Qwen-Coder for Python scripting.

You MUST respond strictly with valid JSON with NO commentary outside the JSON.
Schema:
{
  "title": "Short descriptive title of the plan",
  "task_type": "MULTI_STEP_INDUSTRIAL | CODING_SANDBOX | DRAWING_INSPECTION | MANAGEMENT_DECK | INQUIRY",
  "skill": "inspection-report | code-sandbox | pid-inspection | management-presentation | null",
  "model_profile": "e.g. DeepSeek-R1 + Qwen2-VL",
  "plan": "Detailed multi-paragraph Markdown strategy explaining: 1. Objective & Scope, 2. What can be done, 3. Methodology & Risk Controls, 4. Required Sign-offs.",
  "check_list": [
    {
      "id": "step_1",
      "task": "Actionable task description",
      "tool": "name_of_tool_to_use",
      "status": "pending"
    }
  ]
}
"""


def generate_plan(
    user_prompt: str,
    intent: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Generates a structured multi-step plan tailored to the classified task type with
    detailed markdown strategy and checklist.
    """
    task_type = intent.get("task_type", "INQUIRY")
    plan_id = f"plan_{secrets.token_hex(4)}"

    # 1. Scanned Inspection Report Workflow (Demo 1)
    if task_type == "MULTI_STEP_INDUSTRIAL":
        plan_markdown = (
            "### Refinery Asset Integrity Assessment & SOP Verification\n\n"
            "**Operational Context:**\n"
            "Evaluating high-temperature crude distillation overhead system (CDU-II). Ingests inspector field ultrasonic thickness "
            "measurements, cross-references against live SCADA operating pressures and temperatures, and validates adherence to "
            "MRPL maintenance safety limits.\n\n"
            "**Planned Technical Strategy:**\n"
            "1. **Document Intelligence & OCR Ingestion**: Parse non-destructive ultrasonic testing (NDT) logs from scan artifacts.\n"
            "2. **SCADA Baseline Cross-Correlation**: Ingest live telemetry from column C-101 and condenser train E-101 to assess active acid gas dew point corrosion.\n"
            "3. **Refinery SOP Compliance**: Search MRPL Standard Operating Procedures (SOP-MRPL-4.2.3) for minimum allowable wall thickness (MAWT).\n"
            "4. **Engineering Synthesis**: Formulate corrosion mitigation protocol including neutralizing amine wash optimization.\n"
            "5. **Executive Sign-off Artifact**: Generate signed Word deliverable (`CDU_Overhead_Corrosion_Approval_Note.docx`)."
        )
        check_list = [
            {
                "id": "step_1",
                "task": "Ingest Scanned Inspection PDF & OCR Extraction",
                "tool": "load_skill",
                "status": "pending"
            },
            {
                "id": "step_2",
                "task": "Structure Observations & Cross-Verify SCADA Telemetry (C-101)",
                "tool": "query_refinery_telemetry",
                "status": "pending"
            },
            {
                "id": "step_3",
                "task": "Query & Cross-Verify MRPL Maintenance SOPs (Clause 4.2.3)",
                "tool": "search_refinery_sops",
                "status": "pending"
            },
            {
                "id": "step_4",
                "task": "Synthesize Technical Recommendations & Amine Wash Protocol",
                "tool": "sequential_thinking",
                "status": "pending"
            },
            {
                "id": "step_5",
                "task": "Generate Official Word Approval Deliverable (.docx)",
                "tool": "generate_docx_approval_note",
                "status": "pending"
            }
        ]
        return {
            "plan_id": plan_id,
            "title": "Inspection Report Analysis & SOP Approval Note",
            "task_type": task_type,
            "skill": "inspection-report",
            "model_profile": "DeepSeek-R1 (Local Reasoning) + Qwen2-VL",
            "status": "PENDING_APPROVAL",
            "plan": plan_markdown,
            "check_list": check_list,
            "steps": [
                {
                    "step_id": i + 1,
                    "title": it["task"],
                    "tool": it["tool"],
                    "status": it["status"]
                }
                for i, it in enumerate(check_list)
            ],
            "total_steps": len(check_list)
        }

    # 2. Coding & Sandbox Self-Repair Workflow (Demo 2)
    elif task_type == "CODING_SANDBOX":
        plan_markdown = (
            "### Autonomous Code Generation & Air-Gapped Sandbox Self-Repair\n\n"
            "**Operational Context:**\n"
            "Authoring an on-premise industrial data processing pipeline to parse unstructured refinery sensor logs and "
            "isolate critical thermal anomalies without data exfiltration.\n\n"
            "**Planned Technical Strategy:**\n"
            "1. **Schema & Anomaly Inspection**: Activate code-sandbox skill to inspect workspace layout and sample sensor records.\n"
            "2. **Script & Unit Test Generation**: Author clean, vectorized Python utility (`process_anomalies.py`) with strict unit tests.\n"
            "3. **Air-gapped Sandbox Execution**: Execute script within the isolated local sandbox environment.\n"
            "4. **Autonomous Self-Repair**: If an assertion fails or runtime exception occurs, inspect stderr, patch code, and iterate.\n"
            "5. **Artifact Validation**: Verify generated `critical_findings.csv` and report file hash."
        )
        check_list = [
            {
                "id": "step_1",
                "task": "Inspect Workspace Schemas & Telemetry Anomaly Findings",
                "tool": "load_skill",
                "status": "pending"
            },
            {
                "id": "step_2",
                "task": "Generate Python Automation Utility & Test Suite",
                "tool": "filesystem",
                "status": "pending"
            },
            {
                "id": "step_3",
                "task": "Execute in Isolated Sandbox & Autonomous Self-Repair",
                "tool": "run_code_in_sandbox",
                "status": "pending"
            },
            {
                "id": "step_4",
                "task": "Verify Final Script & Workspace Output Artifacts",
                "tool": "execute_terminal_command",
                "status": "pending"
            }
        ]
        return {
            "plan_id": plan_id,
            "title": "Autonomous Python Utility Development & Sandbox Verification",
            "task_type": task_type,
            "skill": "code-sandbox",
            "model_profile": "Qwen-Coder (Local Code Specialist)",
            "status": "PENDING_APPROVAL",
            "plan": plan_markdown,
            "check_list": check_list,
            "steps": [
                {
                    "step_id": i + 1,
                    "title": it["task"],
                    "tool": it["tool"],
                    "status": it["status"]
                }
                for i, it in enumerate(check_list)
            ],
            "total_steps": len(check_list)
        }

    # 3. P&ID Drawing Inspection Workflow (Demo 3)
    elif task_type == "DRAWING_INSPECTION":
        plan_markdown = (
            "### P&ID Schematic Inspection & Controlled Uncertainty Mapping\n\n"
            "**Operational Context:**\n"
            "Scanning and validating complex Piping & Instrumentation Diagrams for CDU-II overhead and feed pre-heat train. "
            "Enforces zero-hallucination policy and flags ambiguous junction tags for human operator confirmation.\n\n"
            "**Planned Technical Strategy:**\n"
            "1. **Vision Pipeline Activation**: Activate `pid-inspection` skill and segment high-resolution schematic sheets.\n"
            "2. **Tag & Valve Extraction**: Detect instrument tags (PT, TT, FT, XV) and equipment labels (C-101, P-101A/B).\n"
            "3. **Process Topology Mapping**: Trace process lines from crude feed to overhead condenser relief valves.\n"
            "4. **Uncertainty Governance**: Flag ambiguous tag overlaps or low-contrast hand annotations for human sign-off."
        )
        check_list = [
            {
                "id": "step_1",
                "task": "Load P&ID Drawing & Activate Vision Pipeline",
                "tool": "load_skill",
                "status": "pending"
            },
            {
                "id": "step_2",
                "task": "Extract Labeled Equipment, Valves & Instruments",
                "tool": "inspect_refinery_unit",
                "status": "pending"
            },
            {
                "id": "step_3",
                "task": "Trace End-to-End Process Flow Topology",
                "tool": "sequential_thinking",
                "status": "pending"
            },
            {
                "id": "step_4",
                "task": "Enforce Controlled Uncertainty & Flag Ambiguities for Human Review",
                "tool": "memory",
                "status": "pending"
            }
        ]
        return {
            "plan_id": plan_id,
            "title": "P&ID Schematic Inspection & Controlled Uncertainty Mapping",
            "task_type": task_type,
            "skill": "pid-inspection",
            "model_profile": "Qwen2-VL (Local Vision Specialist)",
            "status": "PENDING_APPROVAL",
            "plan": plan_markdown,
            "check_list": check_list,
            "steps": [
                {
                    "step_id": i + 1,
                    "title": it["task"],
                    "tool": it["tool"],
                    "status": it["status"]
                }
                for i, it in enumerate(check_list)
            ],
            "total_steps": len(check_list)
        }

    # 4. Management Presentation & Cost Synthesis (Demo 4)
    elif task_type == "MANAGEMENT_DECK":
        plan_markdown = (
            "### Executive Capital Review & Cross-Artifact Cost Synthesis\n\n"
            "**Operational Context:**\n"
            "Consolidating refinery equipment inspection findings, maintenance labor rates, and metallurgical replacement costs "
            "into synchronized executive deliverables for management approval.\n\n"
            "**Planned Technical Strategy:**\n"
            "1. **Data Aggregation**: Query active maintenance work orders and inspection findings for C-101 and K-201.\n"
            "2. **Financial Cost Modeling**: Generate multi-sheet dynamic Excel workbook (`Inspection_Cost_Analysis.xlsx`) with automated formulas.\n"
            "3. **Executive Presentation**: Build high-impact 16:9 executive presentation deck (`Asset_Integrity_Review.pptx`).\n"
            "4. **Cross-Artifact Consistency Check**: Programmatically verify that financial totals and critical counts match exactly across Word, Excel, and PowerPoint.\n"
            "5. **Final Review & Packaging**: Inspect workspace outputs and verify deliverables."
        )
        check_list = [
            {
                "id": "step_1",
                "task": "Aggregate Inspection Data & Maintenance Work Orders",
                "tool": "search_refinery_sops",
                "status": "pending"
            },
            {
                "id": "step_2",
                "task": "Generate Excel Cost Analysis Workbook (.xlsx)",
                "tool": "generate_xlsx_cost_workbook",
                "status": "pending"
            },
            {
                "id": "step_3",
                "task": "Generate Executive PowerPoint Presentation (.pptx)",
                "tool": "generate_pptx_deck",
                "status": "pending"
            },
            {
                "id": "step_4",
                "task": "Perform Automated Cross-Artifact Consistency Verification",
                "tool": "verify_artifact_consistency",
                "status": "pending"
            },
            {
                "id": "step_5",
                "task": "Final Review & Deliverable Packaging",
                "tool": "execute_terminal_command",
                "status": "pending"
            }
        ]
        return {
            "plan_id": plan_id,
            "title": "Executive Presentation & Cross-Artifact Cost Synthesis",
            "task_type": task_type,
            "skill": "management-presentation",
            "model_profile": "DeepSeek-R1 (Local Reasoning Specialist)",
            "status": "PENDING_APPROVAL",
            "plan": plan_markdown,
            "check_list": check_list,
            "steps": [
                {
                    "step_id": i + 1,
                    "title": it["task"],
                    "tool": it["tool"],
                    "status": it["status"]
                }
                for i, it in enumerate(check_list)
            ],
            "total_steps": len(check_list)
        }

    # Default Single-step Plan
    default_markdown = (
        f"### Direct Operational Analysis: {user_prompt[:50]}\n\n"
        "**Scope & Objective:**\n"
        f"Address the operator inquiry regarding '{user_prompt}' using on-premise knowledge and refinery telemetry.\n\n"
        "**Execution Strategy:**\n"
        "Perform direct engineering reasoning and query on-premise telemetry or documentation if required."
    )
    check_list = [
        {
            "id": "step_1",
            "task": f"Analyze and respond to inquiry: {user_prompt[:60]}",
            "tool": "direct_reply",
            "status": "pending"
        }
    ]
    return {
        "plan_id": plan_id,
        "title": f"Plan: {user_prompt[:35]}",
        "task_type": "INQUIRY",
        "skill": None,
        "model_profile": "default",
        "status": "PENDING_APPROVAL",
        "plan": default_markdown,
        "check_list": check_list,
        "steps": [
            {
                "step_id": 1,
                "title": check_list[0]["task"],
                "tool": check_list[0]["tool"],
                "status": "pending"
            }
        ],
        "total_steps": 1
    }


async def generate_plan_async(
    user_prompt: str,
    intent: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Attempts to generate a comprehensive dynamic plan via the local LLM.
    Falls back gracefully to domain template if LLM is unavailable or unparseable.
    """
    plan_id = f"plan_{secrets.token_hex(4)}"
    try:
        user_msg = f"User Prompt: {user_prompt}"
        if context:
            user_msg += f"\nContext: {json.dumps(context)}"

        req = ModelRequest(
            user_content=user_msg,
            system_content=PLANNING_AGENT_SYSTEM_PROMPT,
            model="default",
            temperature=0.2,
            stream=False,
            thinking=False
        )
        response = await send_async_chat_request(req)
        if response and response.choices:
            raw_text = response.choices[0].message.content or ""
            # Strip markdown fences
            cleaned = re.sub(r"^```(?:json)?", "", raw_text.strip(), flags=re.MULTILINE)
            cleaned = re.sub(r"```$", "", cleaned.strip(), flags=re.MULTILINE).strip()
            json_match = re.search(r"\{[\s\S]*\}", cleaned)
            if json_match:
                data = json.loads(json_match.group(0))
                if "plan" in data and "check_list" in data and isinstance(data["check_list"], list) and len(data["check_list"]) > 0:
                    check_list = []
                    for idx, it in enumerate(data["check_list"]):
                        check_list.append({
                            "id": it.get("id", f"step_{idx+1}"),
                            "task": it.get("task", f"Step {idx+1}"),
                            "tool": it.get("tool", "system_tool"),
                            "status": it.get("status", "pending")
                        })
                    return {
                        "plan_id": plan_id,
                        "title": data.get("title", f"Plan: {user_prompt[:40]}"),
                        "task_type": data.get("task_type", intent.get("task_type", "INQUIRY")),
                        "skill": data.get("skill"),
                        "model_profile": data.get("model_profile", "DeepSeek-R1 / Local Agent"),
                        "status": "PENDING_APPROVAL",
                        "plan": data["plan"],
                        "check_list": check_list,
                        "steps": [
                            {
                                "step_id": i + 1,
                                "title": it["task"],
                                "tool": it["tool"],
                                "status": it["status"]
                            }
                            for i, it in enumerate(check_list)
                        ],
                        "total_steps": len(check_list)
                    }
    except Exception:
        pass

    return generate_plan(user_prompt, intent, context)

