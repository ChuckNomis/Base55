import argparse
import json
import os
import re
from pathlib import Path

try:
    # Load environment variables from .env if available (optional dependency)
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    # If python-dotenv is not installed, continue without raising
    pass

from openai import OpenAI


def load_json(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def truncate_json_for_prompt(data: dict, max_chars: int) -> str:
    text = json.dumps(data, ensure_ascii=False)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "... [truncated]"


def extract_code_only(content: str) -> str:
    # Strip markdown fences if present and return only code content.
    if "```" not in content:
        return content.strip()
    segments = content.split("```")
    for seg in segments:
        cleaned = seg.lstrip()
        if cleaned.startswith("python"):
            cleaned = cleaned[len("python") :].lstrip("\n\r\t ")
        if cleaned.strip():
            return cleaned.strip()
    return content.strip()


def validate_tool_function_only(code: str, tool_name: str) -> list[str]:
    missing: list[str] = []
    if f"def {tool_name}" not in code and f"async def {tool_name}" not in code:
        missing.append(f"function definition for {tool_name}")
    # Prefer explicit parameters over `input: dict`.
    if re.search(rf"(async\s+)?def\s+{re.escape(tool_name)}\s*\(\s*input\s*:\s*dict", code):
        missing.append("explicit function parameters (do not use input: dict)")
    if "@mcp.tool" in code.replace(" ", ""):
        missing.append("remove @mcp.tool (POC requires function-only output)")
    if "FastMCP" in code or "mcp = " in code:
        missing.append("remove FastMCP/mcp server wiring (POC requires function-only output)")
    # rough check for docstring: triple quotes somewhere after def line
    if f"def {tool_name}" in code or f"async def {tool_name}" in code:
        # Heuristic: require any triple-quote in file
        if '"""' not in code and "'''" not in code:
            missing.append("function docstring")
    return missing


def call_model(client: OpenAI, model: str, system_prompt: str, user_prompt: str) -> str:
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return extract_code_only(resp.choices[0].message.content)


def build_user_prompt(tool: dict, spec_text: str) -> str:
    tool_prompt = tool.get("tool_prompt") or tool.get("prompt") or (
        "Select the best matching endpoint(s) from the OpenAPI spec for this tool. "
        "Ignore unrelated or dummy endpoints. Ensure the response matches the output schema."
    )
    return (
        "You will generate a FastMCP-compatible Python tool that calls the best matching "
        "endpoint(s) from the OpenAPI spec for the tool below.\n\n"
        f"Tool-Specific Instructions:\n{tool_prompt}\n\n"
        "OpenAPI spec (possibly truncated):\n"
        f"{spec_text}\n\n"
        "Tool Definition:\n"
        f"Name: {tool.get('name')}\n"
        f"Description: {tool.get('description')}\n"
        f"Input Schema: {json.dumps(tool.get('input_schema', {}))}\n"
        f"Output Schema: {json.dumps(tool.get('output_schema', {}))}\n\n"
        "Requirements:\n"
        "- Identify endpoints that best satisfy the tool description and schemas.\n"
        "- Ignore endpoints whose domain or schema does not align with the tool.\n"
        "- Return only valid Python code. No markdown fences, no prose, no comments.\n"
        "- Prefer a single top-level function (no class) unless a class is required by the tool shape.\n"
        "- If multiple endpoints fit, pick the simplest correct option.\n"
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
        content = call_model(client, model, system_prompt, user_prompt)

        # Minimal quality guard: if the output doesn't match required format, retry once with a corrective instruction.
        tool_name = tool.get("name", "tool")
        missing = validate_tool_function_only(content, tool_name)
        if missing:
            fix_prompt = (
                user_prompt
                + "\n\nFORMAT FIX REQUIRED:\n"
                + f"The output is missing: {', '.join(missing)}.\n"
                + "Regenerate the entire file to satisfy ALL format requirements. Return ONLY Python code."
            )
            content = call_model(client, model, system_prompt, fix_prompt)

        print("\n=== Tool Output: {name} ===".format(name=tool_name))
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

