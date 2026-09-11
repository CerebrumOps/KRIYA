# ==============================================================================
# KRIYA Industrial Refinery Agent Tools
# ==============================================================================
# Wraps MRPL company database queries into callable agent tools.
# Allows the AI workbench to check telemetry, units, work orders, and SOPs.
# ==============================================================================

import asyncio
import json
from typing import Any, Dict, List, Optional

from backend.database.company.request.refinery_db import (
    search_sops,
    get_equipment_telemetry,
    get_unit_detail,
    list_work_orders
)


def _run_async(coro):
    """Helper to execute async DB queries within sync tool calls."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In an active event loop, run in a separate thread or use new event loop
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(lambda: asyncio.run(coro)).result()
        else:
            return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


def search_refinery_sops_tool(query: str) -> str:
    """Searches MRPL Standard Operating Procedures for safety, corrosion, and maintenance standards."""
    results = _run_async(search_sops(query))
    if not results:
        return f"[Knowledge Base]: No SOP matching '{query}' was found in MRPL records."
    return json.dumps(results, indent=2, default=str)


def query_refinery_telemetry_tool(equipment_id: str) -> str:
    """Queries live SCADA telemetry metrics (pressure, temp, vibration) for specified equipment."""
    metrics = _run_async(get_equipment_telemetry(equipment_id))
    if not metrics:
        return f"[Telemetry]: No active telemetry stream found for equipment '{equipment_id}'."
    return json.dumps(metrics, indent=2, default=str)


def inspect_refinery_unit_tool(unit_id: str) -> str:
    """Retrieves operational status, throughput percentage, and equipment list for an MRPL unit."""
    detail = _run_async(get_unit_detail(unit_id))
    if not detail:
        return f"[Unit Registry]: Unit '{unit_id}' not found in MRPL plant topology."
    return json.dumps(detail, indent=2, default=str)


def list_active_work_orders_tool(severity: Optional[str] = None) -> str:
    """Lists current maintenance tickets and open work orders."""
    orders = _run_async(list_work_orders(severity=severity))
    return json.dumps(orders, indent=2, default=str)


# ==============================================================================
# SCHEMAS FOR OPENAI REGISTRY
# ==============================================================================

SEARCH_SOPS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_refinery_sops",
        "description": "Searches MRPL refinery Standard Operating Procedures (SOPs) for corrosion criteria, vibration limits, safety rules, and overhaul requirements.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Keyword or topic to search (e.g. 'corrosion', 'vibration', 'CDU-II', 'flare')"}
            },
            "required": ["query"]
        }
    }
}

QUERY_TELEMETRY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "query_refinery_telemetry",
        "description": "Queries live SCADA/DCS telemetry (pressure, temperature, flow rate, vibration) for equipment tag (e.g. 'K-201', 'P-101A', 'C-101').",
        "parameters": {
            "type": "object",
            "properties": {
                "equipment_id": {"type": "string", "description": "Equipment identifier (e.g. 'K-201', 'C-101', 'P-101A')"}
            },
            "required": ["equipment_id"]
        }
    }
}

INSPECT_UNIT_SCHEMA = {
    "type": "function",
    "function": {
        "name": "inspect_refinery_unit",
        "description": "Returns operational throughput, operating mode, and installed machinery for a unit (e.g. 'CDU-II', 'FCCU', 'VDU').",
        "parameters": {
            "type": "object",
            "properties": {
                "unit_id": {"type": "string", "description": "Unit ID (e.g. 'CDU-II', 'FCCU', 'VDU')"}
            },
            "required": ["unit_id"]
        }
    }
}

LIST_WORK_ORDERS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_active_work_orders",
        "description": "Lists active maintenance tickets and work orders with findings, assigned department, and cost estimates.",
        "parameters": {
            "type": "object",
            "properties": {
                "severity": {"type": "string", "description": "Optional filter: 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'"}
            },
            "required": []
        }
    }
}
