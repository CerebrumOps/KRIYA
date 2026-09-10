# KRIYA

> **Local AI Agent Harness & Sovereign Execution Engine**  
> An on-premise, air-gapped agentic runtime designed to run open-weight models locally with multi-step reasoning, real-time token streaming, pluggable tools, and PostgreSQL session persistence.

---

## Overview

**KRIYA** (Knowledge-based Reasoning & Intelligent Action) is a modular, local-first agent harness that bridges local LLM inference engines (such as `llama-server`, vLLM, or Ollama) with robust tool execution and session management. 

Built with zero external cloud dependencies, KRIYA executes multi-turn tool loops entirely on private hardware, streams reasoning and tool lifecycles in real time to the user interface, and securely persists conversation state in PostgreSQL.

---

## Core Capabilities

- 🧠 **Multi-Step Agentic Loop**: Orchestrates multi-turn reasoning and tool invocation cycles. When a tool is triggered, results feed directly back into the model's context for subsequent reasoning until task completion.
- ⚡ **Real-Time Token & Thought Streaming**: Employs Server-Sent Events (SSE) to stream reasoning thoughts (`<think>`), tool execution status, and final answers token-by-token in strict chronological order.
- 🛠️ **OpenAI-Compatible Tool Registry**: Standardized schema registration and handler binding. Easily plug in new functions (terminal runners, search modules, file parsers) with automatic parameter validation.
- 🗄️ **PostgreSQL Session Persistence**: Lightweight, async storage layer (`kriya_db`) storing full message histories in standard OpenAI JSON format, enabling instant chat restoration and state rehydration.
- 🏷️ **Autonomous Session Titling**: A background mini-agent evaluates the initial exchange (user prompt, reasoning, and response) and generates concise 2-to-3 word session titles without tool schema clutter.
- 🔌 **Pluggable Architecture**: Fully decoupled FastAPI backend and TypeScript API/schema layer, structured for seamless integration into modern React/Vite frontends.

---

## Architecture

```
                                +---------------------------+
                                |  Local LLM / Balancer     |
                                |  (llama-server, vLLM)     |
                                +-------------+-------------+
                                              ^
                                     OpenAI API (HTTP)
                                              v
+------------------+         SSE Stream  +----+----------------------+         Async SQL  +--------------------+
|  Workbench UI    | <================== |  FastAPI Backend Engine   | <================> |  PostgreSQL DB     |
|  (React/TS SPA)  |                     |  - Multi-Step Loop        |                    |  (kriya_db)        |
+------------------+ ==================> |  - Tool Registry & Runner |                    +--------------------+
                           REST API      +-------------+-------------+
                                                       |
                                               Tool Dispatch
                                                       v
                                         +-------------+-------------+
                                         |  Local Tools Sandbox      |
                                         |  - Terminal Execution     |
                                         |  - Web Search Engine      |
                                         +---------------------------+
```

---

## Repository Structure

```text
KRIYA/
├── backend/
│   ├── api/
│   │   ├── conversation_routes.py    # Session CRUD and titling endpoints
│   │   ├── model_client.py          # Asynchronous LLM client adapter
│   │   └── webchat_routes.py        # SSE streaming chat endpoints
│   ├── database/
│   │   └── kriya_db/
│   │       ├── schema/
│   │       │   └── conversation.py  # PostgreSQL DDL and Pydantic records
│   │       └── request/
│   │           └── conversation_db.py # Async database queries (asyncpg)
│   ├── orchestration/
│   │   ├── loop.py                  # Multi-step streaming agent loop
│   │   ├── tool_handler.py          # Local tool execution dispatcher
│   │   └── main.py                  # Orchestration entrypoint
│   ├── prompts/
│   │   └── system_prompts/
│   │       └── conversation_naming_sys.py # Titling mini-agent prompt
│   ├── registries/
│   │   ├── agents_registry.py       # Subagent definitions
│   │   └── tools_registry.py        # Central tool mappings & schemas
│   ├── schemas/
│   │   ├── conversation.py          # Session API request/response models
│   │   ├── model_request.py         # LLM payload specifications
│   │   └── webchat.py               # Chat streaming payload models
│   ├── tools/
│   │   ├── terminal.py              # Sandboxed terminal command runner
│   │   └── websearch.py             # DuckDuckGo search integration
│   ├── main.py                      # FastAPI application setup
│   └── run_backend.py               # Standalone backend launcher
├── frontend/
│   ├── api/
│   │   ├── chat_api.ts              # TypeScript streaming client
│   │   └── conversation_api.ts      # TypeScript session API client
│   ├── schemas/
│   │   ├── chat.ts                  # Chat message types
│   │   └── conversation.ts          # Conversation state interfaces
│   ├── index.html                   # Single-file React workbench UI
│   └── run_frontend.py              # Standalone frontend HTTP server
├── .env.example                     # Environment configuration template
├── requirements.txt                 # Core Python dependencies
└── run.py                           # Unified development runner
```

