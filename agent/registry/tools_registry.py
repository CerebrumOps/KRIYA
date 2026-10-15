# ==============================================================================
# KRIYA - Central Tools Registry
# ==============================================================================
# Registers all available sovereign industrial tools and their OpenAI schemas.
# 1. TOOLS_MAP: Dictionary linking local tool names to Python functions
# 2. BASE_TOOLS_SCHEMA: Base container and workbench tool schemas
# 3. get_active_tools_schema: Combines base tools with live, dynamically fetched
#    MCP tool schemas (26 tools) from the sovereign FastMCP server on Raspberry Pi
# 4. execute_tool: Dispatches tool by name (local tool or remote FastMCP call)
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
    share_file_to_host,
    READ_HOST_FILE_SCHEMA,
    WRITE_HOST_FILE_SCHEMA,
    LIST_HOST_FILES_SCHEMA,
    EXECUTE_HOST_COMMAND_SCHEMA,
    SHARE_FILE_TO_HOST_SCHEMA,
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
from agent.tools.ocr_tool import ocr_extract_text, OCR_TOOL_SCHEMA
from agent.tools.document_generators import (
    generate_word_document,
    generate_excel_spreadsheet,
    generate_powerpoint_deck,
    GENERATE_WORD_DOCUMENT_SCHEMA,
    GENERATE_EXCEL_SPREADSHEET_SCHEMA,
    GENERATE_POWERPOINT_DECK_SCHEMA,
)
from agent.MCP_client.company_mcp import (
    call_fastmcp_tool,
    fetch_dynamic_mcp_schemas,
)

# 1. Dictionary mapping base tool names directly to Python functions
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
    "share_file_to_host": share_file_to_host,

    # Enterprise Deliverable & Document Generators (with Metadata & Signature Blocks)
    "generate_word_document": generate_word_document,
    "generate_excel_spreadsheet": generate_excel_spreadsheet,
    "generate_powerpoint_deck": generate_powerpoint_deck,

    # Progressive Skill & MCP Discovery
    "list_available_skills": list_available_skills,
    "load_skill": load_skill,
    "inspect_mcp_servers": inspect_mcp_servers,

    # Subagents Callable as Tools
    "store_agent_memory": store_agent_memory,
    "search_and_summarize_memories": search_and_summarize_memories,

    # Sovereign OCR & Document Parser (Photos, Scans, PDFs)
    "ocr_extract_text": ocr_extract_text,
    "extract_document_text": ocr_extract_text,
}

# 2. Base tool schemas for local container and workbench tools
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
    SHARE_FILE_TO_HOST_SCHEMA,

    # Enterprise Deliverable & Document Generators
    GENERATE_WORD_DOCUMENT_SCHEMA,
    GENERATE_EXCEL_SPREADSHEET_SCHEMA,
    GENERATE_POWERPOINT_DECK_SCHEMA,

    # Sovereign OCR & Document Parser
    OCR_TOOL_SCHEMA,

    # Progressive Skill Discovery
    LIST_AVAILABLE_SKILLS_SCHEMA,
    LOAD_SKILL_SCHEMA,
    INSPECT_MCP_SERVERS_SCHEMA,

    # Subagent Tools
    STORE_MEMORY_SCHEMA,
    RETRIEVE_MEMORY_SCHEMA,
]


def get_active_tools_schema(force_refresh: bool = False) -> List[Dict[str, Any]]:
    """
    Returns the complete list of active tool schemas for the LLM:
    1. Base container & workbench tools (terminals, bridge, memory, skills)
    2. Dynamic tools fetched from the sovereign FastMCP server via tools/list
       with full OpenAI-style parameter descriptions and constraints (26 tools).
    """
    dynamic_mcp_tools = fetch_dynamic_mcp_schemas(force_refresh=force_refresh)
    return list(BASE_TOOLS_SCHEMA) + dynamic_mcp_tools


def __getattr__(name: str) -> Any:
    """Module-level attribute fallback to support legacy `from tools_registry import TOOLS_SCHEMA`."""
    if name == "TOOLS_SCHEMA":
        return get_active_tools_schema()
    raise AttributeError(f"module {__name__} has no attribute '{name}'")


# 3. Helper function to call a tool by name with arguments
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
