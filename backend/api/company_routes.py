# ==============================================================================
# KRIYA Industrial Operations & Refinery REST API
# ==============================================================================
# Exposes operational data from Mangalore Refinery and Petrochemicals Limited:
# - Units (CDU, VDU, FCCU, HCU, HGU)
# - Equipment inventory & status
# - Real-time SCADA telemetry
# - Standard Operating Procedures (SOPs)
# - Work orders & maintenance logs
# ==============================================================================

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from backend.database.company.request.refinery_db import (
    list_refinery_units,
    get_unit_detail,
    list_equipment,
    get_equipment_telemetry,
    search_sops,
    list_work_orders
)

router = APIRouter(prefix="/api/company", tags=["Industrial Refinery Operations"])


@router.get("/units")
async def api_list_units():
    """Returns all operational units in MRPL complex."""
    units = await list_refinery_units()
    return {"units": units, "total": len(units)}


@router.get("/units/{unit_id}")
async def api_get_unit(unit_id: str):
    """Returns detailed unit parameters and installed equipment."""
    data = await get_unit_detail(unit_id)
    if not data:
        raise HTTPException(status_code=404, detail=f"Unit '{unit_id}' not found.")
    return data


@router.get("/equipment")
async def api_list_equipment(unit_id: Optional[str] = Query(None)):
    """Returns equipment inventory with optional unit filtering."""
    eqs = await list_equipment(unit_id)
    return {"equipment": eqs, "total": len(eqs)}


@router.get("/equipment/{equipment_id}/telemetry")
async def api_get_equipment_telemetry(equipment_id: str):
    """Returns live SCADA / DCS telemetry readings for specified equipment."""
    metrics = await get_equipment_telemetry(equipment_id)
    return {
        "equipmentId": equipment_id,
        "telemetry": metrics,
        "count": len(metrics)
    }


@router.get("/sops/search")
async def api_search_sops(query: str = Query(..., min_length=1)):
    """Performs knowledge base search across MRPL operating standards & SOPs."""
    results = await search_sops(query)
    return {
        "query": query,
        "results": results,
        "totalMatches": len(results)
    }


@router.get("/work-orders")
async def api_list_work_orders(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """Lists maintenance work orders with optional severity and status filters."""
    orders = await list_work_orders(severity, status)
    return {"workOrders": orders, "total": len(orders)}
