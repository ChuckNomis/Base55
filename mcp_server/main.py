import os
from typing import Any

import httpx
from mcp.server.fastmcp import FastMCP

from generated.search_products import search_products as generated_search_products


MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")

mcp = FastMCP(
    name="Demo Commerce MCP",
    stateless_http=True,
    json_response=True,
)
mcp.settings.host = MCP_HOST
mcp.settings.port = MCP_PORT


@mcp.tool()
async def search_products(query: str) -> dict[str, Any]:
    """
    Search for products by a keyword. Searches product titles and descriptions.
    If query is "all" or empty, returns all products.
    """
    query_lower = query.strip().lower()
    # Handle requests for all products
    if not query_lower or query_lower in ("all", "all products", "everything", "list all"):
        # Use list_products to return all products
        base_url = os.getenv("DEMO_API_BASE_URL", "http://127.0.0.1:8001")
        url = f"{base_url}/v1/products"
        params = {"limit": 100}
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            products_data = response.json()
            products = [
                {
                    "id": product["id"],
                    "title": product["title"],
                    "price": product["price"],
                    "image_url": product.get("image_url"),
                }
                for product in products_data
            ]
        
        return {"products": products}
    
    # Otherwise, do normal search
    return await generated_search_products(query)


@mcp.tool()
async def list_products(category: str | None = None, limit: int = 100) -> dict[str, Any]:
    """
    List all products, optionally filtered by category.
    
    Args:
        category: Optional category filter (e.g., "widgets", "gadgets", "accessories")
        limit: Maximum number of products to return (default: 100, max: 100)
    """
    base_url = os.getenv("DEMO_API_BASE_URL", "http://127.0.0.1:8001")
    url = f"{base_url}/v1/products"
    params = {"limit": min(limit, 100)}
    if category:
        params["category"] = category
    
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        products_data = response.json()
        products = [
            {
                "id": product["id"],
                "title": product["title"],
                "price": product["price"],
                "image_url": product.get("image_url"),
                "category": product.get("category"),
            }
            for product in products_data
        ]
    
    return {"products": products}


if __name__ == "__main__":
    try:
        mcp.run(
            transport="streamable-http",
        )
    except KeyboardInterrupt:
        # Clean shutdown on Ctrl+C
        pass

