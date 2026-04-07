# dev/ — Base55 Generator & MCP Server Pipeline

This directory contains the core generation pipeline that turns any OpenAPI spec into a deployable TypeScript MCP server with a rich product carousel UI.

---

## How it works

```
OpenAPI spec  +  template.json
        │
        ▼
  ┌─────────────┐
  │  generator/ │  Python — calls GPT-4o, gets back a TypeScript tool function
  └──────┬──────┘
         │  tools_manifest.json
         ▼
  ┌─────────────┐
  │  assembler/ │  TypeScript/Node.js — renders Handlebars template into final MCP server
  └──────┬──────┘
         │
         ▼
  generated_server/   ← ready to run with `npm start`
```

**Key idea:** templates are fully predefined. The UI, output schema, and MCP wiring are all fixed. GPT's only job is to read the OpenAPI spec, find the right endpoint, and write the adapter function that maps the API response to the template's expected data shape.

---

## Directory structure

```
dev/
├── generator/          Python package — generation logic
│   ├── core.py         make_all_tools(): orchestrates the generation loop
│   ├── llm.py          call_gpt(): OpenAI GPT-4o wrapper (json_object response format)
│   ├── prompts.py      build_user_prompt(): injects OpenAPI spec + base URL into prompt
│   ├── models.py       Pydantic models: GeneratedTool, ToolsManifest
│   ├── generate.py     CLI entrypoint (also triggers the assembler)
│   └── requirements.txt
│
├── templates/          Predefined tool templates and UI assets
│   ├── products.json   The "products" template — system prompt, tool def, output schema
│   ├── mcp_server/
│   │   └── server.hbs  Handlebars master template → produces the final index.ts
│   └── ui/
│       └── carousel.html  Dynamic product carousel HTML (MCP Apps UI)
│
├── assembler/          TypeScript/Node.js — assembles manifest into server files
│   ├── src/index.ts    Reads manifest, renders server.hbs, writes output files
│   ├── package.json
│   ├── tsconfig.json
│   └── dist/           Compiled output (run `npm run build` to regenerate)
│
└── generated_server/   Output directory (git-ignored) — created when you run the pipeline
    ├── index.ts        The generated MCP server
    ├── carousel.html   Copied UI asset
    ├── package.json    Dependencies for the generated server
    └── tools_manifest.json  Intermediate artifact from the generator
```

---

## Setup

**Prerequisites:** Python 3.10+, Node.js 18+, an OpenAI API key, and the shared `.venv` activated.

```bash
# From the repo root — install Python deps
pip install -r dev/generator/requirements.txt

# Build the assembler (only needed once, or after editing assembler/src/)
cd dev/assembler && npm install && npm run build && cd ../..
```

---

## Running the pipeline

### Step 1 — Start the demo API

```bash
uvicorn demo_api.main:app --host 127.0.0.1 --port 8001
```

### Step 2 — Generate the MCP server

```bash
export OPENAI_API_KEY=sk-...

python -m dev.generator.generate \
  --openapi http://127.0.0.1:8001/openapi.json \
  --template dev/templates/products.json \
  --output-dir dev/generated_server/
```

This does two things:
1. Calls GPT-4o to generate the TypeScript tool function → saves `tools_manifest.json`
2. Runs the assembler to produce the complete `generated_server/`

### Step 3 — Run the generated server

```bash
cd dev/generated_server
npm install
npm start
```

### Step 4 — Verify with MCP Inspector

```bash
npx @modelcontextprotocol/inspector
```

Connect to the running server and call `search_products` with a query like `"widget"`.

---

## Templates

A template defines everything about a tool type except the API-specific logic. It has three parts:

| Part | What it is |
|---|---|
| `system_prompt` | Sent to GPT as the system message. Defines the fixed output schema and generation rules. |
| `tools[]` | List of tools to generate. Each has a name, description, and `output_schema`. |
| `ui_template` | Which UI asset to use (e.g., `"carousel"` → `templates/ui/carousel.html`). |

### The products template (`templates/products.json`)

Generates a `search_products(query: string)` function that returns:

```json
{
  "products": [
    {
      "id": "string",
      "title": "string",
      "price": "string",
      "image_url": "string",
      "description": "string",
      "link": "string"
    }
  ]
}
```

GPT reads the provided OpenAPI spec, identifies the best search/list endpoint, and writes the adapter function. The base URL from `servers[0].url` in the spec is hardcoded directly into the generated function — no `.env` needed.

---

## The carousel UI (`templates/ui/carousel.html`)

A standalone dark-theme product carousel that:
- Sends `ui/initialize` and `ui/notifications/initialized` to the MCP host on load (MCP Apps protocol)
- Listens for product data via `window.addEventListener('message', ...)` and renders cards dynamically
- Each card shows: product image, title, price, description, and a VIEW link button

Data can arrive from the host in any of these formats:
```js
{ products: [...] }                        // direct
{ method: 'ui/data', params: { products: [...] } }   // MCP method
{ result: { content: [{ type: 'text', text: '{"products":[...]}' }] } }  // tool result
```

---

## The assembler (`assembler/`)

A small Node.js script that takes the generator's output (`tools_manifest.json`) and produces a complete, runnable MCP server directory.

**Input:** `tools_manifest.json`
```json
{
  "tools": [
    { "name": "search_products", "description": "...", "code": "async function search_products(...) { ... }" }
  ]
}
```

**Output files written to the target directory:**
- `index.ts` — the MCP server (rendered from `server.hbs`)
- `carousel.html` — the UI asset
- `package.json` — dependencies (`@modelcontextprotocol/sdk`, `@mcp-ui/server`, `@modelcontextprotocol/ext-apps`, `zod`)
- `tsconfig.json`

The assembler is a Handlebars render step — it is deterministic, has no LLM calls, and runs in milliseconds.

**Rebuild after editing `assembler/src/index.ts`:**
```bash
cd dev/assembler && npm run build
```

---

## Adding a new template

1. Create `dev/templates/<name>.json` with `system_prompt`, `tools[]`, and `ui_template`
2. Add a corresponding UI HTML file to `dev/templates/ui/<name>.html`
3. Update `server.hbs` if the new template needs a different UI registration pattern
4. Run the generator with `--template dev/templates/<name>.json`

No changes to the Python generator code are needed — it is template-agnostic.
