# ==============================================================================
# KRIYA Industrial Database Schema: MRPL Refinery Units, Equipment & SOPs
# ==============================================================================
# Defines the PostgreSQL tables and Pydantic schemas for Mangalore Refinery &
# Petrochemicals Limited (MRPL) sovereign operations, SCADA telemetry, and maintenance.
# ==============================================================================

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


CREATE_REFINERY_TABLES_SQL = """
-- 1. Refinery Units Table
CREATE TABLE IF NOT EXISTS refinery_units (
    unit_id VARCHAR(32) PRIMARY KEY,
    unit_name VARCHAR(128) NOT NULL,
    capacity_mmtpa NUMERIC(5, 2) NOT NULL,
    current_throughput_pct NUMERIC(5, 2) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'OPERATIONAL',
    description TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 2. Equipment Inventory Table
CREATE TABLE IF NOT EXISTS equipment_inventory (
    equipment_id VARCHAR(32) PRIMARY KEY,
    unit_id VARCHAR(32) NOT NULL REFERENCES refinery_units(unit_id) ON DELETE CASCADE,
    tag_name VARCHAR(64) NOT NULL,
    equipment_type VARCHAR(64) NOT NULL, -- 'Pump', 'Compressor', 'Column', 'Exchanger', 'Valve'
    design_spec TEXT,
    operating_status VARCHAR(32) NOT NULL DEFAULT 'RUNNING', -- 'RUNNING', 'STANDBY', 'MAINTENANCE', 'ALERT'
    criticality VARCHAR(16) NOT NULL DEFAULT 'HIGH', -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    installation_date DATE,
    last_inspected_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 3. Live Equipment Telemetry (SCADA / DCS mirror)
CREATE TABLE IF NOT EXISTS equipment_telemetry (
    id SERIAL PRIMARY KEY,
    equipment_id VARCHAR(32) NOT NULL REFERENCES equipment_inventory(equipment_id) ON DELETE CASCADE,
    metric_name VARCHAR(64) NOT NULL, -- e.g. 'Pressure', 'Temperature', 'Flow_Rate', 'Vibration'
    current_value NUMERIC(10, 3) NOT NULL,
    unit_of_measure VARCHAR(32) NOT NULL, -- 'kg/cm2g', 'degC', 'm3/hr', 'mm/s'
    min_threshold NUMERIC(10, 3),
    max_threshold NUMERIC(10, 3),
    alert_state VARCHAR(16) NOT NULL DEFAULT 'NORMAL', -- 'NORMAL', 'WARNING', 'CRITICAL'
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_telemetry_eq ON equipment_telemetry (equipment_id, recorded_at DESC);

-- 4. Standard Operating Procedures (SOPs) Knowledge Base
CREATE TABLE IF NOT EXISTS refinery_sops (
    sop_id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    unit_id VARCHAR(32) REFERENCES refinery_units(unit_id),
    category VARCHAR(64) NOT NULL, -- 'Inspection', 'Safety', 'Maintenance', 'Emergency'
    version VARCHAR(16) NOT NULL DEFAULT 'v4.2',
    content TEXT NOT NULL,
    summary TEXT,
    key_clauses JSONB DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 5. Maintenance Work Orders Table
CREATE TABLE IF NOT EXISTS work_orders (
    order_id VARCHAR(64) PRIMARY KEY,
    equipment_id VARCHAR(32) NOT NULL REFERENCES equipment_inventory(equipment_id),
    title VARCHAR(255) NOT NULL,
    severity VARCHAR(16) NOT NULL DEFAULT 'MEDIUM', -- 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'
    status VARCHAR(32) NOT NULL DEFAULT 'OPEN', -- 'OPEN', 'IN_PROGRESS', 'PENDING_APPROVAL', 'CLOSED'
    assigned_department VARCHAR(128) NOT NULL,
    findings_summary TEXT,
    sop_reference VARCHAR(64),
    estimated_cost_inr NUMERIC(12, 2) DEFAULT 0.00,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


# Pydantic Schemas
class RefineryUnitModel(BaseModel):
    unit_id: str
    unit_name: str
    capacity_mmtpa: float
    current_throughput_pct: float
    status: str
    description: Optional[str] = None


class EquipmentModel(BaseModel):
    equipment_id: str
    unit_id: str
    tag_name: str
    equipment_type: str
    design_spec: Optional[str] = None
    operating_status: str
    criticality: str
    last_inspected_at: Optional[datetime] = None


class TelemetryModel(BaseModel):
    equipment_id: str
    metric_name: str
    current_value: float
    unit_of_measure: str
    min_threshold: Optional[float] = None
    max_threshold: Optional[float] = None
    alert_state: str


class SOPModel(BaseModel):
    sop_id: str
    title: str
    unit_id: Optional[str] = None
    category: str
    version: str
    content: str
    summary: Optional[str] = None
    key_clauses: List[str] = Field(default_factory=list)


class WorkOrderModel(BaseModel):
    order_id: str
    equipment_id: str
    title: str
    severity: str
    status: str
    assigned_department: str
    findings_summary: Optional[str] = None
    sop_reference: Optional[str] = None
    estimated_cost_inr: float = 0.00
