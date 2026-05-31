# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

**Base55** is a web-based wizard that generates ready-to-deploy MCP (Model Context Protocol) servers with visual UI. Users choose a data source (OpenAPI spec or Shopify store), pick a UI template, and receive a working MCP server that renders interactive carousels inside AI hosts like Claude.

Two integration paths exist today:

1. **OpenAPI path** -- Takes any OpenAPI spec URL, uses GPT-4o to generate Python tool functions, then assembles them via Jinja2 into a complete FastMCP server (returned as a zip).
2. **Shopify path** -- No GPT call. The wizard takes store credentials and renders a configured FastMCP server directly via Jinja2.

```
OpenAPI spec -> GPT-4o -> Python tool functions -> Jinja2 render -> server.zip (FastMCP)
Shopify creds                                    -> Jinja2 render -> server.zip (FastMCP)
```

## Repository Structure

```
src/
  backend/
    server.py         # FastAPI backend (port 3001) — /generate/openapi and /generate/shopify
    requirements.txt  # fastapi, uvicorn, jinja2, httpx, pydantic, python-dotenv, openai
  wizard/
    index.html        # Web wizard UI (vanilla HTML/CSS/JS — open directly in browser)
  openapi/
    generator/        # Python: calls GPT-4o to generate tool functions from OpenAPI spec
      generate.py     # CLI entrypoint (not used by wizard; backend calls core.py directly)
      core.py         # make_all_tools() orchestrates tool generation loop
      llm.py          # call_gpt() sends prompts to GPT-4o, returns JSON
      prompts.py      # injects OpenAPI spec and base URL into GPT prompt
      models.py       # Pydantic models: GeneratedTool, ToolsManifest
    assembler/        # Legacy TypeScript Handlebars assembler — NOT used by current wizard
  shopify/            # Legacy standalone TypeScript Shopify MCP demo — NOT used by wizard
templates/
  mcp_server/
    server.py.jinja2         # Jinja2 scaffold for OpenAPI-path generated server.py
    shopify_server.py.jinja2 # Jinja2 scaffold for Shopify-path generated server.py
  ui/
    carousel.html       # Dark-theme horizontal product carousel
    carousel-light.html # Light-theme horizontal product carousel
    grid-dark.html      # Dark compact 2-3 column grid
  products.json         # Tool spec definition: system prompt + tool specs for GPT
demo_api/              # FastAPI demo commerce API (example OpenAPI source for testing)
result/                # Example generated server output (for reference)
docs/                  # Project documents and meeting notes
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn (port 3001) |
| LLM integration | OpenAI SDK, GPT-4o |
| Templating | Jinja2 (`.jinja2` files → Python servers) |
| HTTP client | httpx (async) |
| Data validation | Pydantic v2 |
| Env config | python-dotenv |
| Wizard frontend | Vanilla HTML/CSS/JS (no build step) |
| Generated servers | Python, FastMCP ≥3.2.4, httpx |
| Demo API | Python, FastAPI (port 8001) |
| Carousel UI | Pure HTML/CSS (CSS custom properties for theming) |

**No TypeScript or Node.js is in active use.** The legacy `src/openapi/assembler/` (Handlebars/TS) and `src/shopify/` (TS) directories are superseded by the Python/Jinja2 pipeline.

## Setup

```bash
# Backend dependencies
pip install -r src/backend/requirements.txt

# Optional: demo API (only needed for local OpenAPI testing)
pip install -r demo_api/requirements.txt
```

Requires an `OPENAI_API_KEY` env var for the OpenAPI path.

## Running the Wizard

**1. Start the backend:**
```bash
uvicorn src.backend.server:app --port 3001
```

**2. Open the wizard:**
Open `src/wizard/index.html` in your browser (double-click or `file://` URL).

**3. (Optional) Start the demo commerce API for OpenAPI testing:**
```bash
uvicorn demo_api.main:app --host 127.0.0.1 --port 8001
```
OpenAPI spec available at `http://127.0.0.1:8001/openapi.json`

