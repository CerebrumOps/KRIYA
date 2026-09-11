# ==============================================================================
# KRIYA Progressive Skill & MCP Discovery Tools
# ==============================================================================
# Implements two-tiered progressive tool discovery:
# - System prompt receives only brief catalog (~30 tokens per skill)
# - Agent dynamically calls `list_available_skills` and `load_skill` on demand
# - Context window is kept compact and free from tool schema flooding
# ==============================================================================

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

SKILLS_DIR = Path(__file__).resolve().parent.parent.parent / "workbench" / "skills"
MCP_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "workbench" / "mcps" / "config.json"


def parse_skill_frontmatter(content: str) -> Dict[str, Any]:
    """Extracts YAML frontmatter from markdown file."""
    match = re.match(r"^---\s*\n([\s\S]*?)\n---\s*\n", content)
    metadata: Dict[str, Any] = {}
    if match:
        raw_yaml = match.group(1)
        current_list_key = None
        for line in raw_yaml.splitlines():
            line_str = line.strip()
            if not line_str or line_str.startswith("#"):
                continue
            if ":" in line_str and not line_str.startswith("-"):
                key, val = line_str.split(":", 1)
                key = key.strip()
                val = val.strip()
                if val:
                    metadata[key] = val
                    current_list_key = None
                else:
                    metadata[key] = []
                    current_list_key = key
            elif line_str.startswith("-") and current_list_key:
                val = line_str.lstrip("-").strip()
                metadata[current_list_key].append(val)
    return metadata


def list_available_skills() -> str:
    """
    Returns a lightweight catalog of all installed industrial skills in the workbench.
    Provides skill name, 1-line description, and keyword triggers.
    """
    if not SKILLS_DIR.exists():
        return "[Notice]: Skills directory not initialized."

    catalog = []
    for skill_folder in sorted(SKILLS_DIR.iterdir()):
        if skill_folder.is_dir():
            skill_file = skill_folder / "SKILL.md"
            if skill_file.exists():
                try:
                    content = skill_file.read_text(encoding="utf-8")
                    meta = parse_skill_frontmatter(content)
                    catalog.append({
                        "name": meta.get("name", skill_folder.name),
                        "description": meta.get("description", "Industrial operational skill"),
                        "triggers": meta.get("triggers", []),
                        "tools": meta.get("tools", [])
                    })
                except Exception as e:
                    catalog.append({"name": skill_folder.name, "error": str(e)})

    return json.dumps(catalog, indent=2)


def load_skill(skill_name: str) -> str:
    """
    Dynamically loads the complete operational guidelines and tool protocols
    for a specific skill from the workbench/skills directory.
    """
    skill_clean = skill_name.strip().lower()
    skill_path = SKILLS_DIR / skill_clean / "SKILL.md"

    if not skill_path.exists():
        # Search by folder name match
        for folder in SKILLS_DIR.iterdir():
            if folder.is_dir() and folder.name.lower() == skill_clean:
                skill_path = folder / "SKILL.md"
                break

    if not skill_path.exists():
        return f"[Error]: Skill '{skill_name}' was not found in workbench/skills."

    try:
        content = skill_path.read_text(encoding="utf-8")
        meta = parse_skill_frontmatter(content)
        # Strip frontmatter for clean instruction loading
        body = re.sub(r"^---\s*\n[\s\S]*?\n---\s*\n", "", content).strip()
        
        result = {
            "skill_loaded": meta.get("name", skill_name),
            "version": meta.get("version", "1.0.0"),
            "activated_tools": meta.get("tools", []),
            "instructions": body
        }
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"[Error loading skill '{skill_name}']: {str(e)}"


def inspect_mcp_servers() -> str:
    """
    Lists active Model Context Protocol (MCP) servers connected to KRIYA,
    including local on-premise appliances and remote air-gapped nodes.
    """
    if not MCP_CONFIG_PATH.exists():
        return "[Notice]: MCP configuration file not found at workbench/mcps/config.json."

    try:
        data = json.loads(MCP_CONFIG_PATH.read_text(encoding="utf-8"))
        return json.dumps(data, indent=2)
    except Exception as e:
        return f"[Error reading MCP config]: {str(e)}"


# ==============================================================================
# TOOL SCHEMAS FOR OPENAI COMPATIBILITY
# ==============================================================================

LIST_AVAILABLE_SKILLS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "list_available_skills",
        "description": "Lists all available domain skills installed in the KRIYA workbench with their descriptions and triggers.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}

LOAD_SKILL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "load_skill",
        "description": "Dynamically loads specialized engineering guidelines, SOP criteria, and tools for an industrial skill (e.g. 'inspection-report', 'code-sandbox', 'pid-inspection', 'management-presentation').",
        "parameters": {
            "type": "object",
            "properties": {
                "skill_name": {
                    "type": "string",
                    "description": "Name of the skill to load (e.g. 'inspection-report', 'code-sandbox', 'pid-inspection', 'management-presentation')"
                }
            },
            "required": ["skill_name"]
        }
    }
}

INSPECT_MCP_SERVERS_SCHEMA = {
    "type": "function",
    "function": {
        "name": "inspect_mcp_servers",
        "description": "Lists configured local and remote air-gapped MCP servers available to KRIYA.",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
}
