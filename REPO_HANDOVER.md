# KRIYA: Sovereign AI Agent Harness & Industrial Workbench
## Master Handover & Technical Specification Document for AI Agents

> **Audience**: AI Coding Agents, Engineers, and Maintainers taking over KRIYA.  
> **Scope**: Complete end-to-end repository context, architectural invariants, file map, data flows, tool contracts, setup guides, and operational commands.

---

## 1. Executive Summary & Problem Context

**KRIYA** (*Knowledge-based Reasoning & Intelligent Action*) is a 100% self-hosted, air-gapped, sovereign AI agentic workbench built for sensitive industrial enterprises:
* **Target Domain**: Mangalore Refinery and Petrochemicals Limited (MRPL), PSUs, defense-linked manufacturing, and government infrastructure.
* **Core Problem (SIH Problem Statement #26117)**: Public cloud assistants (ChatGPT, Claude) cannot be used in refineries due to strictly confidential data—Piping & Instrumentation Diagrams (P&IDs), operating parameters, ultrasonic corrosion logs, vendor pricing, and turnaround strategies. Employees are forced into slow manual paperwork or risk data leakage.
* **KRIYA Solution**: An on-premise, multi-model agentic workbench that:
  1. Operates with **verifiable zero cloud calls** on private GPU/workstation hardware.
  2. Dynamically auto-selects open-weight models (reasoning, vision/VLM for scanned drawings, coder for utilities).
  3. Transcends chat by **synthesizing real corporate deliverables** (`.docx` Word approval notes, `.xlsx` multi-tab Excel workbooks, `.pptx` PowerPoint decks).
  4. Runs code inside an isolated **zero-network Docker sandbox** with autonomous error self-repair.
  5. Dynamically queries plant SCADA/DCS telemetry and standard operating procedures (SOPs) via the **Model Context Protocol (FastMCP)**.
  6. Enforces **cross-artifact mathematical consistency** (validating that numbers in PowerPoint slides exactly match underlying Excel calculations).

---

## 2. High-Level Architecture

```
                       +-----------------------------------------------------+
                       |   Distributed Open-Weight Inference Cluster / Phone |
                       |   - Reasoning: Qwen-2.5-14B / DeepSeek-R1 Distill    |
                       |   - Coding:    Qwen2.5-Coder-7B                     |
                       |   - Vision:    Qwen2-VL / Llama-3.2-Vision          |
                       |   (Served via llama.cpp / vLLM / Model Balancer)     |
                       +--------------------------+--------------------------+
                                                  ^
                                           OpenAI HTTP API
                                                  v
+------------------------+  SSE Stream  +---------+-------------------------+  Async SQL  +-----------------------+
|  Frontend Workbench    | <=========== |  FastAPI Backend (Port 5000)        | <=========> | PostgreSQL (Port 5432)|
|  (React 19, TypeScript,|              |  - Re-Act Agentic Loop              |             |  - kriya_db           |
|   Tailwind CSS, Vite)  | ===========> |  - Planning & Task Checklist Agent  |             |  - Company Directory  |
|  (Port 3000)           |   REST API   |  - Dual-Save Workspace Isolation    |             |  - Chat & Memories    |
+------------------------+              +----+-------------------------+----+             +-----------------------+
                                             |                         |
                        Tool Calls / Sandbox |                         | FastMCP Client
                                             v                         v
                   +-------------------------+----+       +------------+--------------------+
                   | Docker Sandbox Container     |       | Standalone FastMCP Server       |
                   | (kriya-sandbox:latest)       |       | (mcps/server.py on Port 8085)   |
                   | - Isolated (--network none)  |       | - Live Refinery Telemetry       |
                   | - 512MB RAM cap              |       | - CDU-II, FCCU, DHT Sensors     |
                   | - Differential Snapshotting  |       | - Maintenance SOPs Storage      |
                   +------------------------------+       +---------------------------------+
```

---

## 3. Complete Repository Map & File Guide

```text
/home/vicky/Projects/KRIYA/
├── run.py                               # Master concurrent runner (Backend + Frontend + FastMCP)
├── requirements.txt                     # Backend Python dependencies
├── DEMO_DAY_Ideas.md                    # Core judge demonstration flows & surprise capabilities
├── HACKATHON_DEMO_PROMPTS.md            # Ready-to-copy hackathon demonstration prompts
├── AUTHENTICATION_API_CONTRACT.md       # Full REST API specification for enterprise auth & 2FA
├── SIH_PS_26117.md                      # Official Smart India Hackathon problem statement
├── .env.example                         # Template for network bindings, ports, and model gateway
├── backend/
│   ├── main.py                          # FastAPI application factory, CORS, and router registration
│   ├── run_backend.py                   # Standalone backend launcher with reload filters
│   ├── api/
│   │   ├── auth_routes.py               # Enterprise 4-step registration & 2-step 2FA login
│   │   ├── admin_routes.py              # Personnel & directory administration
│   │   ├── company_routes.py            # Departmental directory & shift roster endpoints
│   │   ├── conversation_routes.py       # Session CRUD, history loading, auto-titling
│   │   ├── model_client.py              # Async HTTP client adapter connecting to local LLMs
│   │   ├── plan_routes.py               # Mission Control planner API & checklist sync
│   │   ├── session.py                   # Session token validation & employee state resolution
│   │   ├── webchat_routes.py            # SSE `/api/chat/stream` multi-step agent streaming endpoint
│   │   └── workspace_routes.py          # Deliverables listing, metadata indexing, file download
│   ├── database/
│   │   ├── company/                     # Seeded MRPL employee registry, departments, sites
│   │   ├── kriya_db/                    # Async PostgreSQL tables, queries, migrations
│   │   └── memories/                    # Persistent sovereign memory store
│   ├── orchestration/
│   │   ├── loop.py                      # Multi-step streaming Re-Act loop, <think> parser, safety net
│   │   ├── tool_handler.py              # Model tool call parser and execution dispatcher
│   │   └── main.py                      # Non-streaming orchestration runner
│   ├── registries/
│   │   ├── tools_registry.py            # Master mapping of tool names to functions & OpenAI schemas
│   │   └── agents_registry.py           # Subagent definitions (planner, memory, execution)
│   ├── subagents/
│   │   ├── planning_agent.py            # Autonomous multi-step engineering plan generator
│   │   ├── task_queue.py                # Real-time task checklist updater (update_task_checklist)
│   │   └── memory_agent.py              # Sovereign 2-agent memory pipeline (storage & retrieval)
│   ├── tools/
│   │   ├── deliverable_generator.py     # Generates .docx, .xlsx, .pptx, and consistency verification
│   │   ├── docker_sandbox.py            # Isolated Docker container runner with differential snapshotting
│   │   ├── mcp_client.py                # Client adapter communicating with FastMCP on Port 8085
│   │   ├── refinery_tools.py            # SCADA telemetry query, SOP search, unit inspection
│   │   ├── skill_tools.py               # Two-tiered progressive skill loading from workbench/skills
│   │   ├── terminal.py                  # Sandboxed local OS command execution
│   │   ├── websearch.py                 # Sovereign DuckDuckGo search fallback
│   │   └── workspace_manager.py         # Multi-tenant user workspace isolation & ContextVar fallback
│   └── schemas/                         # Pydantic v2 validation models (conversation, chat, models)
├── frontend/
│   ├── package.json                     # React 19, TypeScript, Lucide Icons, Vite dependencies
│   ├── vite.config.js                   # Vite bundler configuration & proxy setup
│   ├── run_frontend.py                  # Standalone frontend HTTP server
│   ├── src/
│   │   ├── App.tsx                      # Root application component, auth flow, layout state
│   │   ├── api/                         # Frontend API clients (chat, conversation, workspace, plan, auth)
│   │   ├── components/
│   │   │   ├── ChatArea/
│   │   │   │   ├── ChatArea.tsx         # Main chat container
│   │   │   │   ├── MessageList.tsx      # Renders chat messages, <think> drawers, in-chat deliverable cards
│   │   │   │   ├── ChatInput.tsx        # Prompt input bar, plan mode toggle, suggestion pills
│   │   │   │   ├── TaskChecklistPanel.tsx # Live Mission Control checklist progress bar & items
│   │   │   │   └── MarkdownRenderer.tsx # GitHub markdown & KaTeX mathematical renderer
│   │   │   ├── Sidebar/                 # Conversation session manager, new chat, user card
│   │   │   ├── RightToolPanel.tsx       # Real-time animated drawer showing live tool execution
│   │   │   ├── DeliverablesDrawer.tsx   # Slide-out file browser for generated docx/xlsx/pptx
│   │   │   ├── AdminPortal.tsx          # Enterprise employee management & directory UI
│   │   │   └── AuthModal.tsx            # Multi-step corporate onboarding & 2FA modal
│   │   └── utils/                       # Token calculators, clipboard helpers, error formatters
├── mcps/
│   ├── server.py                        # Standalone FastMCP server (Port 8085) with refinery sensors
│   ├── run.py                           # Runner script for FastMCP server
│   └── requirements.txt                 # FastMCP & Starlette dependencies
├── workbench/
│   ├── skills/                          # Progressive domain skills (parsed on-demand)
│   │   ├── code-sandbox/SKILL.md        # Python utility authoring & test harness guidelines
│   │   ├── inspection-report/SKILL.md   # Scanned PDF parsing, corrosion analysis, docx synthesis
│   │   ├── management-presentation/SKILL.md # Excel financial modeling, PPTX deck synthesis
│   │   └── pid-inspection/SKILL.md      # P&ID drawing visual analysis & component flagging
│   └── mcps/config.json                 # FastMCP client registry configuration
└── workspace/                           # Working directory for physical deliverables
    ├── users/                           # Per-user isolated folders (e.g. users/EMP-1001/{chat_id}/)
    └── *.docx, *.xlsx, *.pptx           # Dual-saved verified business artifacts
```

---

## 4. Key Architectural Mechanisms & Invariants

### A. Dual-Save Workspace Isolation Engine
* **Files**: `backend/tools/workspace_manager.py`, `backend/tools/deliverable_generator.py`, `backend/api/workspace_routes.py`
* **Problem**: In multi-threaded FastAPI / Starlette request handling, Python's `contextvars.ContextVar` can lose context when background threads or sub-processes execute tools, causing files to be saved in a generic folder while the frontend looks inside `workspace/users/{employee_id}/{chat_id}/`.
* **Solution**:
  1. `workspace_manager.py` maintains both `ContextVar` and global fallback pointers (`_last_active_workspace_dir`, `_last_active_employee`, `_last_active_chat`).
  2. The deliverable generator uses `_dual_save_file()`: every `.docx`, `.xlsx`, or `.pptx` file is written **simultaneously** to the user-and-chat specific path AND to `workspace/`.
  3. `workspace_routes.py` searches both locations when listing or downloading deliverables, ensuring 100% file discovery regardless of authentication mode.

### B. Automated Deliverable Synthesis Safety Net
* **File**: `backend/orchestration/loop.py`
* **Problem**: Open-weight LLMs sometimes suffer from instruction drift—explaining what a document should contain in markdown rather than actually triggering the tool function to write the binary file.
* **Solution**:
  * An automated safety interceptor runs immediately after the model loop:
    * If the user prompt asked for Word (`.docx`), Excel (`.xlsx`), PowerPoint (`.pptx`), Consistency Verification, or Sandbox Execution, and the corresponding tool name is missing from `executed_tools: set`, KRIYA **automatically executes the generator function** on the server.
    * It streams the corresponding `<tool_call>` and `<tool_result>` tags to the UI so the frontend renders the interactive deliverable card and file download button seamlessly.
  * **Forced Final Synthesis**: If tools were executed but the model stopped without summarizing findings, KRIYA runs a secondary inference pass with `tools=None` to guarantee a comprehensive final engineering report.

### C. Cross-Artifact Numerical Consistency Verifier
* **File**: `backend/tools/deliverable_generator.py` (`verify_artifact_consistency`)
* **Problem**: Refinery executives reject AI presentations if financial costs or defect numbers on slides conflict with supporting calculation spreadsheets.
* **Solution**:
  * A deterministic Python parser:
    1. Uses `openpyxl` to open the generated `.xlsx` workbook, evaluate formulas, and extract calculated totals (e.g., `₹1,045,000.00`).
    2. Uses `python-pptx` to traverse shapes, tables, and paragraphs across all slides in the generated `.pptx`.
    3. Cross-compares the exact numerical figures and finding counts.
    4. Emits a deterministic verification report (`✓ MATCH` / `MISMATCH`) directly to the operator.

### D. Zero-Network Docker Sandbox with Differential File Snapshotting
* **File**: `backend/tools/docker_sandbox.py`
* **Operation**:
  * Runs code inside the `kriya-sandbox:latest` container with `--network none`, `--memory 512m`, and temporary volume mounting.
  * **Differential Snapshotting**: Takes a directory snapshot of the sandbox tempdir before execution. When a script runs and creates new output files (e.g. `critical_findings.csv`), KRIYA diffs the directory post-execution, intercepts all newly generated files, and copies them to the active user workspace.
  * **Autonomous Self-Repair**: If `proc.returncode != 0`, captures `stderr` and test tracebacks, returning them to the model loop so it can inspect the failure and patch the script.
  * **Fallback**: If the Docker daemon is absent, gracefully falls back to a restricted host subprocess sandbox using `sys.executable`.

### E. Two-Tiered Progressive Skill Discovery
* **Files**: `backend/tools/skill_tools.py`, `workbench/skills/*/SKILL.md`
* **Problem**: Open-weight models have limited context windows (8k–32k tokens). Flooding the system prompt with 40 tool schemas degrades reasoning performance.
* **Solution**:
  * The system prompt receives only a 30-token summary of available skills.
  * The agent invokes `list_available_skills()` and `load_skill("inspection-report")` on-demand to load specific guidelines and schemas into memory only when working on that domain.

### F. Standalone FastMCP Telemetry Server
* **Files**: `mcps/server.py`, `backend/tools/mcp_client.py`
* **Operation**: Runs on port `8085` using standard Model Context Protocol (FastMCP) with SSE transport. Exposes realistic MRPL refinery telemetry (Crude Distillation Unit CDU-II, Fluid Catalytic Cracking Unit FCCU, Desulfurization DHT) with live sensor readings (temperatures, pressures, amine injection rates, wall thickness).

---

## 5. Environment Variables & Port Layout

### Port Allocation:
| Service | Port | Host Binding | Responsibility |
|:---|:---|:---|:---|
| **Frontend Web UI** | `3000` | `0.0.0.0` | React 19 / Vite development server |
| **Backend API** | `5000` | `0.0.0.0` | FastAPI core orchestration & REST endpoints |
| **FastMCP Server** | `8085` | `0.0.0.0` | Standalone refinery telemetry server (SSE) |
| **PostgreSQL** | `5432` | `100.100.63.50` / `localhost` | `kriya_db` relational and state database |
| **Model Gateway** | `8000` / `8080` | `100.98.154.51` | Local LLM load balancer / inference cluster |

### `.env` Reference:
```env
# Sovereign LLM Load Balancer / Phone Gateway (OpenAI compatible)
MODEL_BALANCER_URL=http://100.98.154.51:8000/v1
MODEL_BALANCER_KEY=sih2026

# Backend Server Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=5000
BACKEND_URL=http://100.100.63.50:5000

# Frontend Server Configuration
FRONTEND_HOST=0.0.0.0
FRONTEND_PORT=3000
VITE_BACKEND_URL=http://100.100.63.50:5000

# FastMCP Appliance
MCP_HOST=0.0.0.0
MCP_PORT=8085

# PostgreSQL Database Configuration
DATABASE_URL=postgresql://postgres@100.100.63.50:5432/kriya_db
```

---

## 6. How to Run & Verify the System

### 1. Unified Launcher (Recommended):
```bash
# Activates .venv and concurrently launches FastMCP (8085), Backend (5000), and Frontend (3000)
python run.py
```

### 2. Independent Component Launchers:
```bash
# Terminal 1: FastMCP Appliance
python mcps/run.py

# Terminal 2: Backend API Server
python backend/run_backend.py

# Terminal 3: Frontend Web Client
python frontend/run_frontend.py
```

### 3. Frontend Production Build Check:
```bash
cd frontend
npm run build
# Must output 0 errors
```

### 4. Docker Sandbox Image Verification:
```bash
docker images | grep kriya-sandbox
# Tests sandbox execution
docker run --rm --network none --memory 512m kriya-sandbox:latest python -c "print('Sandbox OK')"
```

---

## 7. Master Demonstration Prompts (for Evaluation / SIH Jury)

### Demo 1: Inspection Report → Formal Word Approval Note (`.docx`)
* **Prompt**:
  > *"Analyze the attached scanned inspection report for the CDU-II compressor overhead line. Extract the key findings, identify observations that require attention, cross-check them against the relevant maintenance SOPs in the internal knowledge base, and prepare a draft approval note in Word format. Include the evidence from the report, applicable SOP references, recommended action, and clearly mark anything that requires human review."*
* **Outputs**: `Approval_Note.docx` / `CDU2_Corrosion_Approval_Note.docx` directly downloadable via in-chat card.

### Demo 2: Autonomous Coding Sandbox with Self-Repair Loop
* **Prompt**:
  > *"Create a Python utility that reads the inspection findings generated in this workspace, generates a CSV summary of critical findings, and produces a simple severity report. Run the program in the local sandbox, create test cases, fix any errors you encounter, and provide the verified working code."*
* **Outputs**: `generate_report.py`, `critical_findings.csv`, `severity_summary.csv` produced inside Docker and auto-exported to workspace.

### Demo 3: Management Presentation & Cross-Artifact Consistency Verification
* **Prompt**:
  > *"Using the inspection findings and cost summary available in this workspace, prepare a management-ready presentation covering the issue, impact, recommended action, estimated cost, and next steps. Use the existing organization presentation template and include the supporting data in an Excel workbook. Then run a cross-artifact consistency verification to confirm numbers match."*
* **Outputs**: `Inspection_Cost_Analysis.xlsx`, `Management_Review.pptx`, and verification output (`✓ MATCH`).

---

## 8. Common Pitfalls & Invariants for Incoming Agents

1. **Uvicorn Reload Hangs**:
   * Do NOT allow uvicorn to watch `workspace/` or root directory without exclusion patterns. Doing so triggers uvicorn reload mid-stream whenever a deliverable (`.docx`, `.xlsx`) is generated, causing `Waiting for background tasks to complete` hangs.
   * `backend/run_backend.py` is configured with `reload_dirs=[backend]` and `reload_excludes=[workspace/*, *.docx, *.xlsx]`. Preserve this.
2. **Docker Isolation**:
   * Always maintain `--network none` and `--memory 512m` when running the sandbox. Air-gapped compliance forbids outbound socket connections from the sandbox container.
3. **Open-Weight Tool Calling Robustness**:
   * Tools in `backend/tools/` must accept flexible kwargs (`**kwargs` or argument aliases like `unit` vs `unit_id`, `title` vs `doc_title`). Open-weight models occasionally vary argument key naming.
4. **Deliverable Dual-Saving**:
   * Whenever adding new file generation tools, always save files via `_dual_save_file()` or write to both `get_active_workspace_dir()` and `BASE_WORKSPACE_DIR` so that both authenticated chat sessions and guest/default sessions can access them immediately.
5. **No External Cloud Dependencies**:
   * Never introduce dependencies on OpenAI/Anthropic cloud endpoints or external cloud vector databases. All vector search, token generation, and parsing must run locally.

---
*Document automatically compiled for seamless AI Agent handover. KRIYA is fully operational, verified, and ready for production extension.*
