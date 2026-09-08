# ==============================================================================
# KRIYA - Agent Multi-Step Execution Loop
# ==============================================================================
# This file handles an individual user request from the web frontend.
# It supports:
# 1. Multi-step tool calling (model calls tool -> runs tool -> feeds back result)
# 2. Reasoning / Thinking mode toggle
# 3. Streaming all tokens, thinking tags, and tool events to the frontend
# ==============================================================================

import json
from typing import Any, Dict, Generator, List, Optional
from openai import OpenAI

from backend.api.model_client import get_openai_client
from backend.orchestration.tool_handler import handle_single_tool_call
from backend.registries.tools_registry import TOOLS_SCHEMA
from backend.schemas.model_request import ChatMessage, ModelRequest


# KRIYA Industrial System Prompt for MRPL
SYSTEM_PROMPT = (
    "You are KRIYA, a sovereign AI workbench assistant for confidential industrial "
    "work at Mangalore Refinery and Petrochemicals Limited (MRPL). "
    "You have access to local on-premise tools including 'execute_terminal_command'. "
    "When a user asks to check files, directories, run calculations, or inspect the system, "
    "use your tools to verify facts before answering. "
    "Always maintain plant safety standards and provide clear, professional engineering analysis."
)


def build_messages_history(user_message: str, history: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
    """
    Combines the system prompt, prior conversation history, and latest user query
    into standard OpenAI message dictionaries.
    """
    messages: List[Dict[str, Any]] = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ]

    # Add prior history from frontend if present
    if history:
        for msg in history:
            role = getattr(msg, "role", None) or msg.get("role", "user")
            content = getattr(msg, "content", None) or msg.get("content", "")
            messages.append({"role": role, "content": content})

    # Add latest user prompt
    messages.append({"role": "user", "content": user_message})
    return messages


def run_agent_loop_stream(
    user_message: str,
    history: Optional[List[Any]] = None,
    thinking: bool = False,
    model: str = "default",
    temperature: float = 0.2,
    max_steps: int = 5
) -> Generator[str, None, None]:
    """
    The core agent execution loop for streaming web responses.
    Iterates up to `max_steps` to handle multi-step tool calls.
    Yields:
      - `<think>...</think>` tags for reasoning
      - `<tool_call>...</tool_call>` tags when executing tools
      - `<tool_result>...</tool_result>` tags with tool outputs
      - Text tokens for the final response
    """
    client = get_openai_client()
    messages = build_messages_history(user_message, history)

    # Extra parameters for reasoning / thinking toggle
    extra_body = {}
    if thinking:
        extra_body = {
            "enable_thinking": True,
            "chat_template_kwargs": {"enable_thinking": True}
        }

    # Multi-step loop (runs until model finishes or reaches max_steps)
    for step in range(max_steps):
        # Call model with stream=True so tokens stream in real time
        stream_response = client.chat.completions.create(
            model=model or "default",
            messages=messages,
            tools=TOOLS_SCHEMA,
            temperature=temperature,
            stream=True,
            extra_body=extra_body if extra_body else None
        )

        accumulated_content = ""
        accumulated_reasoning = ""
        in_reasoning = False
        tool_calls_map = {}  # index -> {id, name, arguments}

        for chunk in stream_response:
            if not chunk.choices:
                continue

            choice = chunk.choices[0]
            delta = choice.delta

            # 1. Stream reasoning tokens (e.g. DeepSeek-R1 / Qwen reasoning_content)
            reasoning_chunk = getattr(delta, "reasoning_content", None)
            if reasoning_chunk and thinking:
                if not in_reasoning:
                    in_reasoning = True
                    yield "<think>\n"
                accumulated_reasoning += reasoning_chunk
                yield reasoning_chunk

            # 2. Stream standard content tokens (yielded token by token immediately!)
            content_chunk = delta.content
            if content_chunk:
                # If we were in reasoning_content mode and content starts, close </think>
                if in_reasoning:
                    in_reasoning = False
                    yield "\n</think>\n\n"

                accumulated_content += content_chunk
                yield content_chunk

            # 3. Accumulate tool call deltas if model is invoking a tool
            if delta.tool_calls:
                for tc in delta.tool_calls:
                    idx = tc.index if tc.index is not None else 0
                    if idx not in tool_calls_map:
                        tool_calls_map[idx] = {
                            "id": tc.id or f"call_{idx}",
                            "name": "",
                            "arguments": ""
                        }
                    if tc.id:
                        tool_calls_map[idx]["id"] = tc.id
                    if tc.function:
                        if tc.function.name:
                            tool_calls_map[idx]["name"] += tc.function.name
                        if tc.function.arguments:
                            tool_calls_map[idx]["arguments"] += tc.function.arguments

        # If stream finished while still in reasoning mode, close </think> tag
        if in_reasoning:
            in_reasoning = False
            yield "\n</think>\n\n"

        # Check if any tools were called
        if tool_calls_map:
            # Build assistant message with tool calls to preserve history for next step
            assistant_tool_calls = []
            for idx in sorted(tool_calls_map.keys()):
                t = tool_calls_map[idx]
                assistant_tool_calls.append({
                    "id": t["id"],
                    "type": "function",
                    "function": {
                        "name": t["name"],
                        "arguments": t["arguments"]
                    }
                })

            messages.append({
                "role": "assistant",
                "content": accumulated_content or None,
                "tool_calls": assistant_tool_calls
            })

            # Execute each tool locally and yield tool events to frontend
            for idx in sorted(tool_calls_map.keys()):
                t = tool_calls_map[idx]
                fn_name = t["name"]
                fn_args = t["arguments"]

                # Notify frontend that tool execution started
                yield f"\n<tool_call name=\"{fn_name}\" args='{fn_args}'>\n"

                # Execute the tool locally
                tool_data = handle_single_tool_call({
                    "id": t["id"],
                    "function": {"name": fn_name, "arguments": fn_args}
                })
                output_str = tool_data["result"]

                # Notify frontend of tool output
                yield f"</tool_call>\n<tool_result name=\"{fn_name}\">\n{output_str}\n</tool_result>\n\n"

                # Append tool result message so model can read it in next iteration
                messages.append(tool_data["tool_message"])

            # Continue to next step in the loop so model reads the tool output
            continue

        else:
            # No tool calls: tokens were streamed directly to frontend in real time!
            break


def run_agent_loop(
    user_message: str,
    history: Optional[List[Any]] = None,
    thinking: bool = False,
    model: str = "default",
    temperature: float = 0.2,
    max_steps: int = 5
) -> str:
    """
    Non-streaming agent loop returning complete aggregated output string.
    """
    chunks = []
    for chunk in run_agent_loop_stream(
        user_message=user_message,
        history=history,
        thinking=thinking,
        model=model,
        temperature=temperature,
        max_steps=max_steps
    ):
        chunks.append(chunk)
    return "".join(chunks)
