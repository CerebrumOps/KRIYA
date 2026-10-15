# 🛡️ SIH_mcp: Sovereign Air-Gapped MCP Gateway
## Complete Architectural, Handshake Protocol & API Reference Guide
**Company:** Coastal Refinery & Petrochemicals Ltd (CRPL)  
**Target Appliance:** Raspberry Pi 5 (`100.127.46.50:5432`)  
**Protocol:** Model Context Protocol (MCP) by Anthropic  

---

## Table of Contents
1. [System Architecture & Air-Gap Topology](#1-system-architecture--air-gap-topology)
2. [Employee Designation Handshake Protocol](#2-employee-designation-handshake-protocol)
3. [Clearance Tiers & Authorization Matrix](#3-clearance-tiers--authorization-matrix)
4. [Complete MCP Tool Catalog & API Reference](#4-complete-mcp-tool-catalog--api-reference)
5. [How to Run & Deploy (`run_mcp.sh`)](#5-how-to-run--deploy-run_mcpsh)
6. [Client Integration (Claude Desktop, Cursor, Custom Agents)](#6-client-integration)
7. [Hackathon Demo Walkthrough Scenarios](#7-hackathon-demo-walkthrough-scenarios)
8. [Security & Read-Only Guarantees](#8-security--read-only-guarantees)

---

## 1. System Architecture & Air-Gap Topology

The **`SIH_mcp`** gateway acts as an air-gapped sovereign bridge between autonomous AI Agents (such as KRIYA) and the internal enterprise refinery database (`company_db`).

```
┌────────────────────────────────────────────────────────────────────────┐
│                        AI AGENT LAYER (KRIYA)                          │
│               [Reasoning LLM / Orchestrator / UI Workbench]            │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Model Context Protocol
                                    │ (JSON-RPC over SSE / stdio)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       SIH_mcp GATEWAY SERVER                           │
│                     (FastMCP on Raspberry Pi 5)                        │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │           Session & Employee Handshake Authenticator           │   │
│   │     (Resolves Designation, Role, Department & Clearance 1-4)    │   │
│   └───────────────────────────────┬────────────────────────────────┘   │
│                                   │                                    │
│   ┌───────────────────────────────▼────────────────────────────────┐   │
│   │            Role-Based Access Control (RBAC) Gatekeeper         │   │
│   │   • Level 1: Public / Telemetry / Unit Baselines               │   │
│   │   • Level 2: Engineering Specs / CML Thickness / Inspection    │   │
│   │   • Level 3: Department Budgets / Rate Contracts / MOC         │   │
│   │   • Level 4: Confidential Bids / Capex Proposals / Executive   │   │
│   └───────────────────────────────┬────────────────────────────────┘   │
└───────────────────────────────────┼────────────────────────────────────┘
                                    │ Hardware Read-Only SQL Connection
                                    │ Role: kriya_ro (read_only = ON)
                                    ▼
┌────────────────────────────────────────────────────────────────────────┐
│               INTERNAL STORAGE LAYER [Safe Read Access Only]           │
│                                                                        │
│   ┌────────────────────────────────┐  ┌────────────────────────────┐   │
│   │   PostgreSQL 17 (company_db)   │  │   Physical Blob Storage    │   │
│   │   Schema: corp (28 tables)     │  │   (/company_storage/blob)  │   │
│   │   • Equipment & Line Register  │  │   • P&ID SVGs & Drawings   │   │
│   │   • CML Thickness Readings     │  │   • Scanned Inspection PDFs│   │
│   │   • 30k+ Time-Series Telemetry │  │   • Handwritten Shift Logs │   │
│   │   • Budgets, Bids & DOA Matrix │  │   • SOPs & Buggy Scripts   │   │
│   └────────────────────────────────┘  └────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Architectural Tenets:
1. **Air-Gapped Read-Only:** All queries run as PostgreSQL user `kriya_ro` with `SET default_transaction_read_only = on` and statement timeout of 10s. Even if an AI agent is prompt-injected, the database engine physically rejects any `INSERT`, `UPDATE`, `DELETE`, or `DROP`.
2. **Designation Handshake:** An AI agent cannot access classified inspection dossiers or commercial vendor bids without first performing a handshake identifying the employee context.
3. **Zero Data Leakage:** When an employee of Level 2 or 3 searches documents or asks for commercial bids, sensitive records are automatically filtered out or returned with structured access-denied responses.

---

## 2. Employee Designation Handshake Protocol

### Handshake Lifecycle:
1. **Initial State (Guest / Level 1):**
   Before authentication, any agent connection defaults to **Level 1 (Guest / Public Operator)**. It can look up basic refinery units and live sensor telemetry, but cannot read inspection thickness histories, commercial contracts, or departmental finances.
2. **Handshake Invocation (`handshake_authenticate`):**
   The agent calls `handshake_authenticate(emp_code="EMP-1008")`.
3. **Database Identity Resolution:**
   The gateway queries `corp.employees` joined with `corp.roles`, `corp.departments`, and `corp.delegation_of_authority`:
   - Validates that the employee is `Active`.
   - Computes effective clearance: `MAX(employee.clearance_level, role.clearance_level)`.
   - Resolves financial DOA spending limits.
4. **Session Token & Context Established:**
   The active session profile is stored in memory and returned to the client with permitted domain scopes.

---

## 3. Clearance Tiers & Authorization Matrix

CRPL defines 10 designations mapped across 4 clearance tiers:

| Tier | Role Code | Designation / Title | Sample Employees | Permitted Data Scopes |
| :---: | :---: | :--- | :--- | :--- |
| **Level 1** | `TECH` | Senior Technician / Board Operator / Guest | `EMP-1025` (Mahesh Prabhu)<br>`GUEST-001` (Unauthenticated) | Operational units, equipment basic tags, telemetry sensor streams, ISA standards, public SOPs |
| **Level 2** | `ENG`<br>`LEAD_ENG`<br>`MGR`<br>`SM` | Plant Engineer<br>Lead Plant Engineer<br>Area Manager<br>Inspection Lead / Senior Manager | `EMP-1008` (Arun V. Rao - Inspector)<br>`EMP-1010` (Priya Patel - Lead Eng)<br>`EMP-1007` (Suresh Menon - Lead) | All Level 1 + Equipment engineering specs, CML ultrasonic thickness readings, inspection dossiers, work orders, P&ID line lists, PTWs, Level 1–2 docs |
| **Level 3** | `AGM`<br>`DGM`<br>`AUDIT` | Chief Manager / AGM<br>Deputy General Manager<br>Internal Vigilance Officer | `EMP-1005` (Rajesh Sharma - AGM Maint)<br>`EMP-1004` (Deepak Hegde - DGM)<br>`EMP-1018` (Tanvi Mahajan - Auditor) | All Level 1–2 + Department maintenance budgets, vendor rate contracts, HSE incident investigations, MOC authorizations, DOA matrix, Level 3 docs |
| **Level 4** | `GM`<br>`DIR` | General Manager<br>Director (Refinery Operations) | `EMP-1002` (K. V. Ramanathan - GM O&M)<br>`EMP-1003` (Sunita Deshpande - GM Fin)<br>`EMP-1001` (Dr. Arvind Swaminathan) | **Full Sovereign Access:** Confidential vendor tender bids (`corp.bids`), Board CAPEX modernization proposals, executive correspondence, Level 4 docs |

---

## 4. Complete MCP Tool Catalog & API Reference

### Group 1: Handshake & Identity Management

#### 1. `handshake_authenticate`
- **Description:** Authenticates an employee by code and establishes active session context.
- **Parameters:** `emp_code: str` (e.g., `"EMP-1008"`)
- **Required Clearance:** None (Open Handshake)
- **Sample Output:**
```json
{
  "status": "AUTHENTICATED",
  "message": "Handshake successful! Welcome, Arun V. Rao (Plant / Inspection Engineer).",
  "profile": {
    "emp_code": "EMP-1008",
    "name": "Arun V. Rao",
    "email": "arun.rao@coastalrefinery.in",
    "role_code": "ENG",
    "role_name": "Plant / Inspection Engineer",
    "dept_code": "INSP",
    "dept_name": "Inspection & Asset Reliability",
    "clearance_level": 2,
    "clearance_description": "Level 2: Plant / Inspection Engineer",
    "doa_spending_limit_inr": 25000.0,
    "permitted_domains": ["units", "equipment_summary", "telemetry", "standards", "equipment_design_specs", "thickness_cml", "inspection_reports", "work_orders", "line_list", "ptw", "documents_lvl_2"]
  }
}
```

#### 2. `get_current_session`
- **Description:** Reports the active authenticated employee profile and clearance tier.
- **Parameters:** None
- **Required Clearance:** None

#### 3. `list_employees_for_auth`
- **Description:** Lists employees, designations, and clearance tiers for selecting demo personas.
- **Parameters:** `dept_code: Optional[str]` (e.g., `"MAINT"`, `"INSP"`, `"EXEC"`)
- **Required Clearance:** None

#### 4. `logout_session`
- **Description:** Resets the session back to Level 1 Guest profile.
- **Parameters:** None
- **Required Clearance:** None

---

### Group 2: Plant Assets & Telemetry (Level 1+)

#### 5. `get_refinery_units`
- **Description:** Returns all 6 operational units and capacities.
- **Parameters:** None
- **Required Clearance:** Level 1+

#### 6. `get_equipment`
- **Description:** Returns design pressure, design temperature, metallurgy, nominal thickness ($t_{nom}$), and minimum allowable thickness ($t_{min}$) for an equipment item.
- **Parameters:** `tag: str` (e.g., `"10-E-101"`)
- **Required Clearance:** Level 1+
- **Sample Output:**
```json
{
  "equipment_id": 1,
  "tag": "10-E-101",
  "unit_code": "UNIT-10",
  "name": "Crude Pre-heat Train Heat Exchanger A",
  "equipment_type": "Heat Exchanger (AES)",
  "service": "Crude Oil (Tube) / Atmospheric Residue (Shell)",
  "design_pressure_bar": 25.5,
  "design_temp_c": 320.0,
  "operating_pressure_bar": 18.2,
  "operating_temp_c": 245.0,
  "material_grade": "SA-516 Gr 70",
  "nominal_thk_mm": 12.0,
  "min_required_thk_mm": 8.2,
  "corrosion_allowance_mm": 3.0,
  "criticality": "High",
  "pid_doc_id": "PID-10-CDU-001"
}
```

#### 7. `get_line_list`
- **Description:** Returns piping line register, pipe specs, size, and connected equipment tags.
- **Parameters:** `unit_id: Optional[int]`, `equipment_tag: Optional[str]`
- **Required Clearance:** Level 1+

#### 8. `query_telemetry`
- **Description:** Queries historical sensor readings and alarm thresholds for an online tag.
- **Parameters:** `tag: str` (e.g. `"10-TI-101"`), `hours: Optional[int]`, `limit: Optional[int]`
- **Required Clearance:** Level 1+

---

### Group 3: Inspection & Reliability (Level 2+)

#### 9. `get_thickness_history`
- **Description:** Retrieves ultrasonic thickness readings across surveys for condition monitoring locations (CMLs).
- **Parameters:** `tag: str`, `cml_id: Optional[str]` (e.g. `"10-E-101"`, `"CML-7"`)
- **Required Clearance:** **Level 2+**
- **Sample Output for Hero CML-7:**
```json
[
  {
    "reading_id": 7,
    "report_no": "IR-2024-10-E101-UT",
    "cml_id": "CML-7",
    "reading_date": "2024-04-15",
    "measured_thk_mm": 9.6,
    "nominal_thk_mm": 12.0,
    "min_thk_mm": 8.2,
    "total_metal_loss_mm": 2.4,
    "location_desc": "Shell Bottom Course Under Insulation"
  },
  {
    "reading_id": 15,
    "report_no": "IR-2026-10-E101-UT",
    "cml_id": "CML-7",
    "reading_date": "2026-04-15",
    "measured_thk_mm": 8.9,
    "nominal_thk_mm": 12.0,
    "min_thk_mm": 8.2,
    "total_metal_loss_mm": 3.1,
    "location_desc": "Shell Bottom Course Under Insulation (Severe CUI)"
  }
]
```

#### 10. `get_inspection_reports`
- **Description:** Retrieves inspection dossiers, inspector signatures, and summaries.
- **Parameters:** `tag: str`
- **Required Clearance:** **Level 2+**

#### 11. `get_integrity_findings`
- **Description:** Retrieves open and resolved findings, severities, and recommendations.
- **Parameters:** `tag: Optional[str]`, `severity: Optional[str]`
- **Required Clearance:** **Level 2+**

#### 12. `get_turnaround_plan`
- **Description:** Retrieves scheduled turnaround overhaul dates (e.g. `TA-2028-CDU` in Oct 2028).
- **Parameters:** `unit_id: Optional[int]`
- **Required Clearance:** **Level 2+**

---

### Group 4: Maintenance & Standards (Level 2+)

#### 13. `get_work_orders`
- **Description:** Retrieves maintenance work orders, priorities, costs, and assigned engineers.
- **Parameters:** `tag: Optional[str]`, `status: Optional[str]`
- **Required Clearance:** **Level 2+**

#### 14. `get_standards_register`
- **Description:** Retrieves engineering standards citations (API 510, API 570, ASME Sec VIII).
- **Parameters:** `code_name: Optional[str]`
- **Required Clearance:** Level 1+

---

### Group 5: Procurement, Commercial Bids & Budgets (Level 3 & 4)

#### 15. `get_vendors`
- **Description:** Lists approved equipment contractors, ratings, and contact info.
- **Parameters:** `vendor_code: Optional[str]`
- **Required Clearance:** **Level 2+**

#### 16. `get_rate_contracts`
- **Description:** Retrieves active annual rate contracts and unit rates (e.g. `RC-2026-EXCH-04` at ₹12,50,000).
- **Parameters:** `contract_ref: Optional[str]`, `vendor_id: Optional[int]`
- **Required Clearance:** **Level 3+**

#### 17. `get_department_budget`
- **Description:** Checks allocated, spent, and remaining budget for a cost center.
- **Parameters:** `cost_center_code: str` (e.g. `"CC-10-CDU"`), `fiscal_year: Optional[str]`
- **Required Clearance:** **Level 3+**
- **Sample Output:**
```json
{
  "budget_id": 9,
  "cost_center_code": "CC-10-CDU",
  "cost_center_name": "Unit-10 Crude Distillation Maintenance",
  "fiscal_year": "2026-27",
  "allocated_amount_inr": 15000000.0,
  "committed_amount_inr": 8500000.0,
  "spent_amount_inr": 4650000.0,
  "remaining_amount_inr": 1850000.0
}
```

#### 18. `get_delegation_of_authority`
- **Description:** Retrieves financial DOA approval thresholds and concurrence rules.
- **Parameters:** None
- **Required Clearance:** **Level 2+**

#### 19. `get_commercial_bids`
- **Description:** Retrieves confidential vendor commercial tender bids.
- **Parameters:** `rfq_number: str` (e.g. `"RFQ-2026-EXCH-04"`)
- **Required Clearance:** **Level 4 STRICTLY REQUIRED!**
- **When Called by Level 2 or 3 (Access Denied Response):**
```json
{
  "status": "ACCESS_DENIED",
  "error_code": "INSUFFICIENT_CLEARANCE",
  "required_clearance_level": 4,
  "current_clearance_level": 2,
  "domain": "commercial_bids",
  "authenticated_as": {
    "emp_code": "EMP-1008",
    "name": "Arun V. Rao",
    "designation": "Plant / Inspection Engineer",
    "department": "Inspection & Asset Reliability"
  },
  "message": "Access Denied: The requested domain 'commercial_bids' requires Clearance Level 4 (Level 4: Executive Authority / GM / Director), but active user 'Arun V. Rao' holds Level 2. Please authenticate as an authorized officer."
}
```
- **When Called by Level 4 (GM / Director):**
```json
[
  {
    "bid_id": 1,
    "rfq_number": "RFQ-2026-EXCH-04",
    "vendor_name": "Apex PetroTech Services Pvt Ltd",
    "vendor_code": "VEND-004",
    "amount_inr": 1250000.0,
    "submission_date": "2026-01-05",
    "status": "Selected",
    "classification_level": 4
  },
  {
    "bid_id": 3,
    "rfq_number": "RFQ-2026-EXCH-04",
    "vendor_name": "Alfa Laval India Pvt Ltd",
    "vendor_code": "VEND-003",
    "amount_inr": 1390000.0,
    "submission_date": "2026-01-04",
    "status": "Rejected",
    "classification_level": 4
  },
  {
    "bid_id": 2,
    "rfq_number": "RFQ-2026-EXCH-04",
    "vendor_name": "Larsen & Toubro Heavy Engineering",
    "vendor_code": "VEND-002",
    "amount_inr": 1480000.0,
    "submission_date": "2026-01-04",
    "status": "Rejected",
    "classification_level": 4
  }
]
```

#### 20. `get_capex_proposals`
- **Description:** Retrieves high-value refinery CAPEX proposals.
- **Parameters:** `cost_center_code: Optional[str]`
- **Required Clearance:** **Level 4 STRICTLY REQUIRED!**

---

### Group 6: HSE & Management of Change (Level 2 & 3)

#### 21. `get_hse_incidents`
- **Description:** Retrieves safety incident logs, near-misses, and root cause corrective actions.
- **Parameters:** `tag: Optional[str]`, `severity: Optional[str]`
- **Required Clearance:** **Level 2+**

#### 22. `get_permits_to_work`
- **Description:** Retrieves Permits to Work (Hot Work, Cold Work, Confined Space, LOTO).
- **Parameters:** `tag: Optional[str]`, `status: Optional[str]`
- **Required Clearance:** **Level 2+**

#### 23. `get_moc_records`
- **Description:** Retrieves Management of Change (MOC) authorizations.
- **Parameters:** `tag: Optional[str]`
- **Required Clearance:** **Level 3+**

---

### Group 7: Document Registry & Blob Content

#### 24. `search_documents`
- **Description:** Searches registered enterprise technical documents, automatically filtering out any document where `classification_level > current_clearance`.
- **Parameters:** `query: Optional[str]`, `doc_type: Optional[str]`, `dept_code: Optional[str]`
- **Required Clearance:** Dynamic (returns documents $\le$ user clearance)

#### 25. `get_document_content`
- **Description:** Retrieves document metadata and physical file text/content from blob storage. Gated by document classification level.
- **Parameters:** `doc_id: str` (e.g. `"DOC-INSP-2026-E101"`, `"DOC-BID-APEX-EXCH"`)
- **Required Clearance:** Equal to or greater than the document's classification (1 to 4)

---

### Group 8: Safe Read-Only SQL Query

#### 26. `run_read_only_sql`
- **Description:** Executes a custom `SELECT` or `WITH` query inside a transaction-enforced read-only session with a 5-second timeout. Mutation keywords (`INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, etc.) and multi-statements are blocked by the parser.
- **Parameters:** `sql_query: str`
- **Required Clearance:** Level 1+

---

## 5. How to Run & Deploy (`run_mcp.sh`)

A single, unified shell script manages the entire environment:

```bash
cd /home/vicky/Projects/SIH_mcp
chmod +x run_mcp.sh
```

### Command Options:

| Command | Action | Description |
| :--- | :--- | :--- |
| `./run_mcp.sh` | **Interactive SSE Mode** | Runs the MCP server in the foreground on `http://0.0.0.0:8085/sse` |
| `./run_mcp.sh --daemon` | **Background Daemon** | Detaches server in the background, logging to `mcp_server.log` |
| `./run_mcp.sh --status` | **Check Status** | Shows whether the daemon is running and displays PID |
| `./run_mcp.sh --stop` | **Stop Server** | Safely terminates any running daemon instance |
| `./run_mcp.sh --stdio` | **Stdio Mode** | Launches stdio transport for direct CLI/IDE integration |
| `./run_mcp.sh --test` | **Run Tests** | Executes the automated multi-tier RBAC verification suite |

---

## 6. Client Integration

### A. Integrating with Claude Desktop / Cursor / Antigravity CLI (Stdio Mode)
Add to your `mcpServers` configuration (`~/.config/claude/claude_desktop_config.json` or Antigravity config):

```json
{
  "mcpServers": {
    "crpl_gateway": {
      "command": "/home/vicky/Projects/SIH_mcp/.venv/bin/python",
      "args": [
        "/home/vicky/Projects/SIH_mcp/server.py",
        "--stdio"
      ],
      "env": {
        "DATABASE_URL": "postgresql://kriya_ro:kriya_ro_pass@127.0.0.1:5432/company_db",
        "BLOB_STORAGE_PATH": "/home/vicky/database/company_storage/blob"
      }
    }
  }
}
```

### B. Integrating via Remote HTTP SSE (Port 8085)
Start the server in background daemon mode:
```bash
./run_mcp.sh --daemon
```
The SSE endpoint is immediately accessible over LAN or Tailscale:
```text
http://100.127.46.50:8085/sse
```

Test the SSE connection:
```bash
curl -s -N --max-time 2 http://127.0.0.1:8085/sse
```
Response:
```text
event: endpoint
data: /messages/?session_id=...
```

---

## 7. Hackathon Demo Walkthrough Scenarios

### 🌟 Scenario A: Hero Exchanger `10-E-101` Multi-Hop Reasoning

**Prompt to Agent:**
> *"Examine the integrity of Crude Pre-heat Exchanger 10-E-101. Determine if it can safely operate until the next turnaround. If repair is needed, determine the repair cost, verify if the department has sufficient budget, and state who must approve the expenditure note."*

**Agent Execution Steps via MCP:**
1. **Handshake:**
   Agent calls `handshake_authenticate(emp_code="EMP-1008")` (Arun Rao, Inspector).
2. **Retrieve Equipment Specs:**
   Agent calls `get_equipment("10-E-101")` $\rightarrow$ $t_{nom} = 12.0\text{ mm}$, $t_{min} = 8.2\text{ mm}$.
3. **Retrieve Ultrasonic Thickness Readings:**
   Agent calls `get_thickness_history("10-E-101", "CML-7")` $\rightarrow$
   - 2024 reading: $9.60\text{ mm}$
   - 2026 reading: $8.90\text{ mm}$
4. **Agent Calculates True Corrosion Rate & Remaining Life:**
   $$\text{Metal Loss} = 9.60\text{ mm} - 8.90\text{ mm} = 0.70\text{ mm}$$
   $$\text{True Corrosion Rate} = \frac{0.70\text{ mm}}{2.0\text{ yr}} = 0.35\text{ mm/yr}$$
   $$\text{True Remaining Life (RL)} = \frac{8.90\text{ mm} - 8.20\text{ mm}}{0.35\text{ mm/yr}} = \mathbf{2.00\text{ Years}}$$
5. **Report Trap Detection:**
   Agent calls `get_document_content("DOC-INSP-2026-E101")`. Scanned summary claims $0.15\text{ mm/yr}$ and $4.6\text{ yr}$. Agent flags the discrepancy and overrides with the true computed value ($0.35\text{ mm/yr}$, $2.0\text{ yr}$).
6. **Turnaround Window Cutoff:**
   Agent calls `get_turnaround_plan(unit_id=1)` $\rightarrow$ `TA-2028-CDU` scheduled for October 2028 ($2.46\text{ years}$ away).
   **Conclusion:** Remaining life expires 6 months **before** turnaround $\rightarrow$ **Immediate shutdown repair required!**
7. **Contractor Rate Lookup:**
   Agent calls `get_rate_contracts("RC-2026-EXCH-04")` $\rightarrow$ Vendor *Apex PetroTech Services Pvt Ltd*, unit rate ₹12,50,000.
8. **Budget Check:**
   Agent calls `get_department_budget("CC-10-CDU")` $\rightarrow$ ₹18,50,000 remaining budget (Sufficient funds).
9. **Authority Routing:**
   Agent calls `get_delegation_of_authority()`:
   - Repair cost ₹12,50,000 exceeds AGM authority limit (₹5,00,000).
   - Approval routes to GM (`K. V. Ramanathan`) with Finance Concurrence (`Sunita Deshpande`).

---

### 🛡️ Scenario E: Role-Based Redaction & Confidentiality

**Test Case: Attempting to query vendor commercial tender bids**

1. **Step 1 (Inspector Persona):**
   - Agent calls `handshake_authenticate(emp_code="EMP-1008")` (Clearance Level 2).
   - Agent calls `get_commercial_bids("RFQ-2026-EXCH-04")`.
   - **Result:** **ACCESS DENIED**. Gateway responds that Level 4 Executive clearance is required.
2. **Step 2 (Executive GM Persona):**
   - Agent calls `handshake_authenticate(emp_code="EMP-1002")` (Clearance Level 4 GM).
   - Agent calls `get_commercial_bids("RFQ-2026-EXCH-04")`.
   - **Result:** **UNLOCKED**. Gateway reveals all bids:
     - Apex PetroTech: ₹12,50,000 (Selected)
     - Alfa Laval: ₹13,90,000 (Rejected)
     - L&T Heavy Engineering: ₹14,80,000 (Rejected)

---

## 8. Security & Read-Only Guarantees

1. **Role Privileges (`kriya_ro`):**
   ```sql
   ALTER ROLE kriya_ro SET default_transaction_read_only = on;
   ALTER ROLE kriya_ro SET statement_timeout = '10s';
   ```
2. **Transaction Isolation:**
   Every query executed by `db.py` runs inside an explicit `async with conn.transaction(readonly=True):` block.
3. **Hardware Engine Proof:**
   Even if an injection payload tries to execute:
   ```sql
   INSERT INTO corp.units (unit_code, unit_name) VALUES ('X', 'Y');
   ```
   PostgreSQL raises:
   ```text
   ERROR: cannot execute INSERT in a read-only transaction
   ```
4. **SQL Lexical Filtering:**
   The `run_read_only_sql` tool scans for and rejects any SQL string containing `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, `GRANT`, `REVOKE`, or multiple statements (`;`).

---

## 9. File Directory Summary

```text
/home/vicky/Projects/SIH_mcp/
├── DOCUMENTATION.md              # Complete single-file documentation (This file)
├── README.md                     # Quickstart summary
├── .env                          # Configuration (DB URL, Port, Host)
├── requirements.txt              # FastMCP, asyncpg, pydantic, uvicorn
├── run_mcp.sh                    # Single unified control script (Executable)
├── server.py                     # FastMCP entry point & tool registry
├── config.py                     # Environment loader
├── db.py                         # Asyncpg pool with read-only transaction guarantees
├── auth.py                       # Handshake manager, session state, clearance validator
├── tools/
│   ├── __init__.py
│   ├── auth_tools.py             # Handshake, session info, employee directory
│   ├── asset_tools.py            # Units, equipment, line list, telemetry
│   ├── inspection_tools.py       # Thickness readings, inspection reports, turnaround
│   ├── maintenance_tools.py      # Work orders, standards register
│   ├── finance_tools.py          # Rate contracts, budgets, commercial bids, DOA, CAPEX
│   ├── hse_tools.py              # Incidents, PTW, MOC records
│   ├── document_tools.py         # Document search & blob content retrieval (filtered)
│   └── query_tools.py            # Safe read-only SQL query runner
└── tests/
    └── test_handshake_mcp.py     # Automated multi-role verification suite
```
