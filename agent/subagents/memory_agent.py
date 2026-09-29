# ==============================================================================
# KRIYA Subagents: 2-Agent Memory Pipeline & Engineering Memory Tools
# ==============================================================================
# Implements the dual-agent memory architecture:
# 1. MemoryRetrievalAgent: Dual-source semantic search over both explicit saved
#    memories (`chat_memories` table) and historical dialogues (`conversations` table).
# 2. MemorySummarizerAgent: Synthesizes retrieved insights according to current
#    user prompt and context, generating actionable engineering briefs.
# 3. Dedicated tools: `store_agent_memory` and `search_and_summarize_memories`.
# ==============================================================================

import asyncio
import json
from typing import Any, Dict, List, Optional

from agent.database.memory_db import (
    store_memory,
    search_saved_memories,
    search_past_conversations,
    list_recent_memories
)
from agent.workspace.workspace_manager import get_active_employee_id, get_active_chat_id


class MemoryRetrievalAgent:
    """
    Subagent 1: Memory Retrieval Specialist.
    Concurrently searches saved memories and past conversation transcripts
    to find relevant technical parameters, SOP precedents, and operational notes.
    """

    async def retrieve(
        self,
        query: str,
        context: Optional[str] = None,
        employee_id: Optional[str] = None,
        limit_memories: int = 5,
        limit_conversations: int = 5
    ) -> Dict[str, Any]:
        emp_id = employee_id or get_active_employee_id() or "EMP-1001"
        current_chat = get_active_chat_id()

        # Combine query with context clues if present
        search_query = query
        if context:
            search_query = f"{query} {context}"

        # Run concurrent retrieval over saved memories and past conversations
        saved_task = search_saved_memories(emp_id, search_query, limit=limit_memories)
        convs_task = search_past_conversations(emp_id, search_query, current_conversation_id=current_chat, limit=limit_conversations)

        saved_results, conv_results = await asyncio.gather(saved_task, convs_task)

        return {
            "query": query,
            "employee_id": emp_id,
            "saved_memories": saved_results,
            "past_conversations": conv_results,
            "total_candidates": len(saved_results) + len(conv_results)
        }


class MemorySummarizerAgent:
    """
    Subagent 2: Memory Synthesis & Summarization Specialist.
    Analyzes raw candidates from MemoryRetrievalAgent against the current task context,
    producing a crisp, zero-hallucination factual operational summary.
    """

    def summarize(
        self,
        retrieval_data: Dict[str, Any],
        user_query: str,
        context: Optional[str] = None
    ) -> str:
        saved_memories = retrieval_data.get("saved_memories", [])
        past_convs = retrieval_data.get("past_conversations", [])

        if not saved_memories and not past_convs:
            return (
                f"### [Memory Intelligence Briefing]\n"
                f"No previous chat memories or historical engineering records matched query: \"{user_query}\".\n"
                f"Proceeding with primary refinery database and live plant telemetry queries."
            )

        lines = [
            "### [Memory Intelligence Briefing - Sovereign Knowledge Retrieval]",
            f"**Query Focus**: {user_query}",
            ""
        ]

        # 1. Structured Saved Memories Section
        if saved_memories:
            lines.append("#### Verified Saved Technical Memories:")
            for mem in saved_memories:
                m_type = mem.get("memory_type", "insight").upper()
                content = mem.get("content", "").strip()
                score = mem.get("score", 0.0)
                kw = mem.get("keywords", [])
                kw_str = f" | Tags: {', '.join(kw[:4])}" if kw else ""
                lines.append(f"- **[{m_type}]** (Relevance: {score}){kw_str}")
                lines.append(f"  {content}")
            lines.append("")

        # 2. Historical Conversation Context Section
        if past_convs:
            lines.append("#### Relevant Historical Conversation Context:")
            for c in past_convs:
                title = c.get("conversation_title", "Previous Session")
                role = c.get("role", "user").upper()
                excerpt = c.get("excerpt", "").strip()
                score = c.get("score", 0.0)
                lines.append(f"- **[Chat: {title}] ({role} Turn, Relevance: {score})**:")
                lines.append(f"  \"{excerpt}\"")
            lines.append("")

        # 3. Contextual Synthesis & Recommendations
        lines.append("#### Operational Synthesis for Active Task:")
        if context:
            lines.append(f"- **Active Task Context**: {context}")
        lines.append("- Historical parameters above should be cross-referenced with live sensor telemetry before final sign-off.")

        return "\n".join(lines)


# Singleton instances
_retriever = MemoryRetrievalAgent()
_summarizer = MemorySummarizerAgent()


# ==============================================================================
# TOOL IMPLEMENTATIONS (ASYNC & SYNC)
# ==============================================================================

