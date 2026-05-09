from pathlib import Path
from jinja2 import Environment, FileSystemLoader

REPO_ROOT = Path(__file__).resolve().parents[3]
TEMPLATES_DIR = REPO_ROOT / "templates" / "mcp_server"

def _render(tools, base_url="https://api.example.com", template_name="carousel"):
    env = Environment(loader=FileSystemLoader(str(TEMPLATES_DIR)), autoescape=False)
    tmpl = env.get_template("server.py.jinja2")
    return tmpl.render(tools=tools, base_url=base_url, template_name=template_name)

def test_renders_with_empty_tools():
    out = _render([])
    assert "from fastmcp import FastMCP" in out
    assert "@mcp.resource(" in out
    assert "ui://products/carousel" in out
    assert 'BASE_URL = "https://api.example.com"' in out
    assert 'open("carousel.html"' in out

def test_renders_with_one_tool():
    tools = [type("T", (), {"name": "search_products", "code": "async def search_products(q):\n    return {'products': []}", "description": "Search"})()]
    out = _render(tools)
    assert "async def search_products(q):" in out
    assert "search_products_tool" in out
    assert "@mcp.tool(app=AppConfig(resource_uri=\"ui://products/carousel\"))" in out
