import os
import httpx

async def search_products(query: str) -> dict:
    """
    Search for products by a keyword.

    Args:
        query (str): The keyword to search products.

    Returns:
        dict: A dictionary containing a list of products with their id, title, price, and image_url.
    """
    base_url = os.getenv('DEMO_API_BASE_URL', 'http://127.0.0.1:8001')
    url = f"{base_url}/v1/products/search"
    params = {'q': query}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params)
        response.raise_for_status()
        
        products_data = response.json()
        products = [
            {
                'id': product['id'],
                'title': product['title'],
                'price': product['price'],
                'image_url': product.get('image_url', None)
            }
            for product in products_data
        ]
        
    return {'products': products}