---

## Getting Started

### Prerequisites

- **Python**: 3.10 or higher
- **PostgreSQL**: 14 or higher running locally (port `5432`)
- **LLM Inference Server**: An OpenAI-compatible endpoint (e.g. `llama-server`, vLLM, Ollama, or local gateway)

### 1. Clone & Setup Environment

```bash
git clone https://github.com/your-org/KRIYA.git
cd KRIYA

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and set your local model and database endpoints:

```bash
cp .env.example .env
```

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

# PostgreSQL Database Configuration
DATABASE_URL=postgresql://postgres@100.100.63.50:5432/kriya_db
```

### 3. Initialize PostgreSQL Database

Ensure PostgreSQL is running and create the `kriya_db` database:

```bash
createdb -U postgres kriya_db
```

*(Database tables and indexes are initialized automatically on backend startup).*

### 4. Run the Stack

To launch both the backend API and frontend UI concurrently:

```bash
python run.py
```

- **Frontend Workbench UI**: `http://<FRONTEND_IP>:3000`
- **Backend API**: `http://<BACKEND_IP>:5000`
- **Interactive OpenAPI Docs**: `http://<BACKEND_IP>:5000/docs`

You can also run services independently on separate machines:

```bash
# Backend machine
python backend/run_backend.py

# Frontend machine
python frontend/run_frontend.py
```

---

## API Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/api/chat/stream` | Multi-step agent execution with real-time SSE streaming |
| `GET` | `/api/conversations` | List conversation sessions (ID and title only) |
| `POST` | `/api/conversations` | Create a new session |
| `GET` | `/api/conversations/{id}` | Fetch full message history for a session |
| `POST` | `/api/conversations/{id}/messages` | Append completed user-assistant exchange |
| `POST` | `/api/conversations/{id}/generate-title` | Autonomous 2-to-3 word session titling |
| `DELETE` | `/api/conversations/{id}` | Delete a conversation session |
| `GET` | `/health` | Health check endpoint |

---

## Adding Custom Tools

Tools follow standard OpenAI function schemas and consist of an implementation function and a schema definition:

1. Create a tool in `backend/tools/my_tool.py`:
   ```python
   def execute_my_tool(param: str) -> str:
       # Tool execution logic
       return "Tool result"

   MY_TOOL_SCHEMA = {
       "type": "function",
       "function": {
           "name": "my_tool",
           "description": "Description of tool capability",
           "parameters": {
               "type": "object",
               "properties": {
                   "param": {"type": "string", "description": "Parameter details"}
               },
               "required": ["param"]
           }
       }
   }
   ```

2. Register the tool in `backend/registries/tools_registry.py`:
   ```python
   from backend.tools.my_tool import execute_my_tool, MY_TOOL_SCHEMA

   TOOLS_MAP["my_tool"] = execute_my_tool
   TOOLS_SCHEMA.append(MY_TOOL_SCHEMA)
   ```

The agentic loop will automatically expose the tool to the LLM and execute it when requested.

---

## Security & Sovereign Design

- **Air-Gapped Operation**: No outbound requests to commercial cloud AI APIs.
- **Local Tool Execution**: Commands run strictly on local infrastructure.
- **Data Privacy**: All chat history, prompt exchanges, and reasoning traces remain inside your local PostgreSQL instance.
