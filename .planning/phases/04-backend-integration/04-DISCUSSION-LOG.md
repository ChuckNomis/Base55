# Phase 4: Backend Integration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-08
**Phase:** 4-backend-integration
**Areas discussed:** Backend technology, OpenAPI generation flow, Shopify package structure, Template + color injection

---

## Backend Technology

| Option | Description | Selected |
|--------|-------------|----------|
| Express.js (TypeScript) | Same runtime as wizard; Python generator called via subprocess | |
| FastAPI (Python) | Same language as generator; direct import; matches demo_api/ pattern | ✓ |
| You decide | Claude picks | |

**User's choice:** FastAPI (Python) — and went further: "can we change it all to python?"

**Extended discussion:**
- User asked about the TypeScript ecosystem in the repo before deciding
- After understanding the existing TS code (assembler, Shopify server), user chose FastAPI for the backend AND asked to rewrite the assembler in Python too
- When asked about the generated server output, user selected FastMCP + mcp-ui Python package (consistent with all-Python goal)
- Generated MCP servers (both OpenAPI and Shopify) will be Python, not TypeScript

**Notes:** Significant scope expansion from "wire existing pipelines" to "rewrite assembler + generate Python servers." User's intent is a Python-only stack for all server-side code.

---

## OpenAPI Generation Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Synchronous | POST waits for full GPT-4o + assembly, returns zip | ✓ |
| Job ID + polling | POST returns jobId, wizard polls for completion | |
| SSE / streaming | Server-sent events for progress | |

**User's choice:** Synchronous

**API key handling:**

| Option | Description | Selected |
|--------|-------------|----------|
| .env file on server | Backend reads OPENAI_API_KEY at startup | ✓ |
| User provides in wizard | Wizard sends key in POST body | |

**User's choice:** .env file on server

---

## Shopify Package Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Fresh Python/FastMCP server from template | Jinja2 template, credentials as constants | ✓ |
| Copy existing TypeScript Shopify server | Copy src/shopify/ + inject .env | |

**User's choice:** Fresh Python/FastMCP server

**Credentials storage:**

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded as constants in server.py | Injected by Jinja2 template | ✓ |
| Injected into .env file | server.py reads via dotenv | |

**User's choice:** Hardcoded constants

---

## Template + Color Injection

| Option | Description | Selected |
|--------|-------------|----------|
| Prepend `<style>:root{}` block to HTML | Same as Phase 2 D-08 | ✓ |
| String replace default values | Fragile if CSS changes | |
| Jinja2 variables in HTML template | Requires converting HTML files | |

**User's choice:** Prepend `<style>:root{}` block

**Who handles injection:**

| Option | Description | Selected |
|--------|-------------|----------|
| Assembler handles it | Assembler receives template + colors, owns complete output | ✓ |
| Backend route handles it | Route modifies HTML before passing to assembler | |

**User's choice:** Assembler handles it

---

## Claude's Discretion

- Exact Python mcp-ui package name and `createUIResource` equivalent API
- Jinja2 template structure for generated `server.py`
- Whether backend uses python-dotenv for its own OPENAI_API_KEY
- Port 3001 CORS configuration (needed for wizard fetch calls)
- Error response format for pipeline failures

## Deferred Ideas

None — discussion stayed within phase scope.
