# ==============================================================================
# KRIYA Industrial Database Request Logic: MRPL Operations & SOPs
# ==============================================================================
# Handles queries and data persistence for:
# - Refinery Units (CDU, VDU, FCCU, HCU)
# - Equipment Inventory & Tagged Sensors
# - Real-time SCADA / DCS Telemetry mirrors
# - Standard Operating Procedures (SOPs)
# - Maintenance Work Orders
# ==============================================================================

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncpg
from dotenv import load_dotenv

from backend.database.company.schema.refinery_units import CREATE_REFINERY_TABLES_SQL

env_path = Path(__file__).resolve().parent.parent.parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

DATABASE_URL = os.getenv("DATABASE_URL")
_pool: Optional[asyncpg.Pool] = None


async def get_db_pool() -> asyncpg.Pool:
    """Returns or creates the global asyncpg connection pool bound to current event loop."""
    global _pool
    current_loop = asyncio.get_running_loop()
    if _pool is None or getattr(_pool, "_loop", None) != current_loop or getattr(_pool, "_closed", False):
        load_dotenv(dotenv_path=env_path, override=True)
        db_url = os.getenv("DATABASE_URL", DATABASE_URL)
        _pool = await asyncpg.create_pool(db_url, min_size=1, max_size=10)
        await init_refinery_db(_pool)
    return _pool


# Seed Data for MRPL
SEED_REFINERY_UNITS = [
    {
        "unit_id": "CDU-I",
        "unit_name": "Crude Distillation Unit I",
        "capacity_mmtpa": 4.50,
        "current_throughput_pct": 94.20,
        "status": "OPERATIONAL",
        "description": "Primary crude fractionator separating heavy Arab/Basrah crudes into LPG, Naphtha, Kerosene, and Residue."
    },
    {
        "unit_id": "CDU-II",
        "unit_name": "Crude Distillation Unit II",
        "capacity_mmtpa": 6.00,
        "current_throughput_pct": 98.10,
        "status": "OPERATIONAL",
        "description": "High-capacity modern crude atmospheric distillation train with pre-flash column."
    },
    {
        "unit_id": "VDU",
        "unit_name": "Vacuum Distillation Unit",
        "capacity_mmtpa": 3.20,
        "current_throughput_pct": 91.50,
        "status": "OPERATIONAL",
        "description": "Processes atmospheric residue under 25 mmHg absolute pressure to produce Heavy Vacuum Gas Oil (HVGO)."
    },
    {
        "unit_id": "FCCU",
        "unit_name": "Fluidised Catalytic Cracking Unit",
        "capacity_mmtpa": 2.20,
        "current_throughput_pct": 95.00,
        "status": "OPERATIONAL",
        "description": "Converts heavy gas oils into high-octane motor gasoline and LPG using zeolitic catalyst."
    },
    {
        "unit_id": "HCU",
        "unit_name": "Hydrocracker Unit",
        "capacity_mmtpa": 1.80,
        "current_throughput_pct": 89.40,
        "status": "OPERATIONAL",
        "description": "High-pressure catalytic cracking in hydrogen atmosphere for superior ultra-low sulfur diesel production."
    },
    {
        "unit_id": "HGU",
        "unit_name": "Hydrogen Generation Unit",
        "capacity_mmtpa": 0.07,
        "current_throughput_pct": 96.30,
        "status": "OPERATIONAL",
        "description": "Steam methane reforming unit producing 99.9% pure hydrogen for hydrocracking operations."
    }
]

SEED_EQUIPMENT = [
    {
        "equipment_id": "P-101A",
        "unit_id": "CDU-II",
        "tag_name": "Crude Charge Pump A",
        "equipment_type": "Pump",
        "design_spec": "Centrifugal multi-stage, 520 m3/hr, 28 bar, 450 kW drive",
        "operating_status": "RUNNING",
        "criticality": "CRITICAL"
    },
    {
        "equipment_id": "P-101B",
        "unit_id": "CDU-II",
        "tag_name": "Crude Charge Pump B (Standby)",
        "equipment_type": "Pump",
        "design_spec": "Centrifugal multi-stage standby, auto-start on low header pressure",
        "operating_status": "STANDBY",
        "criticality": "HIGH"
    },
    {
        "equipment_id": "C-101",
        "unit_id": "CDU-II",
        "tag_name": "Atmospheric Distillation Main Fractionator",
        "equipment_type": "Column",
        "design_spec": "Carbon steel with 316L clad upper sections, 48 sieve trays, height 54m, dia 6.2m",
        "operating_status": "RUNNING",
        "criticality": "CRITICAL"
    },
    {
        "equipment_id": "K-201",
        "unit_id": "FCCU",
        "tag_name": "Wet Gas Compressor",
        "equipment_type": "Compressor",
        "design_spec": "Two-stage centrifugal compressor driven by condensing steam turbine (7.2 MW)",
        "operating_status": "ALERT",
        "criticality": "CRITICAL"
    },
    {
        "equipment_id": "E-101",
        "unit_id": "CDU-II",
        "tag_name": "Crude / Residue Heat Exchanger Train",
        "equipment_type": "Exchanger",
        "design_spec": "Shell and tube (AES), surface area 1450 m2, tubes 3/4in Monel 400",
        "operating_status": "RUNNING",
        "criticality": "MEDIUM"
    },
    {
        "equipment_id": "XV-102",
        "unit_id": "CDU-II",
        "tag_name": "Emergency Depressuring Valve (ESD-1)",
        "equipment_type": "Valve",
        "design_spec": "Pneumatic ball valve, SIL-3 certified, fail-open to flare header",
        "operating_status": "RUNNING",
        "criticality": "CRITICAL"
    }
]

