# Base55

Base55 generates ready-to-deploy MCP (Model Context Protocol) servers with a visual product carousel UI. Open the web wizard, choose an OpenAPI spec or Shopify store, pick a color theme, and download a working Python MCP server you can connect to Claude.

**Two integration paths:**
- **OpenAPI** — Provide any OpenAPI spec URL. GPT-4o generates Python tool functions; the backend assembles them into a complete MCP server.
- **Shopify** — Pre-built MCP server. Enter your store domain and Storefront token; the wizard produces a configured server instantly (no GPT call).

---

## Prerequisites

- Python 3.11+
- An OpenAI API key (OpenAPI path only)

---

## Quick Start

### 1. Install backend dependencies

```bash
pip install -r src/backend/requirements.txt
pip install -r demo_api/requirements.txt   # optional — only needed for local OpenAPI demo
```

### 2. Set your OpenAI API key (OpenAPI path only)

```bash
export OPENAI_API_KEY=sk-...
```

### 3. Start the backend

```bash
uvicorn src.backend.server:app --port 3001
```

The backend runs at `http://localhost:3001`.

### 4. Open the wizard

Open `src/wizard/index.html` in your browser (double-click the file or use a `file://` URL).

The wizard talks to `http://localhost:3001` automatically.

### 5. Generate your MCP server

Follow the wizard steps:
1. Choose **OpenAPI** or **Shopify**
2. Pick a UI template (Dark Carousel, Light Carousel, or Dark Grid)
3. Customize colors
4. Enter credentials (spec URL for OpenAPI, or store domain + token for Shopify)
5. Click **Generate** and download `server.zip`

### 6. Run the generated server

```bash
unzip server.zip -d my-mcp-server
cd my-mcp-server
pip install -r requirements.txt
python server.py
```

### 7. Connect to Claude

Add to your `claude_desktop_config.json` (find it at `~/Library/Application Support/Claude/` on macOS or `%APPDATA%\Claude\` on Windows):

```json
{
  "mcpServers": {
    "base55": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/absolute/path/to/my-mcp-server"
    }
  }
}
```

Restart Claude Desktop. The MCP server appears in Claude's tool list.

---

## OpenAPI Path Details

The OpenAPI path uses GPT-4o to generate Python tool functions from any OpenAPI spec.

### Local demo API (optional)

A FastAPI demo commerce API is included as a convenient OpenAPI source for testing:

```bash
uvicorn demo_api.main:app --host 127.0.0.1 --port 8001
```

OpenAPI spec: `http://127.0.0.1:8001/openapi.json`

Use this URL in the wizard's spec URL field.

---

## Shopify Path Details

No GPT call is made. The wizard takes your store domain and Storefront token and renders a Python MCP server directly.

**To get a Storefront Access Token:** Shopify Admin → Apps → Develop apps → Create an app → Storefront API access → enable `unauthenticated_read_product_listings`.

The generated `server.py` hardcodes your credentials. Keep the zip private.

---

## Architecture

```
Wizard (src/wizard/index.html)
        │
        │  POST /generate/openapi or /generate/shopify
        ▼
Backend (src/backend/server.py, port 3001)
        │
        ├── OpenAPI path: fetch spec → GPT-4o → tool functions → Jinja2 render
        └── Shopify path: Jinja2 render (no GPT)
        │
        ▼  server.zip
┌──────────────────────┐
│ server.py            │  ← Python/FastMCP MCP server
│ requirements.txt     │  ← fastmcp, httpx
│ {template}.html      │  ← color-customized carousel UI
└──────────────────────┘
        │
        │  python server.py  (stdio transport)
        ▼
Claude Desktop (MCP host)
```

### UI Templates

| Template | File | Description |
|----------|------|-------------|
| Dark Carousel | `templates/ui/carousel.html` | Dark-theme horizontal product scroll |
| Light Carousel | `templates/ui/carousel-light.html` | Light-theme horizontal scroll |
| Dark Grid | `templates/ui/grid-dark.html` | Dark compact 2-3 column grid |

All templates use `--primary-color`, `--accent-color`, and `--bg-color` CSS variables.

---

## Repository Layout

```
src/
  backend/          Python FastAPI backend (generation endpoints)
  wizard/           Web setup wizard (index.html — open in browser)
  openapi/
    generator/      Python: GPT-4o tool generation (used by backend)
    assembler/      TypeScript: legacy Handlebars assembler (not used by wizard)
  shopify/          TypeScript: standalone Shopify MCP server demo
templates/
  mcp_server/       Jinja2 templates for generated server.py files
  ui/               HTML carousel and grid UI templates
  products.json     Tool spec definition for the OpenAPI generator
demo_api/           FastAPI demo commerce API (example OpenAPI source)
docs/               Project documents and meeting notes
```

---

## Debugging

**MCP Inspector** — inspect any running MCP server:

```bash
npx @modelcontextprotocol/inspector
```

**Backend logs** — the `uvicorn` process prints request logs. Check here if generation fails.

**Wizard error** — if generation fails, the wizard shows the backend error message in-line. Common causes:
- Backend not running (`uvicorn src.backend.server:app --port 3001`)
- Invalid spec URL (must be reachable from the backend process)
- Missing `OPENAI_API_KEY` for the OpenAPI path
