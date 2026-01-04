import os
from typing import Any

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
    Delegate to the generated search_products tool against the Demo Commerce API.
    """
    return await generated_search_products(query)


if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
    )