## Architecture

### Backend (`src/backend/server.py` — FastAPI)
- `POST /generate/openapi` — fetches OpenAPI spec, calls GPT-4o via `make_all_tools()`, renders `server.py.jinja2`, returns `server.zip`
- `POST /generate/shopify` — renders `shopify_server.py.jinja2` with credentials, returns `server.zip`
- Color injection: injects CSS custom properties into the selected UI HTML before zipping
- Pydantic validators block template injection in color fields

### OpenAPI Generator (`src/openapi/generator/` — Python)
- `core.py` — `make_all_tools()` loops over tool specs from `products.json`, calls GPT-4o for each
- `llm.py` — `call_gpt()` sends system+user prompt to GPT-4o (`gpt-4o`), returns JSON
- `prompts.py` — injects OpenAPI spec and base URL into the GPT prompt
- `models.py` — Pydantic models: `GeneratedTool`, `ToolsManifest`

### Templates (`templates/`)
- `products.json` — tool spec definition: system prompt, tool names/descriptions/output schemas
- `mcp_server/server.py.jinja2` — Jinja2 scaffold; GPT-generated tool functions injected here
- `mcp_server/shopify_server.py.jinja2` — Jinja2 scaffold for Shopify path (no GPT)
- `ui/*.html` — carousel and grid UI templates with CSS custom property theming

### Generated Server Output
Each generated zip contains:
- `server.py` — Python/FastMCP MCP server (stdio transport)
- `requirements.txt` — `fastmcp>=3.2.4`, `httpx>=0.27.0`
- `{template}.html` — color-customized carousel/grid UI

### Wizard Frontend (`src/wizard/index.html`)
- Pure HTML/CSS/JS, no npm or build step
- Step-by-step flow: intro → integration type → template → colors → credentials → download
- Talks to `http://localhost:3001` via POST requests
- Handles file download of `server.zip` directly in browser

### Demo API (`demo_api/` — Python/FastAPI)
- Paginated product list, keyword search, single-product lookup
- Loads from `demo_api/data/products.json`
- `demo_api.yaml` — OpenAPI 3.0 spec (usable as generator input in the wizard)

## Key Design Decisions

- **GPT writes only tool logic** — the function body that calls the API and maps the response. All MCP plumbing, UI wiring, and transport setup come from Jinja2 templates.
- **Base URLs are hardcoded** in generated functions (from `servers[0].url` in the OpenAPI spec). No runtime env config in the generated server.
- **Output schema is enforced** — `products.json` defines the exact shape GPT must return. Missing fields return empty strings; prices formatted as `"$29.99"`.
- **Carousel UI data flow** — handles three message formats (direct, MCP method, tool result) for flexibility across MCP host environments.
- **Jinja2 over Handlebars** — the original TypeScript/Handlebars assembler was replaced with Python/Jinja2 to keep the entire pipeline in one language.
- **No-build wizard** — the frontend is a single HTML file opened directly in the browser; no npm, webpack, or build step required.

## Adding a New UI Template

1. Add a new HTML file to `templates/ui/` using CSS custom properties (`--primary-color`, `--accent-color`, `--bg-color`)
2. Add the template name (without `.html`) to `ALLOWED_TEMPLATES` in `src/backend/server.py`
3. Add the option to the wizard UI in `src/wizard/index.html`

## Adding a New Integration Path

1. Create a new Jinja2 template in `templates/mcp_server/`
2. Add a new Pydantic request model and endpoint in `src/backend/server.py`
3. Add the wizard steps in `src/wizard/index.html`

## Debugging

**MCP Inspector** — inspect any running FastMCP server:
```bash
npx @modelcontextprotocol/inspector
```

**Backend logs** — `uvicorn` prints request logs; check here if generation fails.

**Wizard errors** — shown inline in the wizard UI. Common causes:
- Backend not running (`uvicorn src.backend.server:app --port 3001`)
- Invalid spec URL (must be reachable from the backend process)
- Missing `OPENAI_API_KEY` for the OpenAPI path
