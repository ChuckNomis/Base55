"""
Base55 Generator Backend.

Runs at http://localhost:3001 by default.
POST /generate/openapi  → returns a zip of a Python/FastMCP MCP server
POST /generate/shopify  → (implemented in plan 02)
"""
import asyncio
import io
import json
import zipfile
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import re

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, field_validator

from src.openapi.generator.core import make_all_tools

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATES_DIR = REPO_ROOT / "templates"
UI_DIR = TEMPLATES_DIR / "ui"
MCP_TEMPLATE_DIR = TEMPLATES_DIR / "mcp_server"
ALLOWED_TEMPLATES = {"carousel", "carousel-light", "grid-dark"}

GENERATED_REQUIREMENTS = (
    "fastmcp>=3.2.4\n"
    "httpx>=0.27.0\n"
)

app = FastAPI(title="Base55 Generator Backend", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class OpenAPIRequest(BaseModel):
    specUrl: str
    template: str
    primaryColor: str
    accentColor: str
    bgColor: str

class ShopifyRequest(BaseModel):
    storeDomain: str
    storefrontToken: str
    template: str
    primaryColor: str
    accentColor: str
    bgColor: str

    @field_validator("storefrontToken", "storeDomain")
    @classmethod
    def no_template_injection(cls, v: str) -> str:
        if any(c in v for c in ("{", "}", "\n", "\r")):
            raise ValueError("Invalid characters in credential field")
        return v

    @field_validator("storeDomain")
    @classmethod
    def must_be_myshopify(cls, v: str) -> str:
        if not v.endswith(".myshopify.com"):
            raise ValueError("storeDomain must end with .myshopify.com")
        return v

_CSS_COLOR_RE = re.compile(
    r'^#[0-9A-Fa-f]{3}(?:[0-9A-Fa-f]{3})?$'   # hex shorthand or full
    r'|^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$'
)

def _validate_color(value: str, field: str) -> str:
    if not _CSS_COLOR_RE.match(value):
        raise HTTPException(status_code=422, detail=f"Invalid CSS color for {field}: {value!r}")
    return value

def inject_colors(html: str, primary: str, accent: str, bg: str) -> str:
    """Prepend a <style>:root{...}</style> block right after the first <head> tag."""
    style_block = (
        f"<style>:root{{--primary-color:{primary};"
        f"--accent-color:{accent};--bg-color:{bg};}}</style>"
    )
    result = html.replace("</head>", style_block + "</head>", 1)
    if result == html:
        raise ValueError("inject_colors: no </head> tag found in HTML template")
    return result

def build_zip(files: dict[str, str]) -> bytes:
    """Build an in-memory zip from a {filename: content} mapping."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    buf.seek(0)
    return buf.getvalue()

def load_ui_template(template_name: str) -> str:
    """Read templates/ui/{template_name}.html or raise 400."""
    if template_name not in ALLOWED_TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unknown template: {template_name}")
    path = UI_DIR / f"{template_name}.html"
    if not path.exists():
        raise HTTPException(status_code=400, detail=f"Template file missing: {path.name}")
    return path.read_text(encoding="utf-8")

def render_openapi_server(tools: list, base_url: str, template_name: str) -> str:
    env = Environment(loader=FileSystemLoader(str(MCP_TEMPLATE_DIR)), autoescape=False)
    tmpl = env.get_template("server.py.jinja2")
    return tmpl.render(tools=tools, base_url=base_url, template_name=template_name)

def render_shopify_server(store_domain: str, storefront_token: str, template_name: str) -> str:
    env = Environment(loader=FileSystemLoader(str(MCP_TEMPLATE_DIR)), autoescape=False)
    tmpl = env.get_template("shopify_server.py.jinja2")
    return tmpl.render(
        store_domain=store_domain,
        storefront_token=storefront_token,
        template_name=template_name,
    )

@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.post("/generate/openapi")
async def generate_openapi(body: OpenAPIRequest):
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(body.specUrl, timeout=15)
            resp.raise_for_status()
            openapi_spec = resp.json()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch OpenAPI spec: {e}")

    template_path = TEMPLATES_DIR / "products.json"
    try:
        tool_template = json.loads(template_path.read_text(encoding="utf-8"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load tool template: {e}")

    _validate_color(body.primaryColor, "primaryColor")
    _validate_color(body.accentColor, "accentColor")
    _validate_color(body.bgColor, "bgColor")

    loop = asyncio.get_running_loop()
    try:
        manifest = await loop.run_in_executor(None, make_all_tools, openapi_spec, tool_template)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e}")

    base_url = ""
    servers = openapi_spec.get("servers", [])
    if servers and isinstance(servers[0], dict):
        base_url = servers[0].get("url", "") or ""
    server_py = render_openapi_server(manifest.tools, base_url, body.template)

    raw_html = load_ui_template(body.template)
    injected_html = inject_colors(raw_html, body.primaryColor, body.accentColor, body.bgColor)

    zip_bytes = build_zip({
        "server.py": server_py,
        "requirements.txt": GENERATED_REQUIREMENTS,
        f"{body.template}.html": injected_html,
    })
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=server.zip"},
    )

@app.post("/generate/shopify")
async def generate_shopify(body: ShopifyRequest):
    # 1. Validate color values before any processing
    _validate_color(body.primaryColor, "primaryColor")
    _validate_color(body.accentColor, "accentColor")
    _validate_color(body.bgColor, "bgColor")

    # 2. Validate template name + load HTML (raises 400 on bad template)
    raw_html = load_ui_template(body.template)

    # 3. Render server.py — no GPT call, no spec fetch needed
    server_py = render_shopify_server(body.storeDomain, body.storefrontToken, body.template)

    # 4. Color-inject the chosen UI template
    injected_html = inject_colors(raw_html, body.primaryColor, body.accentColor, body.bgColor)

    # 5. Build zip and return
    zip_bytes = build_zip({
        "server.py": server_py,
        "requirements.txt": GENERATED_REQUIREMENTS,
        f"{body.template}.html": injected_html,
    })
    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=server.zip"},
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=3001)
