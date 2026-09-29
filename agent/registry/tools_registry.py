# ==============================================================================
# KRIYA - Central Tools Registry
# ==============================================================================
# Registers all available sovereign industrial tools and their OpenAI schemas.
# 1. TOOLS_MAP: Dictionary linking tool function names to actual Python functions
# 2. BASE_TOOLS_SCHEMA: Base container and workbench tool schemas
# 3. get_active_tools_schema: Combines base tools with live, dynamically fetched
#    MCP tool schemas from the sovereign FastMCP server
# 4. execute_tool: Helper function to execute any tool by name
# ==============================================================================

import json
from typing import Any, Dict, List

from agent.tools.terminal import execute_terminal_command, TERMINAL_TOOL_SCHEMA
from agent.tools.skills_terminal import execute_skills_terminal, SKILLS_TERMINAL_SCHEMA
from agent.tools.websearch import search_duckduckgo, WEBSEARCH_TOOL_SCHEMA
from agent.tools.host_bridge import (
    read_host_file,
    write_host_file,
    list_host_files,
    execute_host_command,
    READ_HOST_FILE_SCHEMA,
    WRITE_HOST_FILE_SCHEMA,
    LIST_HOST_FILES_SCHEMA,
    EXECUTE_HOST_COMMAND_SCHEMA,
)
from agent.tools.skill_tools import (
    list_available_skills,
    load_skill,
    inspect_mcp_servers,
    LIST_AVAILABLE_SKILLS_SCHEMA,
    LOAD_SKILL_SCHEMA,
    INSPECT_MCP_SERVERS_SCHEMA,
)
from agent.subagents.memory_agent import (
    store_agent_memory,
    search_and_summarize_memories,
    STORE_MEMORY_SCHEMA,
    RETRIEVE_MEMORY_SCHEMA,
)
from agent.MCP_client.company_mcp import (
    call_fastmcp_tool,
    fetch_dynamic_mcp_schemas,
    get_live_mcp_telemetry,
    get_all_mcp_units_status,
)

# 1. SCADA Telemetry & Plant Status REST Adapters Schemas
GET_LIVE_MCP_TELEMETRY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_live_mcp_telemetry",
        "description": "Queries live refinery SCADA sensors and active alarms from the MRPL FastMCP server (e.g. CDU-II, FCCU, DHT, HGU).",
        "parameters": {
            "type": "object",
            "properties": {
                "unit_tag": {
                    "type": "string",
                    "description": "Refinery unit tag (e.g. 'CDU-II', 'FCCU', 'DHT', 'HGU')"
                }
            },
            "required": ["unit_tag"]
        }
    }
}

GET_ALL_MCP_UNITS_STATUS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_all_mcp_units_status",
        "description": "Retrieves real-time plant-wide health scores and active alarms across all refinery operating units from the FastMCP server.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

# 2. Dictionary mapping base tool names directly to Python functions
TOOLS_MAP: Dict[str, Any] = {
    # System & Terminals (Container OS Root Shell)
    "execute_terminal_command": execute_terminal_command,
    "execute_skills_terminal": execute_skills_terminal,
    "search_duckduckgo": search_duckduckgo,

    # Host System & File Bridge (Shared ~/kriya-shared folder)
    "read_host_file": read_host_file,
    "write_host_file": write_host_file,
    "list_host_files": list_host_files,
    "execute_host_command": execute_host_command,

    # Progressive Skill & MCP Discovery
    "list_available_skills": list_available_skills,
    "load_skill": load_skill,
    "inspect_mcp_servers": inspect_mcp_servers,

    # Subagents Callable as Tools
    "store_agent_memory": store_agent_memory,
    "search_and_summarize_memories": search_and_summarize_memories,

    # SCADA Telemetry Adapters
    "get_live_mcp_telemetry": get_live_mcp_telemetry,
    "get_all_mcp_units_status": get_all_mcp_units_status,
}

# 3. Base tool schemas for local container and workbench tools
BASE_TOOLS_SCHEMA: List[Dict[str, Any]] = [
    # Terminals & Search
    TERMINAL_TOOL_SCHEMA,
    SKILLS_TERMINAL_SCHEMA,
    WEBSEARCH_TOOL_SCHEMA,

    # Host System & File Bridge
    READ_HOST_FILE_SCHEMA,
    WRITE_HOST_FILE_SCHEMA,
    LIST_HOST_FILES_SCHEMA,
    EXECUTE_HOST_COMMAND_SCHEMA,

    # Progressive Skill Discovery
    LIST_AVAILABLE_SKILLS_SCHEMA,
    LOAD_SKILL_SCHEMA,
    INSPECT_MCP_SERVERS_SCHEMA,

    # Subagent Tools
    STORE_MEMORY_SCHEMA,
    RETRIEVE_MEMORY_SCHEMA,

    # SCADA Telemetry
    GET_LIVE_MCP_TELEMETRY_SCHEMA,
    GET_ALL_MCP_UNITS_STATUS_SCHEMA,
]


def get_active_tools_schema(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Returns the complete list of active tool schemas for the LLM:
    1. Base container & workbench tools (terminals, bridge, memory, skills)
    2. Dynamic tools fetched from the sovereign FastMCP server via tools/list
       with full OpenAI-style parameter descriptions and constraints.
    """
    dynamic_mcp_tools = fetch_dynamic_mcp_schemas(force_refresh=force_refresh)
    return list(BASE_TOOLS_SCHEMA) + dynamic_mcp_tools


def __getattr__(name: str) -> Any:
    """Module-level attribute fallback to support legacy `from tools_registry import TOOLS_SCHEMA`."""
    if name == "TOOLS_SCHEMA":
        return get_active_tools_schema()
    raise AttributeError(f"module {__name__} has no attribute '{name}'")


# 4. Helper function to call a tool by name with arguments
def execute_tool(tool_name: str, arguments: Any) -> str:
    """
    Executes the registered tool function matching `tool_name`
    with the given arguments (which can be a dictionary or a JSON string).
    If tool_name is not a local tool, dispatches dynamically to the remote FastMCP server.
    """
    if isinstance(arguments, str):
        try:
            arguments = json.loads(arguments)
        except Exception:
            arguments = {"command": arguments}

    if not isinstance(arguments, dict):
        arguments = {}

    # 1. Registered local / built-in tools
    if tool_name in TOOLS_MAP:
        func = TOOLS_MAP[tool_name]
        try:
            return func(**arguments)
        except Exception as error:
            return f"[Error running tool '{tool_name}']: {str(error)}"

    # 2. Dynamic remote FastMCP dispatch
    try:
        return call_fastmcp_tool(tool_name, arguments)
    except Exception as error:
        return f"[Error]: Tool '{tool_name}' failed during FastMCP execution: {str(error)}"
