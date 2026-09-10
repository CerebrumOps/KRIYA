import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Generator, Optional
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI

from backend.schemas.model_request import (
    ChatMessage,
    FunctionDefinition,
    ModelRequest,
    ToolDefinition,
)

# Load environment variables from .env in the project root directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Central Sovereign Load Balancer configuration (loaded strictly from .env)
DEFAULT_BASE_URL = os.getenv("MODEL_BALANCER_URL")
DEFAULT_API_KEY = os.getenv("MODEL_BALANCER_KEY")


def get_openai_client(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> OpenAI:
    """Returns a synchronous OpenAI client configured for the local model balancer."""
    return OpenAI(
        base_url=base_url or DEFAULT_BASE_URL,
        api_key=api_key or DEFAULT_API_KEY
    )


def get_async_openai_client(
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> AsyncOpenAI:
    """Returns an asynchronous OpenAI client configured for the local model balancer."""
    return AsyncOpenAI(
        base_url=base_url or DEFAULT_BASE_URL,
        api_key=api_key or DEFAULT_API_KEY
    )


def send_chat_request(
    request: ModelRequest,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Any:
    """
    Sends a synchronous chat completion request to the model load balancer
    using the provided ModelRequest business logic.
    """
    client = get_openai_client(base_url, api_key)
    payload = request.to_openai_payload()
    payload["stream"] = False

    response = client.chat.completions.create(**payload)
    return response


async def send_async_chat_request(
    request: ModelRequest,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Any:
    """
    Sends an asynchronous chat completion request to the model load balancer
    using the provided ModelRequest business logic.
    """
    client = get_async_openai_client(base_url, api_key)
    payload = request.to_openai_payload()
    payload["stream"] = False

    response = await client.chat.completions.create(**payload)
    return response


def stream_chat_request(
    request: ModelRequest,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> Generator[str, None, None]:
    """
    Streams tokens synchronously from the model load balancer as they are generated.
    Yields content or reasoning tokens (e.g. DeepSeek-R1 / Qwen-Reasoning).
    """
    client = get_openai_client(base_url, api_key)
    payload = request.to_openai_payload()
    payload["stream"] = True

    response_stream = client.chat.completions.create(**payload)
    for chunk in response_stream:
        if chunk.choices:
            delta = chunk.choices[0].delta
            text = delta.content or getattr(delta, "reasoning_content", None)
            if text:
                yield text


async def stream_async_chat_request(
    request: ModelRequest,
    base_url: Optional[str] = None,
    api_key: Optional[str] = None
) -> AsyncGenerator[str, None]:
    """
    Streams tokens asynchronously from the model load balancer as they are generated.
    Yields content or reasoning tokens (e.g. DeepSeek-R1 / Qwen-Reasoning).
    """
    client = get_async_openai_client(base_url, api_key)
    payload = request.to_openai_payload()
    payload["stream"] = True

    response_stream = await client.chat.completions.create(**payload)
    async for chunk in response_stream:
        if chunk.choices:
            delta = chunk.choices[0].delta
            text = delta.content or getattr(delta, "reasoning_content", None)
            if text:
                yield text
