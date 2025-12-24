---
name: FastMCP Best Practice Output
overview: Adjust the generator prompts and post-processing so the model outputs a FastMCP-decorated tool with a proper docstring description and best-practice HTTP/error handling, and regenerate the tool code.
todos:
  - id: update-tool-prompt-fastmcp
    content: Update `POC/template_products.json` per-tool prompt to require FastMCP-decorated tool code and a docstring description, code-only output.
    status: completed
  - id: tighten-generator-validation
    content: Update `POC/poc_generate.py` to enforce FastMCP output requirements (FastMCP import, mcp object, @mcp.tool, tool function name) and retry once if missing.
    status: completed
  - id: regenerate-and-verify
    content: Re-run generation and confirm `generated/search_products.py` is best-practice FastMCP tool code with a docstring description and no extra prose.
    status: completed
---

# Generate best-practice FastMCP tools

## Goal

Ensure generated code is a **best-practice FastMCP tool**: a decorated tool function with a **docstring description** and no extra prose/markdown.

## Files to change

- [`POC/template_products.json`](POC/template_products.json): strengthen per-tool `tool_prompt` to require FastMCP-style output and docstring description.
- [`POC/poc_generate.py`](POC/poc_generate.py): tighten base requirements and add a small validation/post-processing step to reject/strip non-code output and optionally re-prompt if the output is missing required FastMCP elements.

## Target output shape (what we will require)

- Imports: `from mcp.server.fastmcp import FastMCP` (and `import httpx` or `requests`).
- A module-level `mcp = FastMCP("...")`.
- A tool function:
- Decorated with `@mcp.tool()`.
- Has a docstring that includes the tool description.
- Uses timeouts, raises clear exceptions, and returns data matching the output schema.
- Output must be **only Python code** (no markdown fences, no commentary).

## Prompting changes

- Move “FastMCP decorated tool” requirements into the template’s `tool_prompt` and the generator’s generic requirements (so it works for every tool, not just products).
- Explicitly forbid classes unless the tool itself is a class-based pattern (rare), and require `@mcp.tool()`.

## Minimal quality guard

In `poc_generate.py`, after receiving the model response:

- Strip markdown fences (already done).
- Validate that output contains `FastMCP` + `@mcp.tool` + a function `def <tool_name>(...)`.
- If validation fails, automatically do a single retry with a short corrective instruction.

## Todos

- `update-tool-prompt-fastmcp`: Update `POC/template_products.json` to require FastMCP tool + docstring description.
- `tighten-generator-validation`: Update `POC/poc_generate.py` to enforce/validate FastMCP output and retry once if missing required elements.