async def store_agent_memory_async(
    content: Optional[str] = None,
    memory_type: str = "insight",
    keywords: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    employee_id: Optional[str] = None,
    **kwargs
) -> str:
    """
    Stores an explicit engineering determination, user preference, or formula result
    in the chat_memories PostgreSQL database table.
    """
    try:
        real_content = content or kwargs.get("text") or kwargs.get("finding") or kwargs.get("memory") or kwargs.get("observation") or "Engineering finding recorded."
        real_keywords = keywords or kwargs.get("tags") or kwargs.get("tag_list") or []
        real_type = memory_type or kwargs.get("type") or "insight"

        emp_id = employee_id or get_active_employee_id() or "EMP-1001"
        chat_id = get_active_chat_id()
        record = await store_memory(
            employee_id=emp_id,
            content=real_content,
            memory_type=real_type,
            conversation_id=chat_id,
            keywords=real_keywords,
            metadata=metadata
        )
        return (
            f"[SUCCESS: Memory Stored]\n"
            f"ID: {record['id']}\n"
            f"Type: {record['memory_type']}\n"
            f"Employee: {record['employee_id']}\n"
            f"Content: {record['content']}\n"
            f"Keywords: {record['keywords']}"
        )
    except Exception as e:
        return f"[Error storing memory]: {str(e)}"


def store_agent_memory(
    content: Optional[str] = None,
    memory_type: str = "insight",
    keywords: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
    employee_id: Optional[str] = None,
    **kwargs
) -> str:
    """Synchronous wrapper for tool registry execution."""
    real_content = content or kwargs.get("text") or kwargs.get("finding") or kwargs.get("memory") or kwargs.get("observation") or "Engineering finding recorded."
    real_keywords = keywords or kwargs.get("tags") or kwargs.get("tag_list") or []
    real_type = memory_type or kwargs.get("type") or "insight"

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # In running event loop (FastAPI context)
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    store_agent_memory_async(real_content, real_type, real_keywords, metadata, employee_id, **kwargs)
                )
                return future.result(timeout=10)
        else:
            return loop.run_until_complete(
                store_agent_memory_async(real_content, real_type, real_keywords, metadata, employee_id, **kwargs)
            )
    except Exception as e:
        # Direct run fallback
        try:
            return asyncio.run(
                store_agent_memory_async(content, memory_type, keywords, metadata, employee_id)
            )
        except Exception as inner_e:
            return f"[Error storing memory]: {str(inner_e)}"


async def search_and_summarize_memories_async(
    query: str,
    context: Optional[str] = None,
    employee_id: Optional[str] = None
) -> str:
    """
    Invokes the 2-agent memory subagent pipeline:
    1. MemoryRetrievalAgent retrieves dual-source candidates.
    2. MemorySummarizerAgent synthesizes the briefing for the main orchestrator agent.
    """
    try:
        emp_id = employee_id or get_active_employee_id() or "EMP-1001"
        retrieval_data = await _retriever.retrieve(
            query=query,
            context=context,
            employee_id=emp_id
        )
        summary = _summarizer.summarize(retrieval_data, user_query=query, context=context)
        return summary
    except Exception as e:
        return f"[Error in memory retrieval pipeline]: {str(e)}"


def search_and_summarize_memories(
    query: str,
    context: Optional[str] = None,
    employee_id: Optional[str] = None
) -> str:
    """Synchronous wrapper for tool registry execution."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    search_and_summarize_memories_async(query, context, employee_id)
                )
                return future.result(timeout=15)
        else:
            return loop.run_until_complete(
                search_and_summarize_memories_async(query, context, employee_id)
            )
    except Exception as e:
        try:
            return asyncio.run(
                search_and_summarize_memories_async(query, context, employee_id)
            )
        except Exception as inner_e:
            return f"[Error in memory retrieval]: {str(inner_e)}"


# ==============================================================================
# OPENAI FUNCTION SCHEMAS FOR TOOLS REGISTRY
# ==============================================================================

STORE_MEMORY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "store_agent_memory",
        "description": "Stores a factual engineering determination, equipment baseline, operator preference, or SOP reference into the persistent chat_memories knowledge store.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "The exact fact, parameter, or decision to remember."
                },
                "memory_type": {
                    "type": "string",
                    "description": "Type of memory: 'insight', 'technical_param', 'sop_preference', 'calculation_result', or 'turnaround_note'. Default: 'insight'."
                },
                "keywords": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Search tags (e.g. ['CDU-II', 'corrosion', 'amine_dosing'])."
                },
                "metadata": {
                    "type": "object",
                    "description": "Optional dictionary of contextual properties (e.g. {'unit': 'CDU-II', 'sop': 'SOP-MRPL-4.2.3'})."
                }
            },
            "required": ["content"]
        }
    }
}

RETRIEVE_MEMORY_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_and_summarize_memories",
        "description": "Invokes the 2-agent memory subagent to search past chat memories and historical conversation exchanges, returning a synthesized briefing of relevant operational context.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query or engineering topic to recall (e.g. 'CDU-II corrosion rates', 'vibration thresholds')."
                },
                "context": {
                    "type": "string",
                    "description": "Optional current task context to guide the summarizer agent's relevance filtering."
                }
            },
            "required": ["query"]
        }
    }
}
