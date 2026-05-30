"""
Auto-generated MCP server by Base55.
Run:  pip install -r requirements.txt && python server.py
"""
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
with open(_os.path.join(_HERE, "carousel-light.html"), "r", encoding="utf-8") as _f:
    _CAROUSEL_HTML = _f.read()

# ── Generated tool functions ─────────────────────────────────────────────────


# Tool: search_products
async def search_products(query: str) -> dict:
    """
    Search for products by a keyword and return them in a format suitable
    for displaying in a product carousel.
    """
    import httpx
    
    base_url = "http://127.0.0.1:8001"
    endpoint = f"{base_url}/v1/products/search"
    
    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint, params={"query": query})
        response.raise_for_status()
        
        products_data = response.json()
        products = []
        for item in products_data:
            products.append({
                "id": item.get("id", ""),
                "title": item.get("title", ""),
                "price": f"${item.get('price', 0):.2f}",
                "image_url": item.get("image_url", ""),
                "description": item.get("description", ""),
                "link": item.get("link", "")
            })
        
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
async def search_products_tool(query: str) -> str:
    """Search for products by keyword and display them in a visual carousel"""
    result = await search_products(query)
    return json.dumps(result)


# ── Server Start ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()