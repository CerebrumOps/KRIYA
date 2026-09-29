# ==============================================================================
# KRIYA Tool: DuckDuckGo Web Search
# ==============================================================================
# This tool allows KRIYA agents to search the web using DuckDuckGo to look up
# technical manuals, equipment specifications, news, or online documentation.
#
# IMPORTANT:
# Internet access is restricted in the air-gapped refinery workbench.
# Users control internet access via a toggle switch in the UI.
# The agent must seek user permission before invoking web search.
# ==============================================================================

from typing import Any, Dict, List


# 1. The Actual Python Tool Function
def search_duckduckgo(query: str, max_results: int = 3) -> str:
    """
    Searches DuckDuckGo for the given query and returns formatted search results.
    Checks the system internet toggle before attempting external connections.
    """
    if not query or not query.strip():
        return "[Error]: Search query cannot be empty."

    # Verify if user has enabled internet services for the workbench
    try:
        from agent.api.settings import is_internet_enabled
        if not is_internet_enabled():
            return (
                "[Internet Disabled]: Internet access is currently locked in sovereign air-gapped mode. "
                "You must ask the user for permission to access external internet services. "
                "Once the user approves and toggles ON 'Internet Access' in the workbench header, "
                "you can retry this web search."
            )
    except Exception:
        # If settings module is unavailable, proceed with fallback
        pass

    try:
        from ddgs import DDGS
        
        # Limit max_results between 1 and 5
        num_results = min(max(1, int(max_results)), 5)
        
        results = list(DDGS().text(query, max_results=num_results))

        if not results:
            return f"No search results found for query: '{query}'"

        output_lines = [f"### Web Search Results for: '{query}'\n"]
        for i, item in enumerate(results, 1):
            title = item.get("title", "No Title")
            snippet = item.get("body", "")
            href = item.get("href", "")
            output_lines.append(f"{i}. **{title}**")
            output_lines.append(f"   Link: {href}")
            output_lines.append(f"   Summary: {snippet}\n")

        return "\n".join(output_lines)

    except Exception as error:
        return f"[Error performing DuckDuckGo search]: {str(error)}"


# 2. OpenAI Function Tool Schema
WEBSEARCH_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_duckduckgo",
        "description": (
            "Search the web using DuckDuckGo to look up external documentation, equipment specifications, "
            "or technical guidelines. CRITICAL: KRIYA operates as a sovereign air-gapped system. "
            "Internet access is controlled by a user toggle switch in the UI. Before calling this tool, "
            "you MUST ask the user for explicit permission to use the internet. If internet is toggled OFF, "
            "the request will be blocked."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query string, for example: 'crude oil distillation temperature limits' or 'darcy weisbach friction factor formula'."
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of top results to retrieve (default: 3, max: 5)"
                }
            },
            "required": ["query"]
        }
    }
}
