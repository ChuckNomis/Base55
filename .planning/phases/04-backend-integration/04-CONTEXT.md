# Phase 4: Backend Integration - Context

**Gathered:** 2026-05-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Build a FastAPI (Python) backend server that accepts wizard submissions, drives both generation pipelines, and returns downloadable zip files containing ready-to-run Python/FastMCP MCP servers. Covers: the backend routes, a Python rewrite of the assembler (replacing the TypeScript Handlebars assembler), color injection into selected templates, and Jinja2 templates for both OpenAPI and Shopify generated servers.

The backend lives at `src/backend/server.py`. It exposes:
- `POST /generate/openapi` — accepts spec URL + template + colors, runs the Python generator pipeline, returns a zip
- `POST /generate/shopify` — accepts store domain + storefront token + template + colors, generates a Shopify FastMCP server from template, returns a zip

Both endpoints return binary `.zip` responses. The wizard at `http://localhost:3001` is already wired to call these (hardcoded from Phase 3).

</domain>

<decisions>
## Implementation Decisions

### Backend Technology

- **D-01:** Backend server is **FastAPI (Python)** at `src/backend/server.py`. Runs at `http://localhost:3001`. All server-side generation logic is Python — no Node.js process needed on the backend.
- **D-02:** The TypeScript assembler (`src/openapi/assembler/`) is **rewritten in Python** using Jinja2. The Handlebars `server.hbs` template will be replaced with a Jinja2 equivalent. The TypeScript assembler is effectively retired.
- **D-03:** Generated MCP servers (both OpenAPI and Shopify outputs) are **Python/FastMCP** servers — not TypeScript. Users unzip and run a Python server.

### Generated Server Technology

- **D-04:** Generated servers use **FastMCP** as the MCP framework. The mcp-ui Python package (`mcp-ui` / pip) handles carousel HTML serving inside Claude — mirrors the JS `@mcp-ui/server` API. Researcher must verify the Python `mcp-ui` package exists and confirm the `createUIResource` equivalent API.
- **D-05:** The generated server Jinja2 template lives in `templates/mcp_server/server.py.jinja2` (new file, replaces `server.hbs`).

### OpenAPI Generation Flow

- **D-06:** Generation is **synchronous** — `POST /generate/openapi` waits for the full GPT-4o call + Python assembly to complete, then returns the zip. No job queue, no polling. The wizard spinner already handles up to 30s.
- **D-07:** `OPENAI_API_KEY` is read from a `.env` file on the backend server at startup. The key is never sent through the wizard UI. User sets it once before running the backend.

### Shopify Package Structure

- **D-08:** Shopify output is a **fresh Python/FastMCP server generated from a Jinja2 template** — not a copy of the existing TypeScript `src/shopify/` server. Consistent with the OpenAPI path.
- **D-09:** Shopify credentials (store domain + storefront token) are **hardcoded as Python constants** at the top of the generated `server.py`. Simple, works immediately after unzip + `pip install` + run. No extra `.env` setup for the end user.

### Template + Color Injection

- **D-10:** Colors are injected into the selected HTML template by **prepending a `<style>:root{}</style>` block** right after `<head>`. This is the same approach used in Phase 2 (CONTEXT D-08) for live preview. The Python assembler owns this step — it reads the HTML file, prepends the color block, writes the color-injected HTML into the output zip.
- **D-11:** The selected template name (carousel / carousel-light / grid-dark) is passed to the Python assembler, which reads from `templates/ui/{template-name}.html`.

### Claude's Discretion

- Exact Python package name for the FastMCP `mcp-ui` integration (to be confirmed by researcher)
- The Jinja2 template structure for the generated `server.py` (analogous to the existing `server.hbs`)
- Whether the backend itself uses `python-dotenv` for its own OPENAI_API_KEY loading
- Port binding (3001) and CORS headers for the wizard's fetch calls (same origin or explicit Allow)
- Error response format when GPT-4o call fails or Shopify credentials are invalid

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase Requirements
- `.planning/REQUIREMENTS.md` — BE-01, BE-02, BE-03 are the 3 requirements for this phase
- `.planning/ROADMAP.md` — Phase 4 success criteria and plan breakdown (PLAN-4a, 4b, 4c)

