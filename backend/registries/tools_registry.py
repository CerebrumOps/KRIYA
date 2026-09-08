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


# 1. Dictionary mapping tool names directly to the actual Python functions
TOOLS_MAP: Dict[str, Any] = {
    "execute_terminal_command": execute_terminal_command,
    "search_duckduckgo": search_duckduckgo,
}


# 2. List of all tool schemas in OpenAI format
TOOLS_SCHEMA: List[Dict[str, Any]] = [
    TERMINAL_TOOL_SCHEMA,
    WEBSEARCH_TOOL_SCHEMA,
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
