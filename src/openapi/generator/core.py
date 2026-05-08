import json

from .llm import call_gpt
from .models import GeneratedTool, ToolsManifest
from .prompts import build_user_prompt


def make_all_tools(openapi_spec: dict, template: dict) -> ToolsManifest:
    """Generate all tools defined in the template from the given OpenAPI spec."""
    base_url = ""
    servers = openapi_spec.get("servers", [])
    if servers and isinstance(servers[0], dict):
        candidate = servers[0].get("url", "").strip()
        if candidate.startswith("http://") or candidate.startswith("https://"):
            base_url = candidate

    system_prompt = template["system_prompt"]
    tools: list[GeneratedTool] = []

    for tool_def in template.get("tools", []):
        print(f"[Generator] Generating tool: {tool_def['name']}")
        user_prompt = build_user_prompt(template, openapi_spec, base_url)
        raw = call_gpt(system_prompt, user_prompt)

        parsed = json.loads(raw)
        code = parsed.get("code", raw)

        tools.append(GeneratedTool(
            name=tool_def["name"],
            code=code,
            description=tool_def["description"],
        ))
        print(f"[Generator] Done: {tool_def['name']}")

    return ToolsManifest(tools=tools)
