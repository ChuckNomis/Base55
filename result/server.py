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
with open(_os.path.join(_HERE, "carousel.html"), "r", encoding="utf-8") as _f:
    _CAROUSEL_HTML = _f.read()

# ── Generated tool functions ─────────────────────────────────────────────────


# Tool: get_all_products
async def get_all_products() -> dict:
    """
    Fetch all products from the catalog and return them in a format
    suitable for a carousel display. This function handles pagination
    to ensure all products are retrieved across all available pages.
    """
    base_url = "http://127.0.0.1:8001"
    endpoint = "/v1/products"
    page = 1
    page_size = 20
    all_products = []

    async with httpx.AsyncClient() as client:
        while True:
            response = await client.get(
                f"{base_url}{endpoint}",
                params={"page": page, "page_size": page_size}
            )
            response.raise_for_status()

            data = response.json()
            items = data.get("items", [])

            for item in items:
                product = {
                    "id": item.get("id", ""),
                    "title": item.get("title", ""),
                    "price": f"${item.get('price', 0):.2f}",
                    "image_url": item.get("image_url", ""),
                    "description": item.get("description", ""),
                    "link": item.get("link", "")
                }
                all_products.append(product)

            if not data.get("has_next", False):
                break

            page += 1

    return {"products": all_products}


# Tool: search_products
async def search_products(query: str) -> dict:
    """
    Search for products using a query string and return them in a carousel-compatible format.
    """
    import httpx

    base_url = "http://127.0.0.1:8001"
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{base_url}/v1/products/search", params={"query": query})
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
    """Show ALL products in a visual carousel. Use this ONLY when the user wants to browse everything with no specific filter (e.g. 'show me all products', 'what do you have?'). If the user mentions ANY specific product type, name, or category, use search_products_tool instead."""
    result = await get_all_products()

    return json.dumps(result)


@mcp.tool(app=AppConfig(resource_uri="ui://products/carousel"))

async def search_products_tool(query: str) -> str:
    """Search for products by keyword and display results in a visual carousel. Use this whenever the user mentions ANY specific product, type, or category (e.g. 'phone', 'shoes', 'blue jacket', 'something for running'). Always prefer this over get_all_products_tool when any search term is present."""
    result = await search_products(query)

    return json.dumps(result)


# ── Server Start ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    mcp.run()