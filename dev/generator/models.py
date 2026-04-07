from pydantic import BaseModel


class GeneratedTool(BaseModel):
    name: str
    code: str
    description: str


class ToolsManifest(BaseModel):
    tools: list[GeneratedTool]