### Prior Phase Decisions (carried forward)
- `.planning/phases/03-web-setup-wizard/03-CONTEXT.md` — D-08 (backend POST URLs and request body shape), D-09 (spinner UX), D-10 (zip download via blob). The backend must match these contracts exactly.
- `.planning/phases/02-ui-templates/02-CONTEXT.md` — D-03 (3 CSS variables), D-08 (color injection via `<style>:root{}` prepend). The assembler must use this exact approach.

### Existing Pipeline Code (read before planning)
- `src/openapi/generator/generate.py` — existing CLI entrypoint; shows how the generator is invoked and what it produces (tools_manifest.json → assembled output dir)
- `src/openapi/generator/core.py` — `make_all_tools()` function; the Python assembler will call this directly (same process, no subprocess)
- `src/openapi/assembler/src/index.ts` — the TypeScript assembler being replaced; read to understand what output files it produces (index.ts, carousel.html, package.json, tsconfig.json)
- `src/shopify/index.ts` — the reference Shopify MCP server implementation; the Python Jinja2 template must produce an equivalent Python server

### UI Templates (selected by user in wizard, injected into output)
- `templates/ui/carousel.html` — dark carousel; option "carousel"
- `templates/ui/carousel-light.html` — light carousel; option "carousel-light"
- `templates/ui/grid-dark.html` — dark compact grid; option "grid-dark"

### MCP Server Template (to be rewritten)
- `templates/mcp_server/server.hbs` — existing Handlebars template being replaced; read to understand the structure before writing the Jinja2 equivalent

### Project Context
- `.planning/PROJECT.md` — Key Decisions table and project goals

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/openapi/generator/core.py` — `make_all_tools(openapi_spec, template)` → returns a `ToolsManifest`. The Python backend imports and calls this directly (no subprocess).
- `templates/ui/*.html` — all 3 templates already use `--primary-color`, `--accent-color`, `--bg-color` CSS variables. Color injection is a simple string prepend.
- `templates/mcp_server/server.hbs` — structural reference for what the generated server scaffold looks like; convert to Jinja2 with `{% for tool in tools %}` syntax.

### Established Patterns
- FastAPI is already in the codebase (`demo_api/main.py`) — reuse that pattern (FastAPI app, uvicorn, returning `Response` with binary content).
- Python generator already uses `pathlib.Path` and `tempfile` patterns — follow the same style.
- All templates communicate via `postMessage` for carousel data; the generated Python server must embed the carousel HTML and serve it the same way.

### Integration Points
- The wizard's `fetch()` calls land at `http://localhost:3001/generate/openapi` and `http://localhost:3001/generate/shopify` (hardcoded from Phase 3). The backend must match these paths exactly.
- CORS: wizard is opened as a local HTML file (file:// or localhost:xxxx) — backend needs `allow_origins=["*"]` or equivalent for the wizard's fetch calls to succeed.
- The zip response triggers the wizard's `URL.createObjectURL(blob)` + hidden `<a>` click pattern. Backend must return `Content-Disposition: attachment; filename="server.zip"` with the correct MIME type.
- The Python assembler replaces `src/openapi/assembler/` — the old TypeScript assembler and its `npm run build` step are no longer needed for the pipeline.

</code_context>

<specifics>
## Specific Ideas

- User explicitly wants everything in Python end-to-end: backend (FastAPI), pipeline logic, and generated server output (FastMCP). The TypeScript assembler is being retired in this phase.
- Generated servers should be simple enough for a course demo: single `server.py` file + `requirements.txt` + the chosen HTML template file. User unzips, runs `pip install -r requirements.txt`, then `python server.py`.
- The Shopify generated server should mirror the existing TypeScript one in behavior: takes a search query, calls Shopify Storefront API, returns products as a carousel.

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope.

</deferred>

---

*Phase: 4-Backend Integration*
*Context gathered: 2026-05-08*
