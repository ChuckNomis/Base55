from __future__ import annotations

import json
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


DATA_PATH = Path(__file__).parent / "data" / "products.json"


class Product(BaseModel):
    id: str
    title: str
    price: float
    description: str | None = None
    image_url: str | None = None
    category: str | None = None


def load_products() -> List[Product]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")
    with DATA_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Product(**item) for item in raw]


app = FastAPI(
    title="Demo Commerce API",
    version="1.0.0",
    # Publish an explicit server URL so "random API → OpenAPI → tool" generation can
    # reliably pick the correct base URL from `servers[0].url`.
    servers=[{"url": "http://127.0.0.1:8001"}],
)
PRODUCTS = load_products()


@app.get("/v1/products", response_model=List[Product], summary="List products")
async def list_products(
    category: str | None = Query(
        default=None, description="Optional category filter"
    ),
    limit: int = Query(
        default=20, ge=1, le=100, description="Max products to return"
    ),
):
    items = PRODUCTS
    if category:
        items = [p for p in PRODUCTS if p.category == category]
    return items[:limit]


@app.get(
    "/v1/products/search",
    response_model=List[Product],
    summary="Search products by keyword",
    description="Searches title or description for the provided keyword.",
)
async def search_products(
    q: str = Query(..., description="Keyword to search products"),
    limit: int = Query(
        default=10, ge=1, le=50, description="Max products to return"
    ),
):
    query = q.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query must not be empty.")

    lowered = query.lower()
    matched = [
        p
        for p in PRODUCTS
        if lowered in (p.title or "").lower()
        or lowered in (p.description or "").lower()
    ]
    return matched[:limit]


@app.get("/health")
async def health():
    return {"status": "ok"}

