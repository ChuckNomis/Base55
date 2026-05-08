# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

**Base55** is a web-based wizard that generates ready-to-deploy MCP (Model Context Protocol) servers with visual UI. Users choose a data source (OpenAPI spec or Shopify store), pick a UI template, and receive a working MCP server that renders interactive carousels inside AI hosts like Claude.

Two integration paths exist today:

1. **OpenAPI path** -- Takes any OpenAPI spec and uses GPT-4o to generate TypeScript tool functions, assembled into a complete MCP server.
2. **Shopify path** -- A pre-built MCP server that connects to the Shopify Storefront API and displays products in a carousel.

```
OpenAPI spec -> GPT-4o -> TypeScript tool functions -> Handlebars assembler -> MCP server
```

## Repository Structure

```
src/
  openapi/
    generator/     # Python: calls GPT-4o to generate tool functions from OpenAPI spec
    assembler/     # TypeScript: assembles tools_manifest.json into a deployable MCP server
    generated_server/  # Output dir (git-ignored) -- recreated on each pipeline run
  shopify/         # TypeScript MCP server for Shopify Storefront API
  wizard/          # (Phase 3) Web setup wizard -- not yet built (src/wizard/)
templates/
  products.json           # Template definition: system prompt + tool specs
  mcp_server/server.hbs   # Handlebars scaffold for generated MCP server
  ui/carousel.html        # Dark-theme product carousel UI
demo_api/          # FastAPI demo commerce API (reference OpenAPI source)
docs/              # Project documents, meeting notes
```

## Setup

```bash
# Python dependencies (OpenAPI generator + demo API)
pip install -r src/openapi/generator/requirements.txt
pip install -r demo_api/requirements.txt

# Build the assembler (TypeScript -> JS)
cd src/openapi/assembler && npm install && npm run build && cd ../../..
```

Requires an `OPENAI_API_KEY` env var for the OpenAPI generator step.

## Running the OpenAPI Pipeline

**1. Start the demo commerce API** (provides an example OpenAPI spec):
```bash
uvicorn demo_api.main:app --host 127.0.0.1 --port 8001
```
OpenAPI spec available at `http://127.0.0.1:8001/openapi.json`

**2. Generate the MCP server:**
```bash
export OPENAI_API_KEY=sk-...

python -m src.openapi.generator.generate \
  --openapi http://127.0.0.1:8001/openapi.json \
  --template templates/products.json \
  --output-dir src/openapi/generated_server/
```
This calls GPT-4o to write tool functions, saves `tools_manifest.json`, then runs the assembler to produce `src/openapi/generated_server/`.

**3. Run the generated server:**
```bash
cd src/openapi/generated_server && npm install && npm start
```

**4. Debug with MCP Inspector:**
```bash
npx @modelcontextprotocol/inspector
```

## Running the Shopify Demo

**Prerequisites:** Create a `.env` file in `src/shopify/` with:
```
SHOPIFY_STORE_DOMAIN=your-store.myshopify.com
SHOPIFY_STOREFRONT_TOKEN=your-storefront-access-token
```

**Install and run:**
```bash
cd src/shopify && npm install && npx tsx index.ts
```

## Architecture

### OpenAPI Generator (`src/openapi/generator/` -- Python)
- `generate.py` -- CLI entrypoint; loads OpenAPI spec + template, writes manifest, calls assembler
- `core.py` -- `make_all_tools()` orchestrates the loop over template tool definitions
- `llm.py` -- `call_gpt()` sends system+user prompt to GPT-4o, returns JSON
- `prompts.py` -- injects OpenAPI spec and base URL into the GPT prompt
- `models.py` -- Pydantic models: `GeneratedTool`, `ToolsManifest`

### Assembler (`src/openapi/assembler/` -- TypeScript)
- `src/index.ts` -- reads `tools_manifest.json`, renders Handlebars templates, writes output files
- Pure transformation: no LLM calls, runs in milliseconds, re-runnable

### Templates (`templates/` -- shared)
- `products.json` -- template definition: system prompt, tool specs (name/description/output schema)
- `mcp_server/server.hbs` -- Handlebars scaffold; GPT-generated tool code is injected here
- `ui/carousel.html` -- dark-theme product carousel (communicates via `postMessage`)

### Shopify Demo (`src/shopify/` -- TypeScript)
- `index.ts` -- MCP server that queries Shopify Storefront API and returns products as carousel data
- `carousel.html` -- the carousel UI (same dark-theme design as the OpenAPI path)
- Requires `SHOPIFY_STORE_DOMAIN` and `SHOPIFY_STOREFRONT_TOKEN` env vars

### Demo API (`demo_api/` -- Python/FastAPI)
- Paginated product list, keyword search, single-product lookup
- Loads from `demo_api/data/products.json`
- `demo_api.yaml` -- OpenAPI 3.0 spec (usable as generator input)

### Generated Server (`src/openapi/generated_server/` -- git-ignored)
Recreated on each pipeline run. Contains: `index.ts`, `carousel.html`, `package.json`, `tsconfig.json`

## Key Design Decisions

- **GPT writes only tool logic** -- the function body that calls the API and maps the response. All MCP plumbing, UI wiring, and transport setup come from templates.
- **Base URLs are hardcoded** in generated functions (from `servers[0].url` in the OpenAPI spec). No runtime env config in the generated server.
- **Output schema is enforced** -- templates define the exact shape GPT must return. Missing fields return empty strings; prices formatted as `"$29.99"`.
- **Carousel UI data flow** -- handles three message formats (direct, MCP method, tool result) for flexibility across MCP host environments.
- **Templates are repo-root level** -- `templates/` is a top-level directory, not buried inside a pipeline-specific folder, because templates are shared across both paths and extended in Phase 2.

## Adding a New Tool Type

1. Create a new template JSON in `templates/` with `system_prompt`, `tools[]`, and `ui_template`
2. Add a matching UI HTML in `templates/ui/`
3. No Python or assembler code changes needed

## VS Code MCP Integration

`.vscode/mcp.json` points to `src/openapi/generated_server/` for local debugging via MCP Inspector.
