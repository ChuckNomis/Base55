---
phase: "04"
plan: "02"
subsystem: backend
tags: [shopify, fastapi, jinja2, mcp, codegen]
dependency_graph:
  requires: [04-01]
  provides: [shopify-endpoint, shopify-server-template]
  affects: [src/backend/server.py, templates/mcp_server/]
tech_stack:
  added: []
  patterns: [jinja2-codegen, fastapi-endpoint, zip-response]
key_files:
  created:
    - templates/mcp_server/shopify_server.py.jinja2
    - src/backend/tests/test_shopify_template.py
  modified:
    - src/backend/server.py
    - src/backend/tests/test_endpoints.py
decisions:
  - "Shopify endpoint requires no GPT call — credentials + template_name render directly via Jinja2"
  - "render_shopify_server mirrors render_openapi_server pattern for consistency"
  - "Appended Shopify tests to existing test_endpoints.py to keep all endpoint tests co-located"
metrics:
  duration: "~5 minutes"
  completed: "2026-05-09"
  tasks_completed: 2
  tests_added: 9
---

# Phase 4 Plan 02: Shopify Endpoint Summary

Jinja2 template for Shopify MCP server codegen + POST /generate/shopify FastAPI endpoint with full test coverage.

## What Was Built

### Task 1 — Shopify Jinja2 Server Template

Created `templates/mcp_server/shopify_server.py.jinja2`: a self-contained Python/FastMCP server template that accepts `store_domain`, `storefront_token`, and `template_name` variables. The rendered output hardcodes Shopify credentials, includes the full GraphQL products query (matching `src/shopify/index.ts`), wires a FastMCP carousel UI resource, and registers a `shopify_search_products` tool with `AppConfig`.

Created `src/backend/tests/test_shopify_template.py` with 5 tests verifying credential injection, FastMCP imports, GraphQL query structure, HTML filename injection, and valid Python syntax of the rendered output.

### Task 2 — POST /generate/shopify Endpoint

Added `render_shopify_server()` function to `src/backend/server.py` that renders the Jinja2 template with the provided credentials and template name.

Added `@app.post("/generate/shopify")` handler that:
1. Validates template name via `load_ui_template()` (raises 400 on unknown template)
2. Renders `server.py` from template — no GPT call needed
3. Color-injects the selected UI HTML
4. Builds and returns a zip containing `server.py`, `requirements.txt`, and `{template}.html`

Appended 4 Shopify endpoint tests to `src/backend/tests/test_endpoints.py` (preserving all 5 existing OpenAPI tests).

## Files Created / Modified

| File | Action |
|------|--------|
| `templates/mcp_server/shopify_server.py.jinja2` | Created |
| `src/backend/tests/test_shopify_template.py` | Created |
| `src/backend/server.py` | Modified — added `render_shopify_server()` + `/generate/shopify` handler |
| `src/backend/tests/test_endpoints.py` | Modified — appended 4 Shopify endpoint tests |

## Test Results

```
pytest src/backend/tests/ -x -q
20 passed, 3 warnings in 0.49s
```

Re-run: `python -m pytest src/backend/tests/ -x -q`

Breakdown:
- `test_shopify_template.py`: 5 tests (new, Task 1)
- `test_endpoints.py`: 9 tests (5 existing OpenAPI + 4 new Shopify, Task 2)
- `test_generate.py` + others: 6 tests (from Plan 01, untouched)

## Routes

```
/healthz
/generate/openapi
/generate/shopify
```

## Requirements Coverage

- **BE-02**: POST /generate/shopify endpoint — COMPLETE
- **BE-03**: Shopify server template with hardcoded credentials — COMPLETE

## Phase 4 Status

Phase 4 (Backend Integration) is **COMPLETE**. Both plans done:
- Plan 04-01: FastAPI scaffold + POST /generate/openapi (commit a300204)
- Plan 04-02: Shopify template + POST /generate/shopify (commits 0f0511d, b9191b9)

Ready for `/gsd-verify-work`.

## Deviations from Plan

None. Plan executed exactly as written.

## Self-Check

- [x] `templates/mcp_server/shopify_server.py.jinja2` exists
- [x] `src/backend/tests/test_shopify_template.py` exists with 5 passing tests
- [x] `src/backend/server.py` has `def render_shopify_server(` and `@app.post("/generate/shopify")`
- [x] `src/backend/tests/test_endpoints.py` has 9 tests (5 original preserved + 4 new)
- [x] Full suite: 20 tests passing
- [x] Commits: 0f0511d (Task 1), b9191b9 (Task 2)

## Self-Check: PASSED
