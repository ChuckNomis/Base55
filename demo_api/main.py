from __future__ import annotations

import json
import re
from pathlib import Path
from typing import List, Set

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel


DATA_PATH = Path(__file__).parent / "data" / "products.json"


def stem_word(word: str) -> str:
    """
    Simple stemmer that reduces words to their root form.
    Handles common pluralizations and word variations.
    """
    word = word.lower().strip()
    if len(word) <= 3:
        return word
    
    # Handle common plural endings
    if word.endswith('ies') and len(word) > 4:
        return word[:-3] + 'y'  # cities -> city
    if word.endswith('es') and len(word) > 4:
        # Check for words ending in ch, sh, s, x, z
        if word[-3] in 'chshsxz':
            return word[:-2]  # boxes -> box, dishes -> dish
        # Check for words ending in consonant + o
        if len(word) > 4 and word[-3] not in 'aeiou' and word[-3] == 'o':
            return word[:-2]  # potatoes -> potato
    if word.endswith('s') and len(word) > 3:
        # Don't stem if it's just 's' or if it ends in 'ss' (like 'access')
        if word[-2] != 's' and word[-2] not in 'aeiou':
            return word[:-1]  # widgets -> widget, gadgets -> gadget
    
    # Handle common verb endings
    if word.endswith('ing') and len(word) > 5:
        if word[-4] == word[-5]:  # running -> run
            return word[:-4]
        return word[:-3]  # searching -> search
    if word.endswith('ed') and len(word) > 4:
        if word[-3] == word[-4]:  # stopped -> stop
            return word[:-3]
        return word[:-2]  # searched -> search
    
    return word


def get_stemmed_words(text: str) -> Set[str]:
    """Extract words from text and return their stemmed forms."""
    words = re.findall(r'\w+', text.lower())
    return {stem_word(word) for word in words if len(word) > 0}


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

    # Get stemmed words from query
    query_stems = get_stemmed_words(query)
    
    def matches_product(product: Product) -> bool:
        # Get stemmed words from product title and description
        title_stems = get_stemmed_words(product.title or "")
        desc_stems = get_stemmed_words(product.description or "")
        all_product_stems = title_stems | desc_stems
        
        # Match if any query stem matches any product stem
        return bool(query_stems & all_product_stems)
    
    matched = [p for p in PRODUCTS if matches_product(p)]
    return matched[:limit]


@app.get("/health")
async def health():
    return {"status": "ok"}

