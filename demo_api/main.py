from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import List, Literal, Set

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, HttpUrl


DATA_PATH = Path(__file__).parent / "data" / "products.json"
IMAGES_PATH = Path(__file__).parent / "data" / "images"
API_VERSION = "1.1.0"
STARTED_AT = datetime.now(tz=UTC)


def stem_word(word: str) -> str:
    """Reduce words to a lightweight root for fuzzy search."""
    word = word.lower().strip()
    if len(word) <= 3:
        return word

    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("es") and len(word) > 4:
        if word[-3] in "chshsxz":
            return word[:-2]
        if len(word) > 4 and word[-3] not in "aeiou" and word[-3] == "o":
            return word[:-2]
    if word.endswith("s") and len(word) > 3:
        if word[-2] != "s" and word[-2] not in "aeiou":
            return word[:-1]

    if word.endswith("ing") and len(word) > 5:
        if word[-4] == word[-5]:
            return word[:-4]
        return word[:-3]
    if word.endswith("ed") and len(word) > 4:
        if word[-3] == word[-4]:
            return word[:-3]
        return word[:-2]

    return word


def get_stemmed_words(text: str) -> Set[str]:
    """Extract stemmed words from free text."""
    words = re.findall(r"\w+", text.lower())
    return {stem_word(word) for word in words}


class Product(BaseModel):
    id: str = Field(description="Stable product identifier")
    sku: str = Field(description="Seller stock keeping unit")
    title: str
    description: str | None = None
    category: str | None = None
    brand: str | None = None
    tags: list[str] = Field(default_factory=list)
    price: float = Field(ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    image_url: HttpUrl | None = None
    link: HttpUrl | None = Field(default=None, description="Canonical product page URL")
    stock_quantity: int = Field(default=0, ge=0)
    rating: float | None = Field(default=None, ge=0, le=5)

    @property
    def in_stock(self) -> bool:
        return self.stock_quantity > 0


class ProductListItem(BaseModel):
    id: str
    sku: str
    title: str
    description: str | None = None
    category: str | None = None
    brand: str | None = None
    tags: list[str] = Field(default_factory=list)
    price: float
    currency: str
    image_url: HttpUrl | None = None
    link: HttpUrl | None = None
    stock_quantity: int
    in_stock: bool
    rating: float | None = None


class ProductListResponse(BaseModel):
    items: list[ProductListItem]
    total: int
    page: int
    page_size: int
    has_next: bool


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    uptime_seconds: int


def load_products() -> List[Product]:
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found at {DATA_PATH}")
    with DATA_PATH.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    return [Product(**item) for item in raw]


def to_list_item(product: Product) -> ProductListItem:
    return ProductListItem(
        id=product.id,
        sku=product.sku,
        title=product.title,
        description=product.description,
        category=product.category,
        brand=product.brand,
        tags=product.tags,
        price=product.price,
        currency=product.currency,
        image_url=product.image_url,
        link=product.link,
        stock_quantity=product.stock_quantity,
        in_stock=product.in_stock,
        rating=product.rating,
    )


def matches_query(product: Product, query: str) -> bool:
    query_stems = get_stemmed_words(query)
    if not query_stems:
        return True

    searchable_chunks = [
        product.title or "",
        product.description or "",
        product.category or "",
        product.brand or "",
        " ".join(product.tags),
    ]
    product_stems: Set[str] = set()
    for chunk in searchable_chunks:
        product_stems |= get_stemmed_words(chunk)

    return bool(query_stems & product_stems)


app = FastAPI(
    title="Demo Commerce API",
    version=API_VERSION,
    description=(
        "A realistic demo commerce service with pagination, filtering, and "
        "search endpoints suitable for MCP tool generation workflows."
    ),
    # Keep an explicit URL so generator logic can reliably read servers[0].url.
    servers=[{"url": "http://127.0.0.1:8001"}],
)
app.mount("/images", StaticFiles(directory=IMAGES_PATH), name="images")
PRODUCTS = load_products()


@app.get("/v1/products", response_model=ProductListResponse, summary="List products")
async def list_products(
    q: str | None = Query(default=None, description="Free-text product query"),
    category: str | None = Query(default=None, description="Filter by category"),
    brand: str | None = Query(default=None, description="Filter by brand"),
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    in_stock: bool | None = Query(default=None, description="Only show in-stock items"),
    sort_by: Literal["relevance", "price_asc", "price_desc", "title_asc"] = Query(
        default="relevance", description="Sort strategy"
    ),
    page: int = Query(default=1, ge=1, description="1-based page index"),
    page_size: int = Query(default=20, ge=1, le=100),
):
    items = PRODUCTS
    if q:
        items = [p for p in items if matches_query(p, q)]
    if category:
        items = [p for p in items if (p.category or "").lower() == category.lower()]
    if brand:
        items = [p for p in items if (p.brand or "").lower() == brand.lower()]
    if min_price is not None:
        items = [p for p in items if p.price >= min_price]
    if max_price is not None:
        items = [p for p in items if p.price <= max_price]
    if in_stock is not None:
        items = [p for p in items if p.in_stock is in_stock]

    if sort_by == "price_asc":
        items = sorted(items, key=lambda p: p.price)
    elif sort_by == "price_desc":
        items = sorted(items, key=lambda p: p.price, reverse=True)
    elif sort_by == "title_asc":
        items = sorted(items, key=lambda p: p.title.lower())

    total = len(items)
    start = (page - 1) * page_size
    end = start + page_size
    page_items = items[start:end]

    return ProductListResponse(
        items=[to_list_item(p) for p in page_items],
        total=total,
        page=page,
        page_size=page_size,
        has_next=end < total,
    )


@app.get(
    "/v1/products/search",
    response_model=list[ProductListItem],
    summary="Search products by keyword",
    description=(
        "Compatibility endpoint for MCP generation demos. Accepts either q or query, "
        "then returns a flat list."
    ),
)
async def search_products(
    q: str | None = Query(default=None, description="Keyword to search products"),
    query: str | None = Query(
        default=None, description="Alias for q used by generated MCP tools"
    ),
    limit: int = Query(default=10, ge=1, le=50, description="Max products to return"),
):
    incoming_query = (q or query or "").strip()
    if not incoming_query:
        raise HTTPException(status_code=400, detail="Either q or query must be provided.")

    matched = [p for p in PRODUCTS if matches_query(p, incoming_query)]
    return [to_list_item(p) for p in matched[:limit]]


@app.get(
    "/v1/products/id/{product_id}",
    response_model=ProductListItem,
    summary="Get product by id",
)
async def get_product(product_id: str):
    for product in PRODUCTS:
        if product.id == product_id:
            return to_list_item(product)
    raise HTTPException(status_code=404, detail="Product not found")


@app.get("/health", response_model=HealthResponse, summary="Health check")
async def health():
    uptime_seconds = int((datetime.now(tz=UTC) - STARTED_AT).total_seconds())
    return HealthResponse(status="ok", version=API_VERSION, uptime_seconds=uptime_seconds)

