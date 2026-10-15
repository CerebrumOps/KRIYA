# ==============================================================================
# KRIYA MCP Client: Sovereign Company Database & FastMCP Gateway Integration
# ==============================================================================
# Connects dynamically to the Sovereign FastMCP Gateway running on Raspberry Pi 5.
# Implements the official protocol from MCP_DOCUMENTATION.md:
# - Dynamic tool schema discovery via JSON-RPC over SSE (tools/list)
# - Tool invocation via JSON-RPC over SSE (tools/call)
# - Handshake authentication protocol (handshake_authenticate) for multi-tier RBAC
# - Safe Read-Only guarantee (hardware enforced on PostgreSQL company_db)
# ==============================================================================

import json
import logging
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from dotenv import load_dotenv

logger = logging.getLogger("kriya.mcp")

env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

REMOTE_MCP_URL = os.getenv("REMOTE_MCP_URL", "http://100.98.154.51:8085")

# In-memory schema cache to prevent repeated SSE handshakes on every turn
_MCP_SCHEMA_CACHE: List[Dict[str, Any]] = []
_MCP_CACHE_TIMESTAMP: float = 0.0
_MCP_CACHE_TTL: float = 120.0  # 2 minutes TTL

# Track active handshaked employee code on gateway
_CURRENT_HANDSHAKE_EMP: Optional[str] = None


def fetch_dynamic_mcp_schemas(force_refresh: bool = False, timeout: float = 12.0) -> List[Dict[str, Any]]:
    """
    Dynamically queries the remote FastMCP server (tools/list) and converts
    each discovered tool into standard OpenAI function calling format:
    {
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["description"],
            "parameters": tool["inputSchema"]
        }
    }
    """
    global _MCP_SCHEMA_CACHE, _MCP_CACHE_TIMESTAMP

    now = time.time()
    if not force_refresh and _MCP_SCHEMA_CACHE and (now - _MCP_CACHE_TIMESTAMP < _MCP_CACHE_TTL):
        return _MCP_SCHEMA_CACHE

    base_url = REMOTE_MCP_URL.rstrip("/")
    sse_url = f"{base_url}/sse"

    try:
        # 1. Connect to SSE stream
        req = urllib.request.Request(sse_url, headers={"User-Agent": "KRIYA-Dynamic-MCP-Client"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        resp.readline()  # event: endpoint
        data_line = resp.readline().decode("utf-8")
        post_endpoint = data_line.replace("data: ", "").strip()
        post_url = f"{base_url}{post_endpoint}"

        # 2. JSON-RPC Handshake: Initialize
        init_payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "kriya-agent", "version": "2.0"}
            }
        }).encode("utf-8")
        urllib.request.urlopen(
            urllib.request.Request(post_url, data=init_payload, headers={"Content-Type": "application/json"}),
            timeout=timeout
        )

        # 3. JSON-RPC Request: tools/list
        tools_payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {}
        }).encode("utf-8")
        urllib.request.urlopen(
            urllib.request.Request(post_url, data=tools_payload, headers={"Content-Type": "application/json"}),
            timeout=timeout
        )

        # 4. Read response from SSE stream
        for _ in range(25):
            line = resp.readline().decode("utf-8")
            if line.startswith("data:"):
                msg = json.loads(line.replace("data: ", ""))
                if msg.get("id") == 2:
                    raw_tools = msg.get("result", {}).get("tools", [])
                    openai_tools = []
                    # Never expose session-switching tools to the LLM to prevent RBAC privilege escalation
                    blocked_llm_tools = {"handshake_authenticate", "reset_session_to_guest"}
                    for t in raw_tools:
                        t_name = t.get("name", "")
                        if t_name in blocked_llm_tools:
                            continue
                        input_schema = t.get("inputSchema") or {}
                        properties = input_schema.get("properties", {})
                        required = input_schema.get("required", [])

                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": t_name,
                                "description": t.get("description", ""),
                                "parameters": {
                                    "type": "object",
                                    "properties": properties,
                                    "required": required
                                }
                            }
                        })

                    _MCP_SCHEMA_CACHE = openai_tools
                    _MCP_CACHE_TIMESTAMP = now
                    logger.info(f"Discovered {len(openai_tools)} tools from FastMCP gateway at {REMOTE_MCP_URL}")
                    return _MCP_SCHEMA_CACHE

    except Exception as e:
        logger.warning(f"Could not dynamically discover tools from FastMCP at {REMOTE_MCP_URL}: {e}")
        if _MCP_SCHEMA_CACHE:
            return _MCP_SCHEMA_CACHE

    return []


