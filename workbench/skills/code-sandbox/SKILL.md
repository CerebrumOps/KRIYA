---
name: code-sandbox
description: Specialized skill for developing on-premise Python utilities, generating unit tests, executing within an isolated Docker/subprocess sandbox, and executing autonomous self-repair loops upon test failure.
version: 1.0.0
triggers:
  - python utility
  - create script
  - run in sandbox
  - test cases
  - self repair
  - fix errors
tools:
  - run_code_in_sandbox
  - execute_terminal_command
---

# Code Sandbox & Autonomous Self-Repair Skill

## Purpose
Enables KRIYA to author Python utilities on-premise, verify them inside an isolated sandbox, observe stderr and assertion tracebacks, and automatically repair implementation bugs without human prompting.

## Operational Workflow
1. **Tool Requirements & File Inspection**:
   - Inspect input schemas, CSV columns, or previous workspace artifacts.
2. **Code Generation & Test Harness**:
   - Write the Python utility file (e.g. `generate_report.py`).
   - Write comprehensive unit tests (e.g. `test_report.py`) with pytest or unittest assertions.
3. **Sandbox Execution**:
   - Execute test harness inside the sandbox using `run_code_in_sandbox(code, test_code)`.
4. **Self-Repair Feedback Loop**:
   - If exit code != 0 or tests fail:
     - Read stdout and stderr stack trace.
     - Reason on root cause (e.g., KeyError, division by zero, edge case parsing).
     - Patch the implementation.
     - Rerun in sandbox until all tests pass (`✓ PASS`).
5. **Final Output**:
   - Produce verified script and generated output files (e.g., CSV, JSON summary).
