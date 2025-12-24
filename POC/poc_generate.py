import argparse
import json
import os
from pathlib import Path

from openai import OpenAI


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def truncate_json_for_prompt(data: dict, max_chars: int) -> str:
    text = json.dumps(data, ensure_ascii=False)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [truncated]"


def build_user_prompt(tool: dict, spec_text: str) -> str:
    return (
        "You will generate a FastMCP-compatible Python tool that calls the best matching "
        "endpoint(s) from the OpenAPI spec for the tool below. Ignore unrelated/dummy "
        "endpoints (orders/users/auth, etc.).\n\n"
        "OpenAPI spec (possibly truncated):\n"
        f"{spec_text}\n\n"
        "Tool Definition:\n"
        f"Name: {tool.get('name')}\n"
        f"Description: {tool.get('description')}\n"
        f"Input Schema: {json.dumps(tool.get('input_schema', {}))}\n"
        f"Output Schema: {json.dumps(tool.get('output_schema', {}))}\n\n"
        "Requirements:\n"
        "- Prefer endpoints under /products (e.g., /products/search or /products) for product search.\n"
        "- Do NOT use endpoints from other domains like orders, users, or auth unless no product endpoints exist.\n"
        "- Return only valid Python code. Avoid markdown fences in the response.\n"
        "- If multiple endpoints fit, pick the simplest that supports keyword search.\n"
        "- Ensure output matches the provided output schema."
    )


def generate_tools(template_path: str, openapi_path: str, model: str, max_chars: int, output_dir: Path | None):
    template = load_json(template_path)
    openapi_spec = load_json(openapi_path)

    spec_text = truncate_json_for_prompt(openapi_spec, max_chars)
    system_prompt = template["generation_prompt"]

    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    tools = template.get("tools", [])
    if not tools:
        raise ValueError("Template contains no tools.")

    for tool in tools:
        user_prompt = build_user_prompt(tool, spec_text)
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = resp.choices[0].message.content

        print("\n=== Tool Output: {name} ===".format(name=tool.get("name", "unknown")))
        print(content)

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / f"{tool.get('name', 'tool')}.py"
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"\n[Saved to] {out_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="POC: Generate FastMCP tools from OpenAPI and template.")
    parser.add_argument("--template", default="POC/template_products.json", help="Path to template JSON.")
    parser.add_argument("--openapi", default="POC/sample_openapi.json", help="Path to OpenAPI JSON.")
    parser.add_argument("--model", default=os.getenv("OPENAI_MODEL", "gpt-4o"), help="OpenAI model to use.")
    parser.add_argument("--max-chars", type=int, default=12000, help="Max characters of OpenAPI JSON to include in prompt.")
    parser.add_argument("--output-dir", type=Path, default=None, help="Optional dir to write generated tool files.")
    return parser.parse_args()


def main():
    args = parse_args()
    generate_tools(
        template_path=args.template,
        openapi_path=args.openapi,
        model=args.model,
        max_chars=args.max_chars,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()

