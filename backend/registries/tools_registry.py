# ==============================================================================
# KRIYA - Central Tools Registry
# ==============================================================================
# This file registers all available tools and their OpenAI schemas.
# 1. TOOLS_MAP: Dictionary linking tool function names to actual Python functions
# 2. TOOLS_SCHEMA: List of OpenAI schemas sent to the model so it knows how to call tools
# 3. execute_tool: Helper function to execute any tool by name
# ==============================================================================

import json
from typing import Any, Dict, List
from backend.tools.terminal import execute_terminal_command, TERMINAL_TOOL_SCHEMA
from backend.tools.websearch import search_duckduckgo, WEBSEARCH_TOOL_SCHEMA
from backend.tools.skill_tools import (
    list_available_skills,
    load_skill,
    inspect_mcp_servers,
    LIST_AVAILABLE_SKILLS_SCHEMA,
    LOAD_SKILL_SCHEMA,
    INSPECT_MCP_SERVERS_SCHEMA
)
from backend.tools.deliverable_generator import (
    generate_docx_approval_note,
    generate_xlsx_cost_workbook,
    generate_pptx_deck,
    verify_artifact_consistency,
    DOCX_TOOL_SCHEMA,
    XLSX_TOOL_SCHEMA,
    PPTX_TOOL_SCHEMA,
    VERIFY_CONSISTENCY_SCHEMA
)
from backend.tools.docker_sandbox import run_code_in_sandbox, SANDBOX_TOOL_SCHEMA
from backend.tools.refinery_tools import (
    search_refinery_sops_tool,
    query_refinery_telemetry_tool,
    inspect_refinery_unit_tool,
    list_active_work_orders_tool,
    SEARCH_SOPS_SCHEMA,
    QUERY_TELEMETRY_SCHEMA,
    INSPECT_UNIT_SCHEMA,
    LIST_WORK_ORDERS_SCHEMA
)


# 1. Dictionary mapping tool names directly to the actual Python functions
TOOLS_MAP: Dict[str, Any] = {
    # System & Web
    "execute_terminal_command": execute_terminal_command,
    "search_duckduckgo": search_duckduckgo,

    # Progressive Skill & MCP Discovery
    "list_available_skills": list_available_skills,
    "load_skill": load_skill,
    "inspect_mcp_servers": inspect_mcp_servers,

    # Deliverables & Verification
    "generate_docx_approval_note": generate_docx_approval_note,
    "generate_xlsx_cost_workbook": generate_xlsx_cost_workbook,
    "generate_pptx_deck": generate_pptx_deck,
    "verify_artifact_consistency": verify_artifact_consistency,

    # Sandboxed Code Execution
    "run_code_in_sandbox": run_code_in_sandbox,

    # Refinery Plant Intelligence
    "search_refinery_sops": search_refinery_sops_tool,
    "query_refinery_telemetry": query_refinery_telemetry_tool,
    "inspect_refinery_unit": inspect_refinery_unit_tool,
    "list_active_work_orders": list_active_work_orders_tool,
}


# 2. List of all tool schemas in OpenAI format
TOOLS_SCHEMA: List[Dict[str, Any]] = [
    TERMINAL_TOOL_SCHEMA,
    WEBSEARCH_TOOL_SCHEMA,

    # Progressive Skill Discovery Meta-Tools (Compact)
    LIST_AVAILABLE_SKILLS_SCHEMA,
    LOAD_SKILL_SCHEMA,
    INSPECT_MCP_SERVERS_SCHEMA,

    # Deliverables
    DOCX_TOOL_SCHEMA,
    XLSX_TOOL_SCHEMA,
    PPTX_TOOL_SCHEMA,
    VERIFY_CONSISTENCY_SCHEMA,

    # Sandbox
    SANDBOX_TOOL_SCHEMA,

    # Refinery Intelligence
    SEARCH_SOPS_SCHEMA,
    QUERY_TELEMETRY_SCHEMA,
    INSPECT_UNIT_SCHEMA,
    LIST_WORK_ORDERS_SCHEMA,
]


# 3. Helper function to call a tool by name with arguments
def execute_tool(tool_name: str, arguments: Any) -> str:
    """
    Executes the registered tool function matching `tool_name`
    with the given arguments (which can be a dictionary or a JSON string).
    Returns the string result of the tool.
    """
    # If arguments came as a JSON string from the model, parse it into a dict
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except Exception:
            arguments = {"command": arguments}

    # Verify tool exists in the registry
    if tool_name not in TOOLS_MAP:
        return f"[Error]: Tool '{tool_name}' is not registered in tools_registry."

    func = TOOLS_MAP[tool_name]

    try:
        if isinstance(arguments, dict):
            return func(**arguments)
        else:
            return func(arguments)
    except Exception as error:
        return f"[Error running tool '{tool_name}']: {str(error)}"
