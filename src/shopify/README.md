# Shopify MCP UI Demo

An MCP (Model Context Protocol) server that connects to a Shopify store and displays products in a visual carousel inside Claude chat.

When you ask Claude to search for products, it calls the Shopify Storefront API and renders the results as a scrollable product card carousel — directly in the conversation.

---

## Setup

### 1. Install dependencies

```bash
cd src/shopify
npm install
```

### 2. Create your `.env` file

Create a file called `.env` inside this folder:

```
SHOPIFY_STORE_DOMAIN=YOUR_STORE.myshopify.com
SHOPIFY_STOREFRONT_TOKEN=YOUR_STOREFRONT_ACCESS_TOKEN
```

Fill in the credentials I will provide you directly. Do **not** share or commit this file — it is already listed in `.gitignore`.

### 3. Add the MCP server to Claude

Open your Claude Desktop config file:

- **Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

Add the following entry inside `"mcpServers"`:

```json
{
  "mcpServers": {
    "shopify-products": {
      "command": "npx",
      "args": ["tsx", "C:/path/to/src/shopify/index.ts"]
    }
  }
}
```

Replace `C:/path/to/src/shopify` with the actual absolute path to this folder on your machine.

### 4. Restart Claude Desktop

After saving the config, fully quit and reopen Claude Desktop. The server will start automatically.

---

## Usage

In Claude chat, ask something like:

- *"Show me all products"*
- *"Search for blue shirts"*
- *"Find running shoes"*

Claude will call the `search_products` tool and render the results in the carousel UI.