SEED_TELEMETRY = [
    {"equipment_id": "P-101A", "metric_name": "Discharge Pressure", "current_value": 27.4, "unit_of_measure": "kg/cm2g", "min_threshold": 24.0, "max_threshold": 30.0, "alert_state": "NORMAL"},
    {"equipment_id": "P-101A", "metric_name": "Flow Rate", "current_value": 482.5, "unit_of_measure": "m3/hr", "min_threshold": 400.0, "max_threshold": 530.0, "alert_state": "NORMAL"},
    {"equipment_id": "P-101A", "metric_name": "Bearing Temperature", "current_value": 68.2, "unit_of_measure": "degC", "min_threshold": 40.0, "max_threshold": 85.0, "alert_state": "NORMAL"},
    {"equipment_id": "C-101", "metric_name": "Overhead Pressure", "current_value": 2.45, "unit_of_measure": "kg/cm2g", "min_threshold": 2.10, "max_threshold": 2.70, "alert_state": "NORMAL"},
    {"equipment_id": "C-101", "metric_name": "Bottom Tray Temperature", "current_value": 348.6, "unit_of_measure": "degC", "min_threshold": 335.0, "max_threshold": 360.0, "alert_state": "NORMAL"},
    {"equipment_id": "C-101", "metric_name": "Differential Pressure (Tray 1-48)", "current_value": 0.42, "unit_of_measure": "kg/cm2g", "min_threshold": 0.25, "max_threshold": 0.65, "alert_state": "NORMAL"},
    {"equipment_id": "K-201", "metric_name": "Vibration Drive-End (X-Axis)", "current_value": 4.82, "unit_of_measure": "mm/s", "min_threshold": 0.5, "max_threshold": 4.5, "alert_state": "WARNING"},
    {"equipment_id": "K-201", "metric_name": "Lube Oil Supply Pressure", "current_value": 1.78, "unit_of_measure": "kg/cm2g", "min_threshold": 1.5, "max_threshold": 2.5, "alert_state": "NORMAL"},
    {"equipment_id": "K-201", "metric_name": "Discharge Gas Temperature", "current_value": 118.4, "unit_of_measure": "degC", "min_threshold": 80.0, "max_threshold": 130.0, "alert_state": "NORMAL"}
]

