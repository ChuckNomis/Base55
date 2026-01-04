---
name: Full system self-check
overview: Step-by-step Windows PowerShell runbook to validate demo_api, tool generation, MCP server, and optional ngrok/ChatGPT connector integration.
todos:
  - id: setup-venv
    content: Create/activate venv and install demo_api + mcp_server (and optionally POC) dependencies.
    status: pending
  - id: run-api
    content: Start demo_api with uvicorn and confirm health, products, search, and openapi endpoints respond.
    status: pending
    dependencies:
      - setup-venv
  - id: generate-tool
    content: Run POC generator against live openapi.json and verify generated/search_products.py meets function-only requirements.
    status: pending
    dependencies:
      - run-api
  - id: run-tool-direct
    content: Execute the generated async search_products function directly against the running API.
    status: pending
    dependencies:
      - generate-tool
  - id: run-mcp
    content: Start mcp_server and confirm it exposes /mcp and the search_products tool delegates correctly.
    status: pending
    dependencies:
      - run-tool-direct
  - id: verify-mcp
    content: Use MCP Inspector to list/invoke tools and validate end-to-end output.
    status: pending
    dependencies:
      - run-mcp
  - id: ngrok-chatgpt
    content: Optionally expose MCP via ngrok and configure ChatGPT connector URL, then test tool invocation.
    status: pending
    dependencies:
      - verify-mcp
---

# End-to-end self-check runbook (Windows PowerShell)

## Goal

Validate the entire stack in this repo:

- Demo API: [`demo_api/main.py`](c:\Users\nadav\Documents\GitHub\Base55\demo_api\main.py)
- Tool generation: [`POC/poc_generate.py`](c:\Users\nadav\Documents\GitHub\Base55\POC\poc_generate.py)
- Generated tool: [`generated/search_products.py`](c:\Users\nadav\Documents\GitHub\Base55\generated\search_products.py)
- MCP server: [`mcp_server/main.py`](c:\Users\nadav\Documents\GitHub\Base55\mcp_server\main.py)

## 0) One-time setup (venv + deps)

From repo root:

```powershell
Set-Location "C:\Users\nadav\Documents\GitHub\Base55"

# Create venv (skip if you already have .venv)
python -m venv .venv

# Activate venv
.\.venv\Scripts\Activate.ps1

# Install deps for API + MCP server
pip install -r demo_api/requirements.txt -r mcp_server/requirements.txt

# (Optional) deps for generator
pip install -r POC/requirements.txt
```

Quick sanity:

```powershell
python -c "import fastapi, uvicorn, httpx; print('deps_ok')"
python -c "import mcp; print('mcp_ok')"
python -c "import openai; print('openai_ok')"   # only if you installed POC deps
```



## 1) Preflight: confirm ports are free (and how to kill blockers)

This demo defaults to:

- API: `8001`
- MCP: `8000`

Check what’s listening:

```powershell
netstat -ano | findstr ":8001"
netstat -ano | findstr ":8000"
```

If you see a `LISTENING` PID, identify it:

```powershell
tasklist /fi "PID eq <PID>"
```

Kill it (PowerShell-native):

```powershell
Stop-Process -Id <PID> -Force
```

Alternative:

```powershell
taskkill /PID <PID> /F
```



## 2) Run the Demo Commerce API

In repo root, in an activated venv:

```powershell
$env:API_PORT = "8001"   # optional override; demo uses 8001 by default
python -m uvicorn demo_api.main:app --host 127.0.0.1 --port $env:API_PORT --reload
```

Expected:

- Log contains `Uvicorn running on http://127.0.0.1:8001`

### 2a) Smoke test the API (terminal calls)

In a second terminal:

```powershell
# Health
Invoke-RestMethod "http://127.0.0.1:8001/health"

# OpenAPI
Invoke-RestMethod "http://127.0.0.1:8001/openapi.json" | Select-Object -First 1

# List products
Invoke-RestMethod "http://127.0.0.1:8001/v1/products?limit=3"

# Search
Invoke-RestMethod "http://127.0.0.1:8001/v1/products/search?q=widget&limit=5"
```

