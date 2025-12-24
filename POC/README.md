# POC: OpenAPI-to-MCP Tool Generator

Minimal POC that turns an OpenAPI spec into FastMCP-style Python tool code using a template + GPT.

## Files
- `template_products.json`: Products template with `search_products` tool definition.
- `sample_openapi.json`: Custom OpenAPI spec with correct product endpoints and dummy distractors (orders/users/auth).
- `poc_generate.py`: Script to call OpenAI and generate tool code.
- `requirements.txt`: Dependencies.

## Prereqs
- Python 3.10+ recommended.
- Environment variable `OPENAI_API_KEY` set to a valid key.
- Default model: `gpt-4o` (override with `OPENAI_MODEL` or `--model`).

## Setup (Windows PowerShell)
```powershell
cd POC
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Set your key for this session
$env:OPENAI_API_KEY = "sk-..."
```

## Run
```powershell
python poc_generate.py --template POC/template_products.json --openapi POC/sample_openapi.json
```

Options:
- `--model` (default `gpt-4o`)
- `--max-chars` truncate spec in prompt (default 12000)
- `--output-dir <path>` write each tool’s code to files in that directory

Example writing files:
```powershell
python poc_generate.py --output-dir generated
```

Expected behavior:
- For `search_products`, the model should pick `/products/search` (or `/products`) and avoid dummy endpoints under `/orders`, `/users`, `/auth`.
- The script prints generated code; with `--output-dir`, also writes `search_products.py`.

