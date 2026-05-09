import ast
from pathlib import Path
from jinja2 import Environment, FileSystemLoader

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES_DIR = REPO_ROOT / "templates" / "mcp_server"

def _render(store="mystore.myshopify.com", token="shpat_test_abc", template_name="carousel"):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    return env.get_template("shopify_server.py.jinja2").render(
        store_domain=store, storefront_token=token, template_name=template_name,
    )

def test_renders_with_credentials_hardcoded():
    out = _render()
    assert 'SHOPIFY_STORE_DOMAIN = "mystore.myshopify.com"' in out
    assert 'SHOPIFY_STOREFRONT_TOKEN = "shpat_test_abc"' in out
    assert 'SHOPIFY_API_VERSION = "2025-01"' in out
    assert 'SHOPIFY_GRAPHQL_URL = f"https://{SHOPIFY_STORE_DOMAIN}/api/{SHOPIFY_API_VERSION}/graphql.json"' in out

def test_has_fastmcp_and_app_config():
    out = _render()
    assert "from fastmcp import FastMCP" in out
    assert "from fastmcp.apps import AppConfig" in out
    assert "@mcp.resource(" in out
    assert "ui://shopify/products/carousel" in out
    assert 'mime_type="text/html;profile=mcp-app"' in out
    assert "@mcp.tool(app=AppConfig(resource_uri=\"ui://shopify/products/carousel\"))" in out
    assert "async def shopify_search_products(query: str) -> str:" in out

def test_has_graphql_query_and_auth_header():
    out = _render()
    assert "products(first: $first, query: $query)" in out
    assert "X-Shopify-Storefront-Access-Token" in out
    assert "priceRange" in out and "minVariantPrice" in out
    assert "onlineStoreUrl" in out

def test_reads_template_html_at_startup():
    out = _render(template_name="grid-dark")
    assert '"grid-dark.html"' in out

def test_rendered_output_is_valid_python():
    out = _render()
    # If this raises SyntaxError, the template produced invalid Python.
    ast.parse(out)
