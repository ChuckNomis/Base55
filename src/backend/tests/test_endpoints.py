import io
import zipfile
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from fastapi.testclient import TestClient

from src.backend.server import app
from src.openapi.generator.models import GeneratedTool, ToolsManifest

client = TestClient(app)

VALID_BODY = {
    "specUrl": "http://127.0.0.1:8001/openapi.json",
    "template": "carousel",
    "primaryColor": "#FF6B00",
    "accentColor": "#1A1A1A",
    "bgColor": "#0F0F0F",
}

FAKE_SPEC = {"servers": [{"url": "https://api.example.com"}], "paths": {}}
FAKE_MANIFEST = ToolsManifest(tools=[
    GeneratedTool(name="search_products", code="async def search_products(q):\n    return {'products': []}", description="Search"),
])

def test_healthz():
    assert client.get("/healthz").json() == {"status": "ok"}

def test_openapi_missing_field_returns_422():
    body = dict(VALID_BODY); del body["specUrl"]
    assert client.post("/generate/openapi", json=body).status_code == 422

def test_openapi_unknown_template_returns_400():
    body = dict(VALID_BODY); body["template"] = "nonexistent"
    with patch("src.backend.server.httpx.AsyncClient") as mock_client, \
         patch("src.backend.server.make_all_tools", return_value=FAKE_MANIFEST):
        mock_resp = MagicMock(); mock_resp.json.return_value = FAKE_SPEC; mock_resp.raise_for_status = MagicMock()
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
        r = client.post("/generate/openapi", json=body)
    assert r.status_code == 400
    assert "Unknown template" in r.json()["detail"]

def test_openapi_happy_path_returns_zip():
    with patch("src.backend.server.httpx.AsyncClient") as mock_client, \
         patch("src.backend.server.make_all_tools", return_value=FAKE_MANIFEST):
        mock_resp = MagicMock(); mock_resp.json.return_value = FAKE_SPEC; mock_resp.raise_for_status = MagicMock()
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_resp)
        r = client.post("/generate/openapi", json=VALID_BODY)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/zip"
    assert "filename=server.zip" in r.headers["content-disposition"]
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = set(zf.namelist())
    assert names == {"server.py", "requirements.txt", "carousel.html"}
    server_py = zf.read("server.py").decode("utf-8")
    assert "from fastmcp import FastMCP" in server_py
    assert "search_products" in server_py
    html = zf.read("carousel.html").decode("utf-8")
    assert "<style>:root{--primary-color:#FF6B00;" in html
    reqs = zf.read("requirements.txt").decode("utf-8")
    assert "fastmcp>=" in reqs and "httpx>=" in reqs

def test_openapi_spec_fetch_failure_returns_400():
    with patch("src.backend.server.httpx.AsyncClient") as mock_client:
        mock_client.return_value.__aenter__.return_value.get = AsyncMock(side_effect=Exception("connection refused"))
        r = client.post("/generate/openapi", json=VALID_BODY)
    assert r.status_code == 400
    assert "Failed to fetch" in r.json()["detail"]

def test_cors_preflight_allowed():
    r = client.options(
        "/generate/openapi",
        headers={"Origin": "http://localhost:8000", "Access-Control-Request-Method": "POST"},
    )
    assert r.status_code in (200, 204)
    assert r.headers.get("access-control-allow-origin") == "*"
