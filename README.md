# Base55 — Local MCP demo (FastAPI → MCP Streamable HTTP → Inspector)

This repo contains:
- A **Demo Commerce API** (FastAPI) in `demo_api/`
- A **FastMCP server** (Streamable HTTP) in `mcp_server/` that exposes a `search_products` tool backed by the Demo API
- An optional **POC generator** in `POC/` that can regenerate `generated/search_products.py` from OpenAPI

If you want the longer walkthrough (including ngrok + ChatGPT connector), see [`DEMO.md`](DEMO.md).

## Prereqs
- Python 3.10+ (recommended)
- Node.js (for MCP Inspector)

## 0) Setup (one venv for everything)

```powershell
# From repo root:
Set-Location "C:\Users\nadav\Documents\GitHub\Base55"

# Create venv (skip if you already have .venv)
python -m venv .venv

# Activate venv
.\.venv\Scripts\Activate.ps1

# Install API + MCP server deps
pip install -r demo_api/requirements.txt -r mcp_server/requirements.txt

# Optional: install generator deps (only needed if you want to regenerate generated/*)
pip install -r POC/requirements.txt
```

## 1) Run the Demo Commerce API (FastAPI)

```powershell
# Default API port is 8001
$env:API_PORT = "8001"

# Start the API
python -m uvicorn demo_api.main:app --host 127.0.0.1 --port $env:API_PORT --reload
```

Quick checks (run in a second terminal):

```powershell
# Health
Invoke-RestMethod "http://127.0.0.1:8001/health"

# OpenAPI (used for generation)
Invoke-RestMethod "http://127.0.0.1:8001/openapi.json" | Select-Object -First 1

# Search endpoint
Invoke-RestMethod "http://127.0.0.1:8001/v1/products/search?q=widget&limit=5"
```

## 2) (Optional) Regenerate the tool from OpenAPI

Only do this if you want to overwrite `generated/search_products.py`.

```powershell
# Set your OpenAI key for this session
$env:OPENAI_API_KEY = "sk-..."

# Generate tool(s) into ./generated
python POC/poc_generate.py --template POC/template_products.json --openapi http://127.0.0.1:8001/openapi.json --output-dir generated
```

Sanity-check the generated file is **function-only** (no MCP server wiring):

```powershell
# Must NOT exist:
Select-String -Path generated/search_products.py -Pattern "@mcp\.tool","FastMCP","mcp\s*="

# Must exist:
Select-String -Path generated/search_products.py -Pattern "DEMO_API_BASE_URL","async def search_products"
```

## 3) Run the MCP server (Streamable HTTP)

```powershell
# Point the MCP tool at the Demo API
$env:DEMO_API_BASE_URL = "http://127.0.0.1:8001"

# Default MCP port is 8000
$env:MCP_PORT = "8000"

# Start MCP server (Streamable HTTP at /mcp)
python -m mcp_server.main
```

- MCP endpoint: `http://127.0.0.1:8000/mcp`

## 4) Verify MCP using MCP Inspector (recommended)

Run the inspector:

```powershell
npx @modelcontextprotocol/inspector
```

Then:
- Open the URL the command prints (it looks like `http://localhost:<port>/?MCP_PROXY_AUTH_TOKEN=...`)
- In the Inspector UI, select **Streamable HTTP** transport
- Set server URL to: `http://127.0.0.1:8000/mcp`
- Verify there is a tool named **`search_products`**, then invoke it with `query = "widget"`

## Troubleshooting (ports in use)

If you see “only one usage of each socket address…”, find and kill the process holding the port:

```powershell
netstat -ano | findstr ":8001"
netstat -ano | findstr ":8000"

tasklist /fi "PID eq <PID>"

# Kill it (be sure it’s the right one)
Stop-Process -Id <PID> -Force
```