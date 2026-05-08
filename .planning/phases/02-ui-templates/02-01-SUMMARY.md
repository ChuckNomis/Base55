---
phase: 02-ui-templates
plan: "01"
subsystem: ui-templates
tags: [carousel, light-theme, css-variables, mcp-protocol]
dependency_graph:
  requires: []
  provides: [templates/ui/carousel-light.html]
  affects: [templates/ui/]
tech_stack:
  added: []
  patterns: [CSS custom properties, MCP postMessage protocol, self-render fallback]
key_files:
  created:
    - templates/ui/carousel-light.html
  modified: []
decisions:
  - "CSS :root block placed immediately inside <style> before all other rules for override-ability"
  - "clearTimeout wrapper pattern wraps renderProducts() after definition so any real MCP message cancels the fallback"
  - "card-btn:hover uses opacity: 0.85 (not a darker hardcoded color) to stay variable-driven"
metrics:
  duration_minutes: 5
  completed_date: "2026-05-08"
  tasks_completed: 1
  tasks_total: 1
  files_created: 1
  files_modified: 0
---

# Phase 2 Plan 01: Light Carousel Template Summary

**One-liner:** Light-theme horizontal product carousel using CSS custom properties (`--primary-color`, `--accent-color`, `--bg-color`) with full MCP postMessage protocol and 500ms self-render fallback.

## What Was Built

`templates/ui/carousel-light.html` — a standalone HTML file providing a white/light-gray product carousel as a visual alternative to the existing dark carousel (`templates/ui/carousel.html`).

**Key characteristics:**
- White card backgrounds (`#ffffff`) on a light-gray body (`var(--bg-color)` = `#f5f5f5`)
- Dark text (`#1a1a1a`) readable on light surfaces
- Green price text via `var(--accent-color)` (`#16a34a`)
- Blue VIEW button via `var(--primary-color)` (`#2563eb`)
- All color rules reference CSS custom properties — override a single `:root` block to retheme the entire carousel

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create carousel-light.html with CSS custom properties and light palette | 82d65ee | templates/ui/carousel-light.html |

## CSS Variables

| Variable | Value | Usage |
|----------|-------|-------|
| `--primary-color` | `#2563eb` | VIEW button background |
| `--accent-color` | `#16a34a` | Price text color |
| `--bg-color` | `#f5f5f5` | Body background + scrollbar track |

## Fallback Timer

- Fires at 500ms after page load if no MCP host postMessage arrives
- Renders 3 sample products: Wireless Headphones ($79.99), Leather Wallet ($34.99), Running Shoes ($119.99)
- `clearTimeout(fallbackTimer)` is called via a wrapper around `renderProducts()` — any real MCP data cancels the fallback immediately

## MCP Protocol

All 3 message formats handled (copied verbatim from carousel.html):
1. `ui/initialize` handshake — sends initialize request, handles host acknowledgment
2. `ui/notifications/tool-result` with `content[]` array — parses JSON from text items
3. Direct `msg.products` payload — fallback for simpler MCP host implementations

`appInfo.name` updated to `'Products Carousel Light'` to distinguish from the dark variant.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

**Note on verify script:** The plan's automated verify script (`node -e "..."`) has a bug: the `:root` check passes the regex literal string `'/:root\\s*\\{/'` to `String.includes()`, which always fails (it looks for that exact string, not a regex match). The file is correct — `:root {` is present as specified. All other 12 checks pass using the plan's exact script. A corrected check (plain substring `':root {'`) passes.

## Known Stubs

None — sample products render real UI with meaningful placeholder data. No unfired data paths or empty arrays reach the user.

## Threat Flags

No new security surface beyond what the plan's threat model covers. The postMessage handler pattern is identical to the existing `carousel.html`.

## Self-Check: PASSED

- [x] `templates/ui/carousel-light.html` exists in worktree
- [x] Commit `82d65ee` exists in git log
- [x] All 14 acceptance criteria verified via node script
- [x] No `background: #0f0f0f` in file (dark carousel color does not bleed in)
