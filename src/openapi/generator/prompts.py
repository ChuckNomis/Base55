import json


def build_user_prompt(tool: dict, openapi_spec: dict, base_url: str) -> str:
    """Build the user-facing prompt by injecting the OpenAPI spec and base URL."""
    spec_text = json.dumps(openapi_spec, ensure_ascii=False)
    if len(spec_text) > 12000:
        spec_text = spec_text[:12000] + "... [truncated]"

    signature = tool.get("signature", f"{tool['name']}(query: str)")

    pagination_note = ""
    if tool.get("fetch_all"):
        pagination_note = (
            "\nPAGINATION REQUIREMENT: This tool must return ALL items — not just one page.\n"
            "Examine the OpenAPI spec to find the pagination scheme "
            "(e.g. has_next/page/page_size, total/offset/limit, next_cursor, etc.).\n"
            "Implement a loop that keeps fetching until the API signals no more results.\n"
            "Do NOT rely on a single large page_size value.\n"
        )

    return (
        f"OpenAPI Spec:\n{spec_text}\n\n"
        f"Base URL (from spec servers[0].url): {base_url}\n\n"
        f"Generate the `{signature}` function.\n"
        f"Hardcode `{base_url}` directly as the base URL inside the function.\n"
        f"{pagination_note}\n"
        f"Tool description: {tool['description']}\n"
        f"Required output schema: {json.dumps(tool['output_schema'], indent=2)}"
    )
