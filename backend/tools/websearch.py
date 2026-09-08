# ==============================================================================
# KRIYA Tool: DuckDuckGo Web Search
# ==============================================================================
# This tool allows KRIYA agents to search the web using DuckDuckGo to look up
# technical manuals, equipment specifications, news, or online documentation.
#
# Style:
# 1. Tool function at top
# 2. OpenAI-compatible JSON schema below it
# ==============================================================================

from typing import Any, Dict, List


# 1. The Actual Python Tool Function
def search_duckduckgo(query: str, max_results: int = 3) -> str:
    """
    Searches DuckDuckGo for the given query and returns formatted search results.
    """
    if not query or not query.strip():
        return "[Error]: Search query cannot be empty."

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
        "description": "Search the web using DuckDuckGo to look up external information, current guidelines, equipment specs, or technical documentation.",
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
