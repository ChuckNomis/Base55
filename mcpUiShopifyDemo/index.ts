import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { registerAppTool, registerAppResource } from '@modelcontextprotocol/ext-apps/server';
import { createUIResource } from '@mcp-ui/server';
import { z } from 'zod';
import * as fs from 'fs';
import * as path from 'path';
import * as dotenv from 'dotenv';

dotenv.config({ path: path.join(__dirname, '.env') });

// ── Shopify Config ────────────────────────────────────────────────────────────

const SHOPIFY_STORE_DOMAIN = process.env.SHOPIFY_STORE_DOMAIN!;
const SHOPIFY_STOREFRONT_TOKEN = process.env.SHOPIFY_STOREFRONT_TOKEN!;

if (!SHOPIFY_STORE_DOMAIN || !SHOPIFY_STOREFRONT_TOKEN) {
  console.error('Missing required env vars: SHOPIFY_STORE_DOMAIN, SHOPIFY_STOREFRONT_TOKEN');
  process.exit(1);
}

const SHOPIFY_API_VERSION = '2025-01';
const SHOPIFY_GRAPHQL_URL = `https://${SHOPIFY_STORE_DOMAIN}/api/${SHOPIFY_API_VERSION}/graphql.json`;

// ── Types ─────────────────────────────────────────────────────────────────────

interface ShopifyProduct {
  id: string;
  title: string;
  description: string;
  onlineStoreUrl: string | null;
  images: {
    edges: { node: { url: string; altText: string | null } }[];
  };
  priceRange: {
    minVariantPrice: {
      amount: string;
      currencyCode: string;
    };
  };
}

interface CarouselProduct {
  id: string;
  title: string;
  price: string;
  image_url: string;
  description: string;
  link: string;
}

// ── Shopify Storefront API ────────────────────────────────────────────────────

const PRODUCTS_QUERY = `
  query SearchProducts($query: String!, $first: Int!) {
    products(first: $first, query: $query) {
      edges {
        node {
          id
          title
          description
          onlineStoreUrl
          images(first: 1) {
            edges {
              node {
                url
                altText
              }
            }
          }
          priceRange {
            minVariantPrice {
              amount
              currencyCode
            }
          }
        }
      }
    }
  }
`;

async function search_products(query: string): Promise<{ products: CarouselProduct[] }> {
  const response = await fetch(SHOPIFY_GRAPHQL_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Shopify-Storefront-Access-Token': SHOPIFY_STOREFRONT_TOKEN,
    },
    body: JSON.stringify({
      query: PRODUCTS_QUERY,
      variables: {
        // Empty query returns all products; a keyword filters by title/tag/etc.
        query: query || '',
        first: 12,
      },
    }),
  });

  if (!response.ok) {
    throw new Error(`Shopify API error: ${response.status} ${response.statusText}`);
  }

  const json = await response.json() as {
    data?: { products: { edges: { node: ShopifyProduct }[] } };
    errors?: { message: string }[];
  };

  if (json.errors?.length) {
    throw new Error(`Shopify GraphQL error: ${json.errors[0].message}`);
  }

  const edges = json.data?.products?.edges ?? [];

  return {
    products: edges.map(({ node }): CarouselProduct => {
      const price = node.priceRange.minVariantPrice;
      const formattedPrice = price
        ? `${price.currencyCode} ${parseFloat(price.amount).toFixed(2)}`
        : '';

      return {
        id: node.id,
        title: node.title || '',
        price: formattedPrice,
        image_url: node.images.edges[0]?.node.url ?? '',
        description: node.description || '',
        link: node.onlineStoreUrl ?? '#',
      };
    }),
  };
}

// ── MCP Server Setup ──────────────────────────────────────────────────────────

const server = new McpServer({ name: 'Shopify Products MCP', version: '1.0.0' });

// ── UI Resource ───────────────────────────────────────────────────────────────

const carouselHtml = fs.readFileSync(path.join(__dirname, 'carousel.html'), 'utf-8');

const productsUI = createUIResource({
  uri: 'ui://shopify/products/carousel',
  content: {
    type: 'rawHtml',
    htmlString: carouselHtml,
  },
  encoding: 'text',
});

registerAppResource(server, 'shopify_products_carousel_ui', productsUI.resource.uri, {}, async () => ({
  contents: [{
    ...productsUI.resource,
    mimeType: 'text/html;profile=mcp-app',
  }],
}));

// ── Tool Registration ─────────────────────────────────────────────────────────

registerAppTool(server, 'search_products', {
  description: 'Search Shopify products by keyword and display them in a visual carousel. Leave query empty to browse all products.',
  inputSchema: z.object({
    query: z.string().describe('Search keyword (e.g. "shirt", "blue"). Leave empty to show all products.'),
  }),
  _meta: { ui: { resourceUri: productsUI.resource.uri } },
}, async (input: { query: string }) => {
  const result = await search_products(input.query);
  return {
    content: [{ type: 'text', text: JSON.stringify(result) }],
  };
});

// ── Server Start ──────────────────────────────────────────────────────────────

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Shopify MCP Server is running!');
}

main().catch(console.error);
