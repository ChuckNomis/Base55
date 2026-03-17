import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { registerAppTool, registerAppResource } from '@modelcontextprotocol/ext-apps/server';
import { createUIResource } from '@mcp-ui/server';

// 1. Initialize the server
const server = new McpServer({ name: 'products-ui-server', version: '1.0.0' });

// Helper to generate a compact card
const createCard = (name: string, price: string) => `
  <div style="flex: 0 0 160px; background: #1e1e1e; border: 1px solid #333; border-radius: 10px; padding: 10px; display: flex; flex-direction: column; gap: 8px; box-sizing: border-box;">
    <div style="height: 100px; background: #2a2a2a; border-radius: 6px; border: 1px dashed #555; display: flex; align-items: center; justify-content: center; color: #777; font-size: 10px;">
      PHOTO
    </div>
    <div style="color: #e0e0e0; font-family: sans-serif; flex-grow: 1;">
      <div style="font-weight: 600; font-size: 13px; margin-bottom: 2px; line-height: 1.2;">${name}</div>
      <div style="color: #4ade80; font-size: 12px; font-weight: bold;">${price}</div>
    </div>
    <button style="width: 100%; padding: 6px; background: #3b82f6; color: white; border: none; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 11px;">
      LINK
    </button>
  </div>
`;

// Create the UI Resource (The Carousel)
const productsUI = createUIResource({
  uri: 'ui://products/carousel',
  content: {
    type: 'rawHtml',
    htmlString: `
        <div style="display: flex; align-items: center; gap: 12px; overflow-x: auto; overflow-y: hidden; padding: 12px; background: #0f0f0f; width: 100%; height: 100%; box-sizing: border-box; scrollbar-width: thin;">
          ${createCard('Wireless Headphones', '$120.00')}
          ${createCard('Mechanical Keyboard', '$85.50')}
          ${createCard('Gaming Mouse', '$45.99')}
          ${createCard('4K Monitor', '$299.00')}
        </div>

        <script>
          // 1. Tell Claude the UI is attempting to load
          window.parent.postMessage({
            jsonrpc: "2.0",
            id: 1,
            method: "ui/initialize",
            params: { protocolVersion: "2025-06-18", capabilities: {} }
          }, "*");
          
          // 2. Tell Claude the UI has finished loading and is ready
          window.parent.postMessage({
            jsonrpc: "2.0",
            method: "ui/notifications/initialized",
            params: {}
          }, "*");
        </script>
      `
  },
  encoding: 'text'
});

// 3. Register the UI Resource (Fixed for Claude)
registerAppResource(server, 'products_carousel_ui', productsUI.resource.uri, {}, async () => ({
  contents: [{
    // Spread the existing resource data (uri, text, etc.)
    ...productsUI.resource,
    // OVERRIDE the MIME type so Claude knows it's a safe UI app
    mimeType: "text/html;profile=mcp-app"
  }]
}));

// 4. Register the tool
registerAppTool(server, 'search_products', {
  description: 'Searches for products and displays them in a visual carousel',
  inputSchema: {},
  _meta: { ui: { resourceUri: productsUI.resource.uri } }
}, async () => {
  return { content: [{ type: 'text', text: 'I have displayed the product carousel!' }] };
});

// 5. Start the server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Products UI Server is running!');
}

main().catch(console.error);