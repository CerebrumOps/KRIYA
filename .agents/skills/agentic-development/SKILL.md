---
name: agentic-development
description: Expert skill for Agentic AI architecture, multi-agent orchestration, FastMCP / Model Context Protocol, dynamic tool calling, progressive skill loading, and open-weight model optimization. Use when building, debugging, or scaling AI agents, tool registries, and subagent workflows.
---

# Agentic Systems & MCP Engineering Skill

This skill guides the design, construction, and optimization of multi-agent execution engines, dynamic tool systems, and Model Context Protocol (MCP) integrations.

---

## 1. Multi-Agent Orchestration Patterns

### A. Hierarchical Orchestrator-Worker
- **Orchestrator Agent**: Receives raw user intent, decomposes multi-step goals into subtasks, and routes to specialized worker agents.
- **Specialized Workers**: Each worker agent is scoped to a single domain (e.g. `ProcessEngineer`, `SafetyInspector`, `DocumentGenerator`) and is equipped **only** with the 2–4 tools needed for its domain.
- **Why**: Keeps context window small (crucial for local 7B–14B models) and eliminates tool confusion.

### B. Tool Execution Loop (ReAct / Think-Act-Observe)
1. **Think**: Model outputs its chain of reasoning (e.g. inside `<think>...</think>`).
2. **Act**: Model emits a structured tool call (`tool_calls` array with name and JSON arguments).
3. **Observe**: System executes the tool locally, captures `stdout`, `stderr`, and execution duration, and feeds the result back as a `tool` role message.
4. **Repeat**: Loop continues until the model produces its final answer or reaches `max_turns`.

---

## 2. Dynamic Tool Calling & Context Budgeting

### A. The 15-Tool Limit Rule
Local open-weight models suffer severe performance degradation when presented with more than 10–15 tool schemas simultaneously.

### B. Progressive Disclosure Pattern
Instead of loading all 50 tools into every prompt:
1. **Catalog Prompt**: Present a lightweight list of tool names and one-line summaries.
2. **Tool Discovery Tool**: The agent calls `search_tools(query="distillation")` to retrieve full schemas on demand.
3. **Scoped Execution**: The agent calls the discovered tool.

### C. Code-As-Action (The Python Sandbox Alternative)
Instead of creating dozens of separate JSON schemas:
- Provide a single tool: `execute_python(script: str)`.
- Pre-import internal libraries:
  ```python
  import kriya.refinery as plant
  data = plant.get_sensor("CDU-101")
  print(plant.calculate_heat_duty(data))
  ```
- The model writes code directly; standard Python docstrings serve as the documentation.

---

## 3. FastMCP / Model Context Protocol Integration

### A. Building a Standalone MCP Server
```python
from fastmcp import FastMCP

mcp = FastMCP("IndustrialSensorHub")

@mcp.tool
def get_sensor_telemetry(tag: str) -> dict:
    """Fetch live temperature, pressure, and vibration for equipment."""
    return {"tag": tag, "temp_c": 312.4, "pressure_bar": 24.1, "status": "NORMAL"}

@mcp.resource("drawing://pnd/{unit}")
def get_pnd_drawing(unit: str) -> str:
    """Fetch P&ID drawing text/SVG for a refinery unit."""
    return f"<svg unit='{unit}'>...</svg>"

if __name__ == "__main__":
    mcp.run()
```

### B. Consuming MCP in an Agent
1. Connect via `stdio` using subprocess pipes (`mcp.ClientSession(stdio_transport)`).
2. Query `session.list_tools()` to discover available tools.
3. Map MCP tool definitions directly into OpenAI-compatible function calling schemas.
4. Execute via `session.call_tool(name, arguments)`.

---

## 4. Hallucination Prevention on Local Models

1. **Explicit Grounding**: Always prepend grounding instructions: *"Rely strictly on the provided tool output. If the tool output does not contain the answer, state that the data is unavailable rather than guessing."*
2. **Calculation Sandboxing**: Never let the LLM calculate math directly in text. Always force calculations through a Python runner tool (`exec` or `eval`).
3. **Structured Deliverables**: Use deterministic templates (`python-docx`, `openpyxl`) populated by JSON variables rather than expecting the LLM to format raw documents from scratch.