SEED_SOPS = [
    {
        "sop_id": "SOP-MRPL-4.2.3",
        "title": "Atmospheric Column Overhead Corrosion & Ultrasonic Inspection Standard",
        "unit_id": "CDU-II",
        "category": "Inspection",
        "version": "v4.2.3",
        "content": (
            "1. Objective: Standardized protocol for detecting naphthenic acid and ammonium chloride corrosion "
            "in CDU overhead piping and condenser bundles.\n"
            "2. Corrosion Allowance: Minimum permissible wall thickness is 6.5 mm. Thickness below 6.0 mm mandates "
            "immediate derating or emergency bypass.\n"
            "3. Visual Indicators: Any visible salt deposition, green/brown ferric deposits, or weeping flanges "
            "must be flagged as Category-A defect.\n"
            "4. Corrective Action: Neutralizing amine injection rate must be recalibrated to maintain overhead boot "
            "water pH strictly between 5.8 and 6.8.\n"
            "5. Documentation: Engineering approval note required within 24 hours of inspection with ultrasonic "
            "evidence grid attachment."
        ),
        "summary": "Mandates 6.5mm minimum wall thickness and strict pH control (5.8-6.8) for CDU overhead systems with 24h approval note.",
        "key_clauses": [
            "Min wall thickness: 6.5 mm",
            "pH buffer requirement: 5.8 to 6.8",
            "Approval note turnaround: 24 hours",
            "Mandatory Category-A defect flag for visible weeping"
        ]
    },
    {
        "sop_id": "SOP-MRPL-7.1.1",
        "title": "Centrifugal & Wet Gas Compressor Vibration Monitoring & Overhaul Criteria",
        "unit_id": "FCCU",
        "category": "Maintenance",
        "version": "v3.1.0",
        "content": (
            "1. Permissible Vibration Limits: Continuous overall vibration for K-201 shall not exceed 4.5 mm/s RMS.\n"
            "2. Warning Action: If vibration exceeds 4.5 mm/s but remains below 7.1 mm/s, initiate 4-hour monitoring interval, "
            "perform lube oil spectral analysis, and inspect seal gas differential pressure.\n"
            "3. Trip Protection: Vibration reaching 7.1 mm/s mandates manual/automatic unit trip.\n"
            "4. Repair Procedure: Rotor rebalancing, dynamic alignment verification, and bearing replacement protocol."
        ),
        "summary": "Compressor vibration limits: normal <4.5 mm/s, warning 4.5-7.1 mm/s with 4-hour spectral checks, trip at 7.1 mm/s.",
        "key_clauses": [
            "Warning threshold: 4.5 mm/s RMS",
            "Trip threshold: 7.1 mm/s RMS",
            "Action: 4-hour spectral monitoring & lube oil sampling"
        ]
    },
    {
        "sop_id": "SOP-MRPL-3.0.5",
        "title": "Emergency Depressuring and Flare Isolation Interlocks",
        "unit_id": "CDU-II",
        "category": "Safety",
        "version": "v5.0.1",
        "content": (
            "1. Activation Criteria: Overpressure event exceeding 110% of design pressure (3.1 kg/cm2g).\n"
            "2. Valve Isolation: Automatic actuation of XV-102 venting 80% column inventory to low-pressure flare in 15 minutes.\n"
            "3. Human Review: Manual override requires Chief Operations Superintendent dual-key authentication."
        ),
        "summary": "Protocol for emergency column depressurization via XV-102 to flare header with dual-key override.",
        "key_clauses": [
            "Activation: Overpressure > 3.1 kg/cm2g",
            "Target: 80% depressurization in 15 minutes",
            "Dual-key authorization for manual override"
        ]
    }
]

SEED_WORK_ORDERS = [
    {
        "order_id": "WO-MRPL-2026-0891",
        "equipment_id": "K-201",
        "title": "K-201 Compressor Drive-End High Vibration Investigation",
        "severity": "HIGH",
        "status": "IN_PROGRESS",
        "assigned_department": "Rotary Equipment Maintenance",
        "findings_summary": "Vibration sensor detected 4.82 mm/s RMS exceeding 4.5 mm/s SOP limit. Suspected lube oil degradation or coupling misalignment.",
        "sop_reference": "SOP-MRPL-7.1.1",
        "estimated_cost_inr": 285000.00
    },
    {
        "order_id": "WO-MRPL-2026-0892",
        "equipment_id": "C-101",
        "title": "CDU-II Fractionator Overhead Nozzle Ultrasonic Thickness Survey",
        "severity": "CRITICAL",
        "status": "PENDING_APPROVAL",
        "assigned_department": "Plant Inspection & Integrity Wing",
        "findings_summary": "Scanned inspection report shows wall thickness degradation down to 6.1 mm on Tray 44 nozzle with salt weeping.",
        "sop_reference": "SOP-MRPL-4.2.3",
        "estimated_cost_inr": 640000.00
    },
    {
        "order_id": "WO-MRPL-2026-0893",
        "equipment_id": "P-101B",
        "title": "Standby Charge Pump Mechanical Seal Replacement & Hydrotest",
        "severity": "MEDIUM",
        "status": "OPEN",
        "assigned_department": "Rotary Equipment Maintenance",
        "findings_summary": "Preventative overhaul prior to heavy crude campaign. Seal barrier fluid inspection.",
        "sop_reference": "SOP-MRPL-5.1.0",
        "estimated_cost_inr": 120000.00
    }
]


