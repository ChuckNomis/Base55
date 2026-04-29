# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

**Base55** is an AI-powered MCP (Model Context Protocol) server generator. It takes an OpenAPI specification and automatically produces a deployable TypeScript MCP server — complete with tool functions and a visual UI (e.g. a product carousel). The core pipeline:

```
OpenAPI spec → GPT-4o → TypeScript tool function → Handlebars template → complete MCP server
```

## Setup

```bash
# Python dependencies (generator + demo API)
pip install -r dev/generator/requirements.txt
pip install -r demo_api/requirements.txt

# Build the assembler (TypeScript → JS)
cd dev/assembler && npm install && npm run build && cd ../..
```

Requires an `OPENAI_API_KEY` env var for the generator step.

## Running the Full Pipeline

**1. Start the demo commerce API** (reference OpenAPI source):
```bash
uvicorn demo_api.main:app --host 127.0.0.1 --port 8001
```
OpenAPI spec served at `http://127.0.0.1:8001/openapi.json`

**2. Generate the MCP server:**
```bash
export OPENAI_API_KEY=sk-...

python -m dev.generator.generate \
  --openapi http://127.0.0.1:8001/openapi.json \
  --template dev/templates/products.json \
  --output-dir dev/generated_server/
```
This calls GPT-4o to write tool functions, saves `tools_manifest.json`, then runs the assembler to produce the complete `dev/generated_server/` directory.

**3. Run the generated server:**
```bash
cd dev/generated_server && npm install && npm start
```

**4. Debug with MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector
```

## Architecture

### Generation (Python — `dev/generator/`)
- `generate.py` — CLI entrypoint; loads OpenAPI spec + template, writes manifest, calls assembler
- `core.py` — `make_all_tools()` orchestrates the loop over template tool definitions
- `llm.py` — `call_gpt()` sends system+user prompt to GPT-4o, expects JSON back
- `prompts.py` — injects OpenAPI spec and base URL into GPT prompt
- `models.py` — Pydantic models: `GeneratedTool`, `ToolsManifest`

### Assembly (TypeScript — `dev/assembler/`)
- `src/index.ts` — reads `tools_manifest.json`, renders Handlebars templates, writes output files
- Pure transformation step: no LLM calls, runs in milliseconds, can be re-run freely

### Templates (immutable — `dev/templates/`)
- `products.json` — template definition: system prompt, tool specs (name/description/output schema), UI type
- `mcp_server/server.hbs` — Handlebars scaffold for the MCP server (GPT-generated tool code is injected here)
- `ui/carousel.html` — dark-theme product carousel UI (communicates via `postMessage`)

### Demo API (`demo_api/`)
- FastAPI server with paginated product list, keyword search, and single-product lookup
- Loads from `demo_api/data/products.json`; uses stemming for fuzzy search
- `demo_api.yaml` — the OpenAPI 3.0 spec for this API (can also be used as generator input)

### Generated Output (`dev/generated_server/` — git-ignored)
Recreated on each run. Contains: `index.ts`, `carousel.html`, `package.json`, `tsconfig.json`

## Key Design Decisions

- **GPT writes only tool logic** — the function body that calls the API and maps the response. All MCP plumbing, UI wiring, and transport setup come from templates.
- **Base URLs are hardcoded** in generated functions (extracted from `servers[0].url` in the OpenAPI spec). No runtime env config needed in the generated server.
- **Output schema is enforced** — templates define the exact shape GPT must return (e.g. `{ products: [...] }`). Missing fields return empty strings; prices are formatted as `"$29.99"`.
- **Carousel UI data flow** — the HTML handles three message formats (direct, MCP method, tool result) to stay flexible across MCP host environments.

## Adding a New Tool Type

1. Create a new template JSON in `dev/templates/` with `system_prompt`, `tools[]`, and `ui_template`
2. Add a matching UI HTML in `dev/templates/ui/`
3. No Python or assembler code changes needed

## VS Code MCP Integration

`.vscode/mcp.json` is configured to point at the generated server for local debugging.
