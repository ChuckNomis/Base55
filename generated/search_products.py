import httpx

async def search_products(query: str) -> dict:
    """
    Searches for products matching the provided query string in the title or description.

    Parameters:
    - query (str): The keyword to search for in product titles or descriptions.

    Returns:
    - dict: A dictionary containing a list of products, each with an id, title, price, and image URL.
    """
    url = "https://api.demo-commerce.test/v1/products/search"
    params = {"q": query, "limit": 10}

    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(url, params=params)
        response.raise_for_status()

        products_data = response.json()
        products = [{
            "id": product.get("id", ""),
            "title": product.get("title", ""),
            "price": product.get("price", 0.0),
            "image_url": product.get("image_url", "")
        } for product in products_data]

        return {"products": products}