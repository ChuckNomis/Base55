# POC Build Plan: OpenAPI-to-MCP Tool Generator Using GPT

## Objective
The goal of this proof of concept (POC) is to create a minimal and simple system that takes:
- An OpenAPI specification from a company (e.g., product API)
- A single predefined template (e.g., "Products") that defines a desired output schema and tool behavior

…and uses GPT to generate the MCP-compatible tool definitions automatically. This POC does **not** build the full MCP server or UI; it focuses only on demonstrating GPT’s ability to match OpenAPI endpoints to tool definitions.

---

## Step-by-Step Plan

### 1. Explain What We're Building
We are building a minimal system that proves we can:
- Provide a company OpenAPI spec
- Define a simple template with tool(s) and the desired input/output schemas
- Use GPT to read both and generate a valid Python tool definition that conforms to the FastMCP format

This mimics the most critical part of the larger architecture: the ability to take arbitrary APIs and map them into known tool shapes.

---

### 2. Create a Simple Template File (JSON)
Define a template that describes the domain "Products". Save this as `template_products.json`.

```json
{
  "template_id": "products",
  "generation_prompt": "You are an expert Python backend developer. Given an OpenAPI spec and the tool definition below, generate a FastMCP-compatible Python tool that matches the spec and returns data shaped to the output schema.",
  "tools": [
    {
      "name": "search_products",
      "description": "Search for products by a keyword",
      "input_schema": {
        "type": "object",
        "properties": {
          "query": { "type": "string" }
        },
        "required": ["query"]
      },
      "output_schema": {
        "type": "object",
        "properties": {
          "products": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "id": { "type": "string" },
                "title": { "type": "string" },
                "price": { "type": "number" },
                "image_url": { "type": "string" }
              },
              "required": ["id", "title", "price"]
            }
          }
        },
        "required": ["products"]
      }
    }
  ]
}
```

---

### 3. Sample Python Script (poc_generate.py)
Create a simple Python file `poc_generate.py` that:
- Loads the template JSON
- Loads a sample OpenAPI spec (as a JSON file)
- For each tool in the template:
  - Constructs a prompt and sends it to GPT
  - Prints the result

No server. No packaging. Just simple script behavior.

```python
import json
import openai

openai.api_key = "YOUR_API_KEY"

# Load inputs
with open("template_products.json") as f:
    template = json.load(f)

with open("sample_openapi.json") as f:
    openapi_spec = json.load(f)

# Prompt engine
def build_prompt(tool, spec, base_prompt):
    return f"""
{base_prompt}

OpenAPI Spec:
{json.dumps(spec)[:5000]}

Tool Definition:
Name: {tool['name']}
Description: {tool['description']}
Input Schema: {json.dumps(tool['input_schema'])}
Output Schema: {json.dumps(tool['output_schema'])}
"""

# Send to GPT
for tool in template["tools"]:
    prompt = build_prompt(tool, openapi_spec, template["generation_prompt"])
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}]
    )
    print("\n=== Tool Output ===")
    print(response.choices[0].message.content)
```

---

### 4. Run & Test
- Use a public or mock OpenAPI spec (e.g., Fake Store API)
- Run `python poc_generate.py`
- Observe the generated code output from GPT
- Review for quality and correctness

---

## Summary
This plan focuses only on the critical POC flow:
- One simple template (Products)
- One input OpenAPI
- One script
- One GPT call

Everything is minimal and testable. Once this POC is working, we can move forward with UI generation, full MCP server automation, and template switching.
