# Base55 -- Project State

## Current Status

**Active Phase:** ALL PHASES COMPLETE ✓
**Last Updated:** 2026-05-09
**Last Session:** Phase 5 UAT passed — both OpenAPI and Shopify flows verified working end-to-end in Claude Desktop
**Resume File:** None — milestone complete
**Current Plan:** Phase 5 COMPLETE (2/2 plans done) — human UAT approved

## Phase Progress

| Phase | Status | Notes |
|-------|--------|-------|
| 1: Organization & Docs | COMPLETE (2/2 plans done) | Plan 1a: dir restructure; Plan 1b: README.md |
| 2: UI Templates | COMPLETE (3/3 plans done) | 02-01: light carousel; 02-02: dark grid; 02-03: refactor existing carousel |
| 3: Web Setup Wizard | COMPLETE (3/3 plans done) | Plan 3a: wizard shell + source selector (bdea49b); Plan 3b: template picker + color customization (10e62b6); Plan 3c: credentials form + generate/result (39b82b1) |
| 4: Backend Integration | COMPLETE (2/2 plans done) | Plan 04-01: FastAPI scaffold + /generate/openapi (a300204); Plan 04-02: Shopify template + /generate/shopify (b9191b9) |
| 5: End-to-End Polish | COMPLETE (2/2 plans done) | 05-01: integration audit + template fixes (8a2e0fc); 05-02: README rewrite (c3e3cef); UAT: both flows verified in Claude Desktop 2026-05-09 |

## Key Context

- OpenAPI generator pipeline: working in `src/openapi/generator/`
- Shopify MCP demo: working in `src/shopify/`
- Dark carousel UI: working in `templates/ui/carousel.html`
- Web wizard shell created: `src/wizard/index.html` (Plan 3a, commit bdea49b)
- Wizard fully complete: Steps 1-5 all implemented (Plan 3c, commit 39b82b1)
- Phase 1 (Organization & Docs) is COMPLETE: src/ restructured, CLAUDE.md rewritten, README.md written
- Phase 3 (Web Setup Wizard) is COMPLETE: all 3 plans done
- Phase 4 Plan 01 COMPLETE: FastAPI backend at port 3001, inject_colors, build_zip, load_ui_template, POST /generate/openapi, 11 pytest tests pass
- Phase 4 Plan 02 COMPLETE: Shopify Jinja2 template, render_shopify_server(), POST /generate/shopify, 20 pytest tests pass (9 new)

## Decisions Log

| Date | Decision | Reason |
|------|----------|--------|
| 2026-05-08 | Web wizard = simple HTML/JS (not Next.js) | Lightweight, matches existing vanilla HTML approach |
| 2026-05-08 | 2-3 UI templates in v1 | Enough to demo customization without over-engineering |
| 2026-05-08 | commit_docs = false | Keep .planning/ local only |
| 2026-05-08 | templates/ at repo root (not inside src/openapi/) | Shared across both OpenAPI and Shopify paths, extended in Phase 2 |
| 2026-05-08 | docs/ directory for meeting notes and PDF | Cleaner than repo root placement |
| 2026-05-08 | README targets developers first with run commands before prose | D-09: developer audience; D-12: covers what exists today only |
| 2026-05-08 | Single-file wizard (all HTML/CSS/JS inline) | No bundler needed; consistent with project's vanilla HTML approach |
| 2026-05-08 | Steps 2-5 rendered as labeled placeholders in Plan 3a | Shell first; Plans 3b/3c fill in content incrementally |
| 2026-05-08 | iframe scaled 3x (300%/scale(0.333)) for template card previews | Full carousel visible in 200px card without clipping |
| 2026-05-08 | Color injection via contentDocument.documentElement.style.setProperty | Same-origin safe for file:// protocol; silent no-op on cross-origin |
| 2026-05-08 | validateStep4 fires only on goNext() click, not on step entry | Avoids showing validation errors when user first arrives at Step 4 |
| 2026-05-08 | HTML entity &#x2B07; for download arrow | Avoids emoji encoding issues across platforms |
| 2026-05-09 | asyncio.run_in_executor wraps make_all_tools | make_all_tools makes blocking LLM calls; executor offloads to thread pool without blocking FastAPI event loop |
| 2026-05-09 | ALLOWED_TEMPLATES set in server.py | Validates template name before filesystem read; returns 400 for unknowns |
| 2026-05-09 | GENERATED_REQUIREMENTS hardcoded string | fastmcp>=3.2.4 + httpx>=0.27.0 matches Python FastMCP API used in server.py.jinja2 |
| 2026-05-09 | Shopify endpoint requires no GPT call | store_domain + storefront_token render directly into Jinja2 template; no spec fetch or LLM inference needed |
| 2026-05-09 | README targets wizard-based flow as primary; assembler noted as legacy | Phase 5 closes the loop — README must reflect actual current system state |
| 2026-05-09 | GPT prompt updated to request Python/httpx (was TypeScript/fetch) | products.json system prompt was never updated when pipeline switched from TS assembler to Python/FastMCP |
| 2026-05-09 | inject_colors replaces before </head> not after <head> | Injected :root vars must come after template defaults in the cascade to win |
