import json
import os

from openai import OpenAI


def call_gpt(system_prompt: str, user_prompt: str, model: str = "gpt-4o") -> str:
    """Call GPT with the given prompts and return the raw response string."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    resp = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        response_format={"type": "json_object"},
    )
    return resp.choices[0].message.content
