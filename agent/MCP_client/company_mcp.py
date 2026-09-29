# ==============================================================================
# KRIYA MCP Client: Sovereign Company Database & Dynamic MCP Integration
# ==============================================================================
# Connects dynamically to the MRPL FastMCP Server running on the Raspberry Pi node.
# Zero hardcoded tool schemas: dynamically queries tools/list via JSON-RPC over SSE,
# transforms MCP schemas into OpenAI function calling format, and dispatches
# tools/call when requested by the model.
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

REMOTE_MCP_URL = os.getenv("REMOTE_MCP_URL", "http://100.127.46.50:8085")

# In-memory schema cache to prevent repeated SSE handshakes on every turn
_MCP_SCHEMA_CACHE: List[Dict[str, Any]] = []
_MCP_CACHE_TIMESTAMP: float = 0.0
_MCP_CACHE_TTL: float = 120.0  # 2 minutes TTL


def fetch_dynamic_mcp_schemas(force_refresh: bool = False, timeout: float = 5.0) -> List[Dict[str, Any]]:
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
        for _ in range(20):
            line = resp.readline().decode("utf-8")
            if line.startswith("data:"):
                msg = json.loads(line.replace("data: ", ""))
                if msg.get("id") == 2:
                    raw_tools = msg.get("result", {}).get("tools", [])
                    openai_tools = []
                    for t in raw_tools:
                        input_schema = t.get("inputSchema") or {}
                        properties = input_schema.get("properties", {})
                        required = input_schema.get("required", [])

                        openai_tools.append({
                            "type": "function",
                            "function": {
                                "name": t.get("name", ""),
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
                    return _MCP_SCHEMA_CACHE

    except Exception as e:
        logger.warning(f"Could not dynamically discover tools from FastMCP at {REMOTE_MCP_URL}: {e}")
        # Return stale cache if available
        if _MCP_SCHEMA_CACHE:
            return _MCP_SCHEMA_CACHE

    return []


def call_fastmcp_tool(tool_name: str, arguments: Optional[Dict[str, Any]] = None, timeout: float = 6.0) -> str:
    """
    Executes any dynamically discovered tool on the remote FastMCP server using JSON-RPC over SSE.
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
        while True:
            line = resp.readline().decode("utf-8")
            if line.startswith("data:"):
                msg_data = json.loads(line.replace("data: ", ""))
                if msg_data.get("id") == 2:
                    res = msg_data.get("result", {})
                    content = res.get("content", [])
                    if content and isinstance(content, list):
                        return content[0].get("text", json.dumps(res, indent=2))
                    return json.dumps(res, indent=2)

    except Exception as e:
        return f"[Error executing MCP tool '{tool_name}' on server {REMOTE_MCP_URL}]: {str(e)}"


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
        "tools": tools
    }, indent=2)


# ==============================================================================
# REST ADAPTER HELPERS (SCADA TELEMETRY & PLANT STATUS)
# ==============================================================================

def fetch_rest_mcp(endpoint: str, params: Optional[Dict[str, str]] = None) -> Optional[Dict[str, Any]]:
    """Makes a lightweight HTTP GET request to the MCP server's REST adapter."""
    try:
        base_url = REMOTE_MCP_URL.rstrip("/")
        query_str = f"?{urllib.parse.urlencode(params)}" if params else ""
        req = urllib.request.Request(f"{base_url}{endpoint}{query_str}", headers={"User-Agent": "KRIYA-Agent"})
        with urllib.request.urlopen(req, timeout=4) as resp:
            if resp.status == 200:
                return json.loads(resp.read().decode("utf-8"))
    except Exception:
        return None
    return None


def get_live_mcp_telemetry(unit_tag: str, **kwargs) -> str:
    """Queries live telemetry and active integrity alarms from the MCP server REST endpoint."""
    data = fetch_rest_mcp("/api/telemetry", {"unit": unit_tag})
    if data and "telemetry" in data:
        return json.dumps({
            "source": f"Sovereign FastMCP Server ({REMOTE_MCP_URL})",
            "telemetry": data["telemetry"]
        }, indent=2)
    return f"[Notice]: FastMCP telemetry appliance at {REMOTE_MCP_URL} is unreachable."


def get_all_mcp_units_status(**kwargs) -> str:
    """Queries plant-wide health scores and active alarms from the FastMCP server REST endpoint."""
    data = fetch_rest_mcp("/api/units")
    if data and "units" in data:
        return json.dumps({
            "source": f"Sovereign FastMCP Server ({REMOTE_MCP_URL})",
            "data": data
        }, indent=2)
    return f"[Notice]: FastMCP appliance at {REMOTE_MCP_URL} is unreachable."
