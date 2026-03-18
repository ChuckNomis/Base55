import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { registerAppTool, registerAppResource, RESOURCE_MIME_TYPE } from '@modelcontextprotocol/ext-apps/server';
import { z } from 'zod';

const server = new McpServer({ name: 'products-ui-server', version: '1.0.0' });
const RESOURCE_URI = 'ui://products/carousel';

// 1. THE STATIC SHELL (Frontend)
registerAppResource(server, 'products_carousel_ui', RESOURCE_URI, { mimeType: RESOURCE_MIME_TYPE }, async () => {
  const htmlString = `<!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"><style>body { margin: 0; padding: 0; background: #0f0f0f; font-family: sans-serif; }</style></head>
    <body>
      <div id="carousel" style="display: flex; align-items: center; gap: 10px; overflow-x: auto; overflow-y: hidden; padding: 10px; width: 100%; height: 100vh; box-sizing: border-box; scrollbar-width: thin;">
        <div style="color: #777; font-family: sans-serif; padding: 20px; width: 100%; text-align: center;">Awaiting search results...</div>
      </div>
      
      <script>
        // Listen for the official tool-result notification from Claude
        window.addEventListener("message", (event) => {
          if (event.data?.method === "ui/notifications/tool-result") {
            // FIX: Access the data via the standard MCP Apps structure
            const structuredData = event.data.params.structuredContent;
            const products = structuredData?.products || [];
            
            const container = document.getElementById("carousel");
            
            if (products.length === 0) {
              container.innerHTML = '<div style="color: #777; width: 100%; text-align: center;">No products found.</div>';
              return;
            }

            container.innerHTML = products.map(p => {
              const name = p.title;
              const price = "$" + p.price.toFixed(2);
              const imageUrl = p.image_url;
              return \`
              <div style="flex: 0 0 140px; background: #1e1e1e; border: 1px solid #333; border-radius: 8px; padding: 8px; display: flex; flex-direction: column; gap: 6px; box-sizing: border-box;">
                <img src="\${imageUrl}" alt="\${name}" style="height: 70px; width: 100%; object-fit: cover; border-radius: 4px; border: 1px dashed #555;" />
                <div style="color: #e0e0e0; font-family: sans-serif; flex-grow: 1; display: flex; flex-direction: column; justify-content: center;">
                  <div style="font-weight: 600; font-size: 12px; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;">\${p.title}</div>
                  <div style="color: #4ade80; font-size: 11px; font-weight: bold;">$\${p.price.toFixed(2)}</div>
                </div>
                <button style="margin-top: auto; width: 100%; padding: 5px; background: #3b82f6; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 10px;">LINK</button>
              </div>
            \`;
            }).join('');
          }
        });

        // The Claude Handshake
        window.parent.postMessage({ jsonrpc: "2.0", id: 1, method: "ui/initialize", params: { protocolVersion: "2025-06-18", capabilities: {} } }, "*");
        window.parent.postMessage({ jsonrpc: "2.0", method: "ui/notifications/initialized", params: {} }, "*");
      </script>
    </body>
    </html>`;

  return { 
    contents: [{ 
      uri: RESOURCE_URI, 
      mimeType: RESOURCE_MIME_TYPE, 
      text: htmlString,
      _meta: {
        ui: {
          csp: {
            resourceDomains: ["https://picsum.photos", "https://fastly.picsum.photos"]
          }
        }
      }
    }] 
  };
});

// 2. THE TOOL (Backend)
registerAppTool(server, 'search_products', {
  description: 'Searches for products and displays them in a visual carousel',
  inputSchema: z.object({ keyword: z.string().describe("The search term") }),
  _meta: { ui: { resourceUri: RESOURCE_URI } }
}, async (args) => {
  const keyword = args.keyword as string;
  let fetchedProducts = [];

  try {
    const response = await fetch(`http://127.0.0.1:8001/v1/products/search?q=${encodeURIComponent(keyword)}`);
    if (response.ok) {
      fetchedProducts = await response.json();
    }
  } catch (error) {
    console.error("API Fetch Error:", error);
  }

  // @ts-ignore
  return { 
    content: [{ type: 'text', text: `Fetched ${fetchedProducts.length} items for "${keyword}".` }],
    // FIX: Wrapping in a proper object for Claude's structuredContent validation
    structuredContent: {
      products: fetchedProducts,
      searchTerm: keyword
    }
  };
});

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Master UI Server is running!');
}

main().catch(console.error);