from pydantic import BaseModel


class GeneratedTool(BaseModel):
    name: str
    code: str
    description: str
    fetch_all: bool = False


class ToolsManifest(BaseModel):
    tools: list[GeneratedTool]
