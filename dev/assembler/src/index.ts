import * as fs from 'fs';
import * as path from 'path';
import Handlebars from 'handlebars';

interface GeneratedTool {
  name: string;
  code: string;
  description: string;
}

interface ToolsManifest {
  tools: GeneratedTool[];
}

function parseArgs(): { manifest: string; output: string } {
  const args = process.argv.slice(2);
  const manifestIdx = args.indexOf('--manifest');
  const outputIdx = args.indexOf('--output');

  if (manifestIdx === -1 || outputIdx === -1) {
    console.error('Usage: node index.js --manifest <path> --output <dir>');
    process.exit(1);
  }

  return {
    manifest: args[manifestIdx + 1],
    output: args[outputIdx + 1],
  };
}

function main() {
  const { manifest: manifestPath, output: outputDir } = parseArgs();

  const manifest: ToolsManifest = JSON.parse(fs.readFileSync(manifestPath, 'utf-8'));

  // Templates are at dev/templates/ relative to dev/assembler/
  const templatesDir = path.join(__dirname, '..', '..', 'templates');
  const serverHbs = fs.readFileSync(path.join(templatesDir, 'mcp_server', 'server.hbs'), 'utf-8');
  const carouselHtml = fs.readFileSync(path.join(templatesDir, 'ui', 'carousel.html'), 'utf-8');

  // Compile and render the MCP server template
  const template = Handlebars.compile(serverHbs);
  const indexTs = template({ tools: manifest.tools });

  // Write output files
  fs.mkdirSync(outputDir, { recursive: true });
  fs.writeFileSync(path.join(outputDir, 'index.ts'), indexTs);
  fs.writeFileSync(path.join(outputDir, 'carousel.html'), carouselHtml);

  // Generate package.json for the output server
  const packageJson = {
    name: 'generated-commerce-mcp',
    version: '1.0.0',
    description: 'Auto-generated MCP server by Base55',
    type: 'commonjs',
    scripts: {
      start: 'npx tsx index.ts',
    },
    dependencies: {
      '@mcp-ui/server': '^6.1.0',
      '@modelcontextprotocol/ext-apps': '^1.2.0',
      '@modelcontextprotocol/sdk': '^1.27.1',
      zod: '^4.3.6',
    },
    devDependencies: {
      '@types/node': '^25.3.5',
      tsx: '^4.21.0',
      typescript: '^5.9.3',
    },
  };
  fs.writeFileSync(path.join(outputDir, 'package.json'), JSON.stringify(packageJson, null, 2));

  // Generate tsconfig.json
  const tsConfig = {
    compilerOptions: {
      target: 'ES2020',
      module: 'commonjs',
      lib: ['ES2020'],
      strict: true,
      esModuleInterop: true,
      skipLibCheck: true,
      resolveJsonModule: true,
    },
  };
  fs.writeFileSync(path.join(outputDir, 'tsconfig.json'), JSON.stringify(tsConfig, null, 2));

  console.log(`[Assembler] Generated MCP server in: ${outputDir}`);
  console.log(`[Assembler] Tools: ${manifest.tools.map((t) => t.name).join(', ')}`);
  console.log(`[Assembler] Next steps:`);
  console.log(`  cd ${outputDir} && npm install && npm start`);
}

main();
