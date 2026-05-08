import json


def build_user_prompt(template: dict, openapi_spec: dict, base_url: str) -> str:
    """Build the user-facing prompt by injecting the OpenAPI spec and base URL."""
    spec_text = json.dumps(openapi_spec, ensure_ascii=False)
    if len(spec_text) > 12000:
        spec_text = spec_text[:12000] + "... [truncated]"

    tool = template["tools"][0]

    return (
        f"OpenAPI Spec:\n{spec_text}\n\n"
        f"Base URL (from spec servers[0].url): {base_url}\n\n"
        f"Generate the `{tool['name']}(query: string)` function.\n"
        f"Hardcode `{base_url}` directly as the base URL inside the function.\n\n"
        f"Tool description: {tool['description']}\n"
        f"Required output schema: {json.dumps(tool['output_schema'], indent=2)}"
    )
