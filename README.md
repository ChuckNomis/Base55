# Base55

Base55 generates ready-to-deploy MCP (Model Context Protocol) servers with visual product carousel UI. Give it an OpenAPI spec or a Shopify store and it produces a working MCP server you can connect to Claude or any MCP-compatible host.

**Two integration paths:**
- **OpenAPI path** — Provide any OpenAPI spec URL. GPT-4o generates TypeScript tool functions; a Handlebars assembler packages them into a complete MCP server.
- **Shopify path** — Pre-built MCP server that connects to the Shopify Storefront API. Configure your store credentials and run.

---

## Prerequisites

- Python 3.11+
- Node.js 18+
- An OpenAI API key (for the OpenAPI path only)

---

## Setup

```bash
# Python dependencies
pip install -r src/openapi/generator/requirements.txt
pip install -r demo_api/requirements.txt

# Build the TypeScript assembler
cd src/openapi/assembler && npm install && npm run build && cd ../../..
```

---

## Running the OpenAPI Pipeline

The OpenAPI path takes any OpenAPI spec and generates a complete MCP server.

### 1. Start the demo commerce API

A local FastAPI server is included as an example OpenAPI source:

```bash
uvicorn demo_api.main:app --host 127.0.0.1 --port 8001
```

OpenAPI spec is served at `http://127.0.0.1:8001/openapi.json`

### 2. Generate the MCP server

```bash
export OPENAI_API_KEY=sk-...

python -m src.openapi.generator.generate \
  --openapi http://127.0.0.1:8001/openapi.json \
  --template templates/products.json \
  --output-dir src/openapi/generated_server/
```

This calls GPT-4o to write the tool functions, then assembles them into `src/openapi/generated_server/`.

You can also point `--openapi` at any publicly accessible OpenAPI JSON URL.

### 3. Run the generated server

```bash
cd src/openapi/generated_server && npm install && npm start
```

### 4. Connect to Claude (optional)

Add to your Claude MCP config:

```json
{
  "mcpServers": {
    "base55": {
      "command": "npx",
      "args": ["tsx", "index.ts"],
      "cwd": "/path/to/src/openapi/generated_server"
    }
  }
}
```

---

## Running the Shopify Demo

The Shopify path is a standalone MCP server that connects to the Shopify Storefront API.

### 1. Configure credentials

Create `src/shopify/.env`:

```
SHOPIFY_STORE_DOMAIN=your-store.myshopify.com
SHOPIFY_STOREFRONT_TOKEN=your-storefront-access-token
```

To get a Storefront Access Token: Shopify Admin → Apps → Develop apps → Create an app → Storefront API access → enable `unauthenticated_read_product_listings`.

### 2. Install and run

```bash
cd src/shopify && npm install && npx tsx index.ts
```

### 3. Connect to Claude (optional)

```json
{
  "mcpServers": {
    "shopify": {
      "command": "npx",
      "args": ["tsx", "index.ts"],
      "cwd": "/path/to/src/shopify"
    }
  }
}
```

---

## Architecture

```
OpenAPI Pipeline
────────────────
OpenAPI spec (URL or file)
        │
        ▼
  src/openapi/generator/   ← Python; calls GPT-4o
  (generate.py, core.py,
   llm.py, prompts.py)
        │
        │  tools_manifest.json
        ▼
  src/openapi/assembler/   ← TypeScript; Handlebars render
  (src/index.ts)
        │
        ├── index.ts        (MCP server with generated tools)
        ├── carousel.html   (product carousel UI)
        ├── package.json
        └── tsconfig.json
        │
        ▼
  src/openapi/generated_server/   ← ready to run


Shopify Pipeline
────────────────
Shopify Storefront API
        │
        ▼
  src/shopify/index.ts     ← TypeScript MCP server
  (Storefront GraphQL)
        │
        ▼
  carousel.html            ← product carousel UI
```

---

## Repository Layout

```
src/
  openapi/
    generator/      Python: GPT-4o tool generation
    assembler/      TypeScript: Handlebars-based MCP server assembly
    generated_server/  (git-ignored) pipeline output
  shopify/          TypeScript: Shopify Storefront MCP server
  wizard/           (coming in Phase 3) web setup wizard
templates/
  products.json           template definition (system prompt + tool specs)
  mcp_server/server.hbs   Handlebars scaffold for generated server
  ui/carousel.html        dark-theme product carousel UI
demo_api/           FastAPI demo commerce API (example OpenAPI source)
docs/               project documents and meeting notes
```

---

## Debugging

**MCP Inspector** — connect to any running MCP server:
```bash
npx @modelcontextprotocol/inspector
```

**VS Code** — `.vscode/mcp.json` is pre-configured to connect to `src/openapi/generated_server/` for local debugging.
