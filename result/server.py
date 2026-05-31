"""
Auto-generated MCP server by Base55.
Run:  pip install -r requirements.txt && python server.py
"""
import asyncio
import base64
import json
import httpx
from fastmcp import FastMCP
from fastmcp.apps import AppConfig

mcp = FastMCP("Generated Commerce MCP", version="1.0.0")
BASE_URL = "http://127.0.0.1:8001"

# Read carousel HTML at startup (relative to this script's directory so it works
# regardless of which directory Claude launches "python server.py" from)
import os as _os
_HERE = _os.path.dirname(_os.path.abspath(__file__))
with open(_os.path.join(_HERE, "carousel.html"), "r", encoding="utf-8") as _f:
    _CAROUSEL_HTML = _f.read()

_IMAGE_EMBED_LIMIT = 20

async def _embed_images(products: list) -> list:
    """Embed images as base64 data URIs for the first _IMAGE_EMBED_LIMIT products.
    Beyond that limit the image_url is cleared so the carousel shows a placeholder,
    keeping the tool result within Claude's context window."""
    async def _fetch(url: str) -> str:
        if not url:
            return ""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                r = await client.get(url)
                if r.status_code == 200:
                    mime = r.headers.get("content-type", "image/jpeg").split(";")[0]
                    data = base64.b64encode(r.content).decode()
                    return f"data:{mime};base64,{data}"
        except Exception:
            pass
        return url

    to_embed = products[:_IMAGE_EMBED_LIMIT]
    beyond = products[_IMAGE_EMBED_LIMIT:]

    urls = [p.get("image_url", "") for p in to_embed]
    data_uris = await asyncio.gather(*[_fetch(u) for u in urls])
    for product, uri in zip(to_embed, data_uris):
        product["image_url"] = uri
    for product in beyond:
        product["image_url"] = ""
    return products

# ── Generated tool functions ─────────────────────────────────────────────────


# Tool: get_all_products
async def get_all_products() -> dict:
    """
    Fetches all products from the catalog and returns them in a structured format suitable for a product carousel.
    The function handles pagination and continues fetching until all products are retrieved.
    """
    import httpx
    base_url = "http://127.0.0.1:8001"
    products = []
    page = 1
    has_next = True

    async with httpx.AsyncClient() as client:
        while has_next:
            response = await client.get(f"{base_url}/v1/products", params={"page": page})
            response.raise_for_status()
            data = response.json()
            for item in data.get("items", []):
                products.append({
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "price": f"${item.get('price', 0):.2f}",
                    "image_url": item.get("image_url") or "",
                    "description": item.get("description") or "",
                    "link": item.get("link") or "",
                })
            has_next = data.get("has_next", False)
            page += 1

    return {"products": products}


# Tool: search_products
async def search_products(query: str) -> dict:
    """
    Search for products by a keyword and return a list of products
    formatted for a product carousel.
    """
    import httpx

    base_url = "http://127.0.0.1:8001"
    endpoint = "/v1/products/search"
    url = f"{base_url}{endpoint}"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params={"query": query})
        response.raise_for_status()
        products_data = response.json()

    products = [
        {
            "id": product.get("id", ""),
            "title": product.get("title", ""),
            "price": f"${product.get('price', 0):.2f}",
            "image_url": product.get("image_url", ""),
            "description": product.get("description", ""),
            "link": product.get("link", "")
        }
        for product in products_data
    ]

    return {"products": products}


# ── UI Resource ───────────────────────────────────────────────────────────────

@mcp.resource(
    "ui://products/carousel",
    mime_type="text/html;profile=mcp-app",
    meta={"preferred-frame-size": ["100%", "320px"]},
)
def carousel_ui() -> str:
    return _CAROUSEL_HTML

# ── Tool Registrations ────────────────────────────────────────────────────────


@mcp.tool(app=AppConfig(resource_uri="ui://products/carousel"))

async def get_all_products_tool() -> str:
    """Fetch ALL products from the catalog and display them in a visual carousel. Must return every product across all pages."""
    result = await get_all_products()

    if isinstance(result.get("products"), list):
        result["products"] = await _embed_images(result["products"])
    return json.dumps(result)


@mcp.tool(app=AppConfig(resource_uri="ui://products/carousel"))

async def search_products_tool(query: str) -> str:
    """Search for products by keyword and display them in a visual carousel"""
    result = await search_products(query)

    if isinstance(result.get("products"), list):
        result["products"] = await _embed_images(result["products"])
    return json.dumps(result)


# ── Server Start ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()