What to look for:

- `/health` returns `{"status":"ok"}`
- `/openapi.json` includes `"title": "Demo Commerce API"` (see `FastAPI(title=...)` in [`demo_api/main.py`](c:\Users\nadav\Documents\GitHub\Base55\demo_api\main.py))

## 3) Generate the tool from OpenAPI (POC)

Only needed if you want to regenerate [`generated/search_products.py`](c:\Users\nadav\Documents\GitHub\Base55\generated\search_products.py).Set your key for the session:

```powershell
$env:OPENAI_API_KEY = "sk-..."
```

Generate into `generated/`:

```powershell
python POC/poc_generate.py --template POC/template_products.json --openapi http://127.0.0.1:8001/openapi.json --output-dir generated
```



### 3a) Validate the generated file is “function-only” (code checks)

The generator enforces “no server wiring” (see `validate_tool_function_only()` in [`POC/poc_generate.py`](c:\Users\nadav\Documents\GitHub\Base55\POC\poc_generate.py)). Verify via grep-like checks:

```powershell
# Must NOT exist
Select-String -Path generated/search_products.py -Pattern "@mcp\.tool","FastMCP","mcp\s*="

# Must exist
Select-String -Path generated/search_products.py -Pattern "DEMO_API_BASE_URL","async def search_products"
```



### 3b) Execute the generated tool directly (terminal call)

With the API still running:

```powershell
$env:DEMO_API_BASE_URL = "http://127.0.0.1:8001"
python -c "import asyncio; from generated.search_products import search_products; print(asyncio.run(search_products('widget')))"
```

Expected: printed JSON-like dict with `products: [...]`.

## 4) Run the MCP server

In repo root (new terminal), with venv active:

```powershell
$env:DEMO_API_BASE_URL = "http://127.0.0.1:8001"  # must point at the API
$env:MCP_PORT = "8000"                             # optional override
python -m mcp_server.main
```

Expected:

- Server binds to `$env:MCP_PORT`
- MCP endpoint is `http://127.0.0.1:8000/mcp` (per [`mcp_server/main.py`](c:\Users\nadav\Documents\GitHub\Base55\mcp_server\main.py) and `DEMO.md`)

## 5) Verify MCP is serving tools

### Option A (recommended): MCP Inspector

Requires Node.

```powershell
npx @modelcontextprotocol/inspector http://127.0.0.1:8000/mcp
```

In inspector:

- Confirm a tool named `search_products` exists
- Invoke it with `query = "widget"`

### Option B: direct HTTP POST (quick connectivity check)

If you want to confirm the endpoint is reachable over HTTP:

```powershell
Invoke-WebRequest -Uri "http://127.0.0.1:8000/mcp" -Method OPTIONS -UseBasicParsing
```

(If you want a full JSON-RPC call, tell me which MCP protocol version/shape your inspector expects; Streamable HTTP implementations can differ slightly in payload conventions.)

## 6) Optional: expose MCP via ngrok and connect in ChatGPT

Run ngrok:

```powershell
ngrok http 8000
```

Then:

- Use the HTTPS forwarding URL + `/mcp` as the connector URL, e.g. `https://<id>.ngrok.app/mcp`
- In ChatGPT, test by asking it to call `search_products`.

## 7) Common failure modes + how to diagnose fast

- **Port already in use**: use `netstat -ano | findstr ":<port>"` → `tasklist` → `Stop-Process -Id <PID> -Force`.
- **Tool calls wrong base URL**: ensure `$env:DEMO_API_BASE_URL` is set for MCP and for direct tool runs. The generated tool defaults to `http://127.0.0.1:8001` (see [`generated/search_products.py`](c:\Users\nadav\Documents\GitHub\Base55\generated\search_products.py)), while `DEMO.md` mentions `/v1` but the actual code appends `/v1/...` itself.
- **Module import errors**: confirm you activated the same venv in all terminals and installed both requirement files.
- **API returns empty results**: try a query that matches titles/descriptions in [`demo_api/data/products.json`](c:\Users\nadav\Documents\GitHub\Base55\demo_api\data\products.json).