async def init_refinery_db(pool: asyncpg.Pool) -> None:
    """Initializes tables and seeds default refinery records if empty."""
    async with pool.acquire() as conn:
        await conn.execute(CREATE_REFINERY_TABLES_SQL)

        # Check existing units
        count = await conn.fetchval("SELECT count(*) FROM refinery_units")
        if count == 0:
            for u in SEED_REFINERY_UNITS:
                await conn.execute(
                    """
                    INSERT INTO refinery_units (unit_id, unit_name, capacity_mmtpa, current_throughput_pct, status, description)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    ON CONFLICT (unit_id) DO NOTHING
                    """,
                    u["unit_id"], u["unit_name"], u["capacity_mmtpa"], u["current_throughput_pct"], u["status"], u["description"]
                )

            for eq in SEED_EQUIPMENT:
                await conn.execute(
                    """
                    INSERT INTO equipment_inventory (equipment_id, unit_id, tag_name, equipment_type, design_spec, operating_status, criticality, last_inspected_at)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, NOW())
                    ON CONFLICT (equipment_id) DO NOTHING
                    """,
                    eq["equipment_id"], eq["unit_id"], eq["tag_name"], eq["equipment_type"], eq["design_spec"], eq["operating_status"], eq["criticality"]
                )

            for t in SEED_TELEMETRY:
                await conn.execute(
                    """
                    INSERT INTO equipment_telemetry (equipment_id, metric_name, current_value, unit_of_measure, min_threshold, max_threshold, alert_state)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """,
                    t["equipment_id"], t["metric_name"], t["current_value"], t["unit_of_measure"], t["min_threshold"], t["max_threshold"], t["alert_state"]
                )

            for s in SEED_SOPS:
                await conn.execute(
                    """
                    INSERT INTO refinery_sops (sop_id, title, unit_id, category, version, content, summary, key_clauses)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8::jsonb)
                    ON CONFLICT (sop_id) DO NOTHING
                    """,
                    s["sop_id"], s["title"], s["unit_id"], s["category"], s["version"], s["content"], s["summary"], json.dumps(s["key_clauses"])
                )

            for wo in SEED_WORK_ORDERS:
                await conn.execute(
                    """
                    INSERT INTO work_orders (order_id, equipment_id, title, severity, status, assigned_department, findings_summary, sop_reference, estimated_cost_inr)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                    ON CONFLICT (order_id) DO NOTHING
                    """,
                    wo["order_id"], wo["equipment_id"], wo["title"], wo["severity"], wo["status"], wo["assigned_department"], wo["findings_summary"], wo["sop_reference"], wo["estimated_cost_inr"]
                )


# ==============================================================================
# QUERY FUNCTIONS
# ==============================================================================

async def list_refinery_units() -> List[Dict[str, Any]]:
    """Lists all operational refinery units at MRPL."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM refinery_units ORDER BY capacity_mmtpa DESC")
    return [dict(r) for r in rows]


async def get_unit_detail(unit_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves unit information along with associated equipment inventory."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        unit = await conn.fetchrow("SELECT * FROM refinery_units WHERE unit_id = $1", unit_id.strip())
        if not unit:
            return None
        eqs = await conn.fetch("SELECT * FROM equipment_inventory WHERE unit_id = $1", unit_id.strip())

    res = dict(unit)
    res["equipment"] = [dict(e) for e in eqs]
    return res


async def list_equipment(unit_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists refinery equipment with optional unit filtering."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        if unit_id:
            rows = await conn.fetch("SELECT * FROM equipment_inventory WHERE unit_id = $1", unit_id.strip())
        else:
            rows = await conn.fetch("SELECT * FROM equipment_inventory ORDER BY criticality ASC, tag_name ASC")
    return [dict(r) for r in rows]


async def get_equipment_telemetry(equipment_id: str) -> List[Dict[str, Any]]:
    """Returns live sensor telemetry readings for an equipment piece."""
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT metric_name, current_value, unit_of_measure, min_threshold, max_threshold, alert_state, recorded_at
            FROM equipment_telemetry
            WHERE equipment_id = $1
            ORDER BY recorded_at DESC
            """,
            equipment_id.strip()
        )
    return [dict(r) for r in rows]


async def search_sops(query: str) -> List[Dict[str, Any]]:
    """Performs full-text/keyword search across MRPL standard operating procedures."""
    pool = await get_db_pool()
    q = f"%{query.strip().lower()}%"
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT sop_id, title, unit_id, category, version, summary, key_clauses, content
            FROM refinery_sops
            WHERE LOWER(title) LIKE $1 OR LOWER(content) LIKE $1 OR LOWER(sop_id) LIKE $1
            ORDER BY sop_id ASC
            """,
            q
        )

    results = []
    for r in rows:
        d = dict(r)
        if isinstance(d["key_clauses"], str):
            try:
                d["key_clauses"] = json.loads(d["key_clauses"])
            except Exception:
                d["key_clauses"] = []
        results.append(d)
    return results


async def list_work_orders(severity: Optional[str] = None, status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Lists maintenance work orders with optional status or severity filters."""
    pool = await get_db_pool()
    query = "SELECT * FROM work_orders WHERE 1=1"
    params = []

    if severity:
        params.append(severity.upper())
        query += f" AND severity = ${len(params)}"
    if status:
        params.append(status.upper())
        query += f" AND status = ${len(params)}"

    query += " ORDER BY created_at DESC"

    async with pool.acquire() as conn:
        rows = await conn.fetch(query, *params)
    return [dict(r) for r in rows]