def _raw_call_fastmcp(tool_name: str, arguments: Optional[Dict[str, Any]] = None, timeout: float = 12.0) -> str:
    """
    Low-level JSON-RPC over SSE call to the remote FastMCP server.
    """
    arguments = arguments or {}
    base_url = REMOTE_MCP_URL.rstrip("/")
    sse_url = f"{base_url}/sse"

    try:
        # 1. Connect to SSE stream to acquire session ID
        req = urllib.request.Request(sse_url, headers={"User-Agent": "KRIYA-Dynamic-MCP-Client"})
        resp = urllib.request.urlopen(req, timeout=timeout)
        resp.readline()  # event: endpoint
        data_line = resp.readline().decode("utf-8")
        post_endpoint = data_line.replace("data: ", "").strip()
        post_url = f"{base_url}{post_endpoint}"

        # 2. Protocol Handshake: Initialize
        init_payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "kriya-agent", "version": "2.0"}
            }
        }).encode("utf-8")
        init_req = urllib.request.Request(post_url, data=init_payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(init_req, timeout=timeout)

        # 3. Dispatch Tool Call
        call_payload = json.dumps({
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments}
        }).encode("utf-8")
        call_req = urllib.request.Request(post_url, data=call_payload, headers={"Content-Type": "application/json"})
        urllib.request.urlopen(call_req, timeout=timeout)

        # 4. Read SSE response stream for tool result
        for _ in range(30):
            line = resp.readline().decode("utf-8")
            if line.startswith("data:"):
                msg_data = json.loads(line.replace("data: ", ""))
                if msg_data.get("id") == 2:
                    res = msg_data.get("result", {})
                    content = res.get("content", [])
                    if content and isinstance(content, list):
                        return content[0].get("text", json.dumps(res, indent=2))
                    return json.dumps(res, indent=2)

        return "[Error]: MCP tool call timed out waiting for response."

    except Exception as e:
        return f"[Error executing MCP tool '{tool_name}' on server {REMOTE_MCP_URL}]: {str(e)}"


def call_fastmcp_tool(tool_name: str, arguments: Optional[Dict[str, Any]] = None, timeout: float = 12.0) -> str:
    """
    Executes a tool on the remote FastMCP server while strictly enforcing the
    logged-in employee's RBAC identity. Blocks any LLM attempt to escalate privileges
    via handshake_authenticate or reset_session_to_guest.
    """
    arguments = arguments or {}

    try:
        from agent.workspace.workspace_manager import get_active_employee_id
        active_emp = get_active_employee_id()
    except Exception:
        active_emp = None

    # Block LLM from switching or spoofing employee identity
    if tool_name in ("handshake_authenticate", "reset_session_to_guest"):
        requested_emp = arguments.get("emp_code")
        if active_emp and requested_emp and requested_emp.strip().upper() != active_emp.strip().upper():
            return json.dumps({
                "status": "ACCESS_DENIED",
                "error": "RBAC_PRIVILEGE_ESCALATION_BLOCKED",
                "message": (
                    f"Security Violation: Session is cryptographically locked to authenticated employee '{active_emp}'. "
                    f"Switching or impersonating employee '{requested_emp}' is strictly forbidden."
                ),
            })
        if active_emp:
            ensure_mcp_handshake(active_emp, force=True)
            return _raw_call_fastmcp("get_current_session", {}, timeout=timeout)

    # Always ensure the gateway session matches the logged-in user before running any tool
    if active_emp and active_emp != "default_user":
        ensure_mcp_handshake(active_emp)
    else:
        ensure_mcp_handshake("GUEST")

    return _raw_call_fastmcp(tool_name, arguments, timeout=timeout)


def ensure_mcp_handshake(emp_code: Optional[str], force: bool = False) -> Optional[str]:
    """
    Ensures that the FastMCP gateway has established session authentication
    for the given logged-in employee code, or resets to guest if unauthenticated.
    """
    global _CURRENT_HANDSHAKE_EMP
    normalized = (emp_code or "GUEST").strip().upper()
    if normalized in ("", "DEFAULT_USER", "GUEST", "NONE"):
        if not force and _CURRENT_HANDSHAKE_EMP == "GUEST":
            return None
        try:
            result = _raw_call_fastmcp("reset_session_to_guest", {})
            _CURRENT_HANDSHAKE_EMP = "GUEST"
            logger.info("FastMCP gateway session reset to GUEST (Clearance Level 1).")
            return result
        except Exception as e:
            logger.warning(f"Could not reset MCP session to guest: {e}")
            return None

    if not force and _CURRENT_HANDSHAKE_EMP == normalized:
        return None
    try:
        result = _raw_call_fastmcp("handshake_authenticate", {"emp_code": normalized})
        _CURRENT_HANDSHAKE_EMP = normalized
        logger.info(f"Handshake locked to authenticated employee {normalized} on FastMCP gateway.")
        return result
    except Exception as e:
        logger.warning(f"Could not perform MCP handshake for {normalized}: {e}")
        return None


def discover_mcp_tools(timeout: float = 5.0) -> str:
    """
    Returns a human-readable JSON summary of dynamically discovered tools
    from the connected FastMCP server.
    """
    tools = fetch_dynamic_mcp_schemas(force_refresh=True, timeout=timeout)
    return json.dumps({
        "mcp_server": REMOTE_MCP_URL,
        "status": "connected" if tools else "offline_or_empty",
        "discovered_tools_count": len(tools),
        "tools": [t["function"]["name"] for t in tools]
    }, indent=2)
