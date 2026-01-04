# Local MCP demo (Demo Commerce API -> MCP -> ChatGPT)

This doc shows how to run the demo API, generate the tool, serve it via MCP over Streamable HTTP, and expose it with ngrok for ChatGPT.

## Prereqs
- Python 3.10+
- PowerShell (Windows) or a shell
- Ngrok installed and authtoken configured (`ngrok config add-authtoken ...`)

## Install deps (shared venv)
```powershell
Set-Location "C:\Users\nadav\Documents\GitHub\Base55"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r demo_api/requirements.txt -r mcp_server/requirements.txt
```

## 1) Run the Demo Commerce API (source of truth OpenAPI)
```powershell
$env:API_PORT="8001"
python -m uvicorn demo_api.main:app --host 127.0.0.1 --port $env:API_PORT --reload
```
- Health: http://127.0.0.1:8001/health  
- Products: http://127.0.0.1:8001/v1/products  
- Search: http://127.0.0.1:8001/v1/products/search?q=widget  
- OpenAPI (used for generation): http://127.0.0.1:8001/openapi.json

## 2) Generate the tool from OpenAPI (function-only)
```powershell
$env:OPENAI_API_KEY="sk-..."
python POC/poc_generate.py --template POC/template_products.json --openapi http://127.0.0.1:8001/openapi.json --output-dir generated
```
Notes:
- The generated `generated/search_products.py` must be function-only (no `@mcp.tool`, no `mcp = ...`).
- Default base URL for the tool is `http://127.0.0.1:8001/v1`; override with `DEMO_API_BASE_URL`.

## 3) Run the MCP server (Streamable HTTP at /mcp)
```powershell
$env:DEMO_API_BASE_URL="http://127.0.0.1:8001"
$env:MCP_PORT="8000"
python -m mcp_server.main
```
- MCP endpoint: http://127.0.0.1:8000/mcp
- Tools: `search_products`

## 4) Local verification (before ChatGPT)
- Option A: Call via MCP Inspector: `npx @modelcontextprotocol/inspector http://127.0.0.1:%MCP_PORT%/mcp`
- Option B: Direct POST JSON-RPC to `/mcp` (Streamable HTTP).

## 5) Expose with ngrok for ChatGPT
```powershell
ngrok http 8000
```
- Use the **HTTPS** forwarding URL from ngrok, e.g. `https://abc123.ngrok.app/mcp`.

## 6) Connect in ChatGPT
- In ChatGPT (developer mode), add a connector with **Connector URL** = `https://abc123.ngrok.app/mcp`.
- In a chat, invoke: “Search products for ‘widget’ and show the top 5.”

## Default ports and overrides
- API: `API_PORT` (default 8001)
- MCP: `MCP_PORT` (default 8000)
- Base URL for tool: `DEMO_API_BASE_URL` (default `http://127.0.0.1:8001/v1`)

