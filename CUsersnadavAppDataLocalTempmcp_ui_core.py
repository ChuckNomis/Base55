

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, Literal, Optional, Union
import base64

# --------------------------
# Types & Constants
# --------------------------

URI = str  # Must start with "ui://"

MimeType = Literal[
    "text/html",
    "text/uri-list",
    "application/vnd.mcp-ui.remote-dom+javascript; framework=react",
    "application/vnd.mcp-ui.remote-dom+javascript; framework=webcomponents",
]

UIMetadataKey = {
    "PREFERRED_FRAME_SIZE": "preferred-frame-size",
    "INITIAL_RENDER_DATA": "initial-render-data",
}

UI_METADATA_PREFIX = "mcpui.dev/ui-"

InternalMessageType = {
    "UI_MESSAGE_RECEIVED": "ui-message-received",
    "UI_MESSAGE_RESPONSE": "ui-message-response",
    "UI_SIZE_CHANGE": "ui-size-change",
    "UI_LIFECYCLE_IFRAME_READY": "ui-lifecycle-iframe-ready",
    "UI_LIFECYCLE_IFRAME_RENDER_DATA": "ui-lifecycle-iframe-render-data",
}

ReservedUrlParams = {
    "WAIT_FOR_RENDER_DATA": "waitForRenderData",
}


# --------------------------
# Resource Content Payloads
# --------------------------

@dataclass
class RawHtmlContent:
    type: Literal["rawHtml"]
    htmlString: str


@dataclass
class ExternalUrlContent:
    type: Literal["externalUrl"]
    iframeUrl: str


@dataclass
class RemoteDomContent:
    type: Literal["remoteDom"]
    script: str
    framework: Literal["react", "webcomponents"]


ResourceContentPayload = Union[RawHtmlContent, ExternalUrlContent, RemoteDomContent]


# --------------------------
# Resource Representations
# --------------------------

@dataclass
class HTMLTextContent:
    uri: URI
    mimeType: MimeType
    text: str
    blob: Optional[str] = None
    _meta: Optional[Dict[str, Any]] = None


@dataclass
class Base64BlobContent:
    uri: URI
    mimeType: MimeType
    blob: str
    text: Optional[str] = None
    _meta: Optional[Dict[str, Any]] = None


UIResource = Dict[str, Union[str, HTMLTextContent, Base64BlobContent]]


@dataclass
class CreateUIResourceOptions:
    uri: URI
    content: ResourceContentPayload
    encoding: Literal["text", "blob"]
    uiMetadata: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    resourceProps: Optional[Dict[str, Any]] = None


# --------------------------
# Utils
# --------------------------

def utf8_to_base64(s: str) -> str:
    return base64.b64encode(s.encode("utf-8")).decode("utf-8")


def get_additional_resource_props(options: CreateUIResourceOptions) -> Dict[str, Any]:
    props = dict(options.resourceProps or {})

    if options.uiMetadata or options.metadata:
        ui_prefixed_metadata = {
            f"{UI_METADATA_PREFIX}{k}": v for k, v in (options.uiMetadata or {}).items()
        }
        props["_meta"] = {
            **ui_prefixed_metadata,
            **(options.metadata or {}),
            **props.get("_meta", {}),
        }

    return props


# --------------------------
# Resource Factory
# --------------------------

def create_ui_resource(options: CreateUIResourceOptions) -> Dict[str, Any]:
    if not options.uri.startswith("ui://"):
        raise ValueError("MCP-UI SDK: URI must start with 'ui://'.")

    if isinstance(options.content, RawHtmlContent):
        actual_content = options.content.htmlString
        mime_type: MimeType = "text/html"

    elif isinstance(options.content, ExternalUrlContent):
        actual_content = options.content.iframeUrl
        mime_type = "text/uri-list"

    elif isinstance(options.content, RemoteDomContent):
        actual_content = options.content.script
        mime_type = (
            f"application/vnd.mcp-ui.remote-dom+javascript; framework={options.content.framework}"  # type: ignore
        )

    else:
        raise ValueError(f"MCP-UI SDK: Invalid content.type: {options.content}")

    if options.encoding == "text":
        resource = HTMLTextContent(
            uri=options.uri,
            mimeType=mime_type,
            text=actual_content,
            **get_additional_resource_props(options),
        )
    elif options.encoding == "blob":
        resource = Base64BlobContent(
            uri=options.uri,
            mimeType=mime_type,
            blob=utf8_to_base64(actual_content),
            **get_additional_resource_props(options),
        )
    else:
        raise ValueError(f"MCP-UI SDK: Invalid encoding type: {options.encoding}")

    # ✅ return a dict so MCP can consume it
    return {
        "type": "resource",
        "resource": asdict(resource),
    }

# --------------------------
# UI Action Results
# --------------------------

@dataclass
class UIActionResultToolCall:
    type: Literal["tool"] = "tool"
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIActionResultPrompt:
    type: Literal["prompt"] = "prompt"
    payload: Dict[str, str] = field(default_factory=dict)


@dataclass
class UIActionResultLink:
    type: Literal["link"] = "link"
    payload: Dict[str, str] = field(default_factory=dict)


@dataclass
class UIActionResultIntent:
    type: Literal["intent"] = "intent"
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UIActionResultNotification:
    type: Literal["notify"] = "notify"
    payload: Dict[str, str] = field(default_factory=dict)


UIActionResult = Union[
    UIActionResultToolCall,
    UIActionResultPrompt,
    UIActionResultLink,
    UIActionResultIntent,
    UIActionResultNotification,
]


def ui_action_result_tool_call(tool_name: str, params: Dict[str, Any]) -> UIActionResultToolCall:
    return UIActionResultToolCall(payload={"toolName": tool_name, "params": params})


def ui_action_result_prompt(prompt: str) -> UIActionResultPrompt:
    return UIActionResultPrompt(payload={"prompt": prompt})


def ui_action_result_link(url: str) -> UIActionResultLink:
    return UIActionResultLink(payload={"url": url})


def ui_action_result_intent(intent: str, params: Dict[str, Any]) -> UIActionResultIntent:
    return UIActionResultIntent(payload={"intent": intent, "params": params})


def ui_action_result_notification(message: str) -> UIActionResultNotification:
    return UIActionResultNotification(payload={"message": message})
