"""
CLI entrypoint for the Base55 generator.

Usage:
    python -m dev.generator.generate \
        --openapi http://127.0.0.1:8001/openapi.json \
        --template dev/templates/products.json \
        --output-dir dev/generated_server/
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


def load_json(path: str) -> dict:
    parsed = urlparse(path)
    if parsed.scheme in ("http", "https"):
        import httpx
        resp = httpx.get(path, timeout=10)
        resp.raise_for_status()
        return resp.json()
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Base55: Generate MCP server from OpenAPI spec + template")
    parser.add_argument("--openapi", required=True, help="Path or URL to OpenAPI JSON")
    parser.add_argument("--template", required=True, help="Path to template JSON")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for generated server")
    args = parser.parse_args()

    from .core import make_all_tools

    print(f"[Generator] Loading OpenAPI spec from: {args.openapi}")
    openapi_spec = load_json(args.openapi)

    print(f"[Generator] Loading template from: {args.template}")
    template = load_json(args.template)

    manifest = make_all_tools(openapi_spec, template)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = args.output_dir / "tools_manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2)

    print(f"[Generator] Wrote manifest: {manifest_path}")
    print(f"[Generator] Generated {len(manifest.tools)} tool(s): {[t.name for t in manifest.tools]}")

    # Run assembler if built
    assembler_script = Path(__file__).parent.parent / "assembler" / "dist" / "index.js"
    if assembler_script.exists():
        print("[Generator] Running assembler...")
        result = subprocess.run(
            ["node", str(assembler_script), "--manifest", str(manifest_path), "--output", str(args.output_dir)],
        )
        if result.returncode != 0:
            print("[Generator] Assembler failed.", file=sys.stderr)
            sys.exit(1)
    else:
        print(f"[Generator] Assembler not built yet.")
        print(f"[Generator] To build: cd dev/assembler && npm install && npm run build")
        print(f"[Generator] Manifest saved to {manifest_path} — you can run the assembler manually.")


if __name__ == "__main__":
    main()
