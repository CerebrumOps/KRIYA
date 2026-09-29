---
name: code-sandbox
description: Specialized skill for developing on-premise Python utilities, writing unit tests, executing within the container environment, and running autonomous self-repair loops upon test failure.
version: 1.0.0
triggers:
  - python utility
  - create script
  - test cases
  - self repair
  - fix errors
  - run script
tools:
  - execute_terminal_command
---

# Code Execution & Autonomous Self-Repair Skill

## Purpose
Enables KRIYA to author Python utilities on-premise, verify them inside the dedicated container OS, observe stderr and assertion tracebacks, and automatically repair implementation bugs without human prompting.

## Operational Workflow
1. **Tool Requirements & File Inspection**:
   - Inspect input data, schemas, CSV columns, or previous workspace artifacts.
2. **Code Generation & Test Harness**:
   - Write the Python utility file (e.g. `solution.py`).
   - Write comprehensive unit tests (e.g. `test_solution.py`) with `pytest` or `unittest` assertions.
3. **Execution**:
   - Execute test harness inside the workspace using `execute_terminal_command(command="python3 -m unittest test_solution.py")`.
4. **Self-Repair Feedback Loop**:
   - If returncode != 0 or tests fail:
     - Read stdout and stderr stack trace.
     - Reason on root cause (e.g., KeyError, boundary condition, type mismatch).
     - Patch the implementation.
     - Rerun until all tests pass (`✓ PASS`).
5. **Final Output**:
   - Produce verified script and generated output artifacts directly in the chat workspace.
