#!/usr/bin/env python3
"""Validate a generated make-workflow-canvas HTML artifact."""

from __future__ import annotations

import base64
import copy
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


EXPECTED_DIAGNOSTIC_FIELDS = {
    "node_id",
    "edge_id",
    "port_id",
    "error_code",
    "count",
    "duration_ms",
}
RESOURCE_ATTRIBUTES = {
    "a": {"href", "ping"},
    "area": {"href", "ping"},
    "audio": {"src"},
    "base": {"href"},
    "blockquote": {"cite"},
    "body": {"background"},
    "button": {"formaction"},
    "del": {"cite"},
    "embed": {"src"},
    "form": {"action"},
    "frame": {"longdesc", "src"},
    "html": {"manifest"},
    "iframe": {"longdesc", "src"},
    "image": {"href", "xlink:href"},
    "img": {"longdesc", "src", "srcset"},
    "input": {"formaction", "src"},
    "ins": {"cite"},
    "link": {"href"},
    "object": {"data"},
    "q": {"cite"},
    "script": {"src"},
    "source": {"src", "srcset"},
    "track": {"src"},
    "use": {"href", "xlink:href"},
    "video": {"poster", "src"},
}
DYNAMIC_RESOURCE_ATTRIBUTES = {
    attribute.lower()
    for attributes in RESOURCE_ATTRIBUTES.values()
    for attribute in attributes
} | {"srcdoc"}
ALLOWED_GRAPH_MODES = {"design", "contracts", "preview", "trace", "docs"}
ALLOWED_NODE_STATUSES = {"active", "draft", "paused", "failing", "unknown"}
ALLOWED_EDGE_KINDS = {"data", "control", "error", "event", "trace"}
ALLOWED_STEP_STATUSES = {"pending", "running", "succeeded", "failed", "skipped"}
MAX_RUNTIME_MS = 3_600_000


class ValidationError(RuntimeError):
    """Raised when the workflow canvas bundle violates its contract."""


class ReferenceParser(HTMLParser):
    """Collect the structural information needed for static validation."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.elements: list[tuple[str, dict[str, str]]] = []
        self.scripts: list[dict[str, Any]] = []
        self.styles: list[dict[str, Any]] = []
        self.doctypes: list[str] = []
        self._script: dict[str, Any] | None = None
        self._style: dict[str, Any] | None = None

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        normalized = {key.lower(): value or "" for key, value in attrs}
        lowered_tag = tag.lower()
        self.elements.append((lowered_tag, normalized))
        if lowered_tag == "script":
            self._script = {"attrs": normalized, "content": []}
            self.scripts.append(self._script)
        elif lowered_tag == "style":
            self._style = {"attrs": normalized, "content": []}
            self.styles.append(self._style)

    def handle_startendtag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        self.handle_starttag(tag, attrs)
        if tag.lower() == "script":
            self._script = None
        elif tag.lower() == "style":
            self._style = None

    def handle_endtag(self, tag: str) -> None:
        lowered_tag = tag.lower()
        if lowered_tag == "script":
            self._script = None
        elif lowered_tag == "style":
            self._style = None

    def handle_decl(self, decl: str) -> None:
        self.doctypes.append(decl.strip().lower())

    def handle_data(self, data: str) -> None:
        if self._script is not None:
            self._script["content"].append(data)
        elif self._style is not None:
            self._style["content"].append(data)

    def has_element(self, tag: str, **attributes: str) -> bool:
        for element_tag, element_attrs in self.elements:
            if element_tag != tag:
                continue
            if all(_attribute_matches(element_attrs, key, value) for key, value in attributes.items()):
                return True
        return False

    def values(self, attribute: str) -> set[str]:
        return {
            attrs[attribute]
            for _tag, attrs in self.elements
            if attribute in attrs
        }


def _attribute_matches(attrs: dict[str, str], key: str, value: str) -> bool:
    actual = attrs.get(key)
    if actual is None:
        return False
    if key == "class":
        return value in actual.split()
    return actual == value


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def parse_reference(reference: str) -> ReferenceParser:
    parser = ReferenceParser()
    try:
        parser.feed(reference)
        parser.close()
    except Exception as error:
        raise ValidationError(f"reference HTML does not parse: {error}") from error
    return parser


def validate_html_structure(parser: ReferenceParser) -> None:
    require(parser.doctypes == ["doctype html"], "artifact must contain exactly one HTML5 doctype")
    for tag in ("html", "head", "body", "title"):
        require(parser.has_element(tag), f"artifact is missing required {tag} element")
    require(
        parser.has_element("meta", charset="UTF-8")
        or parser.has_element("meta", charset="utf-8"),
        "artifact must declare UTF-8 charset",
    )
    require(
        any(tag == "meta" and attrs.get("name", "").lower() == "viewport" for tag, attrs in parser.elements),
        "artifact must include a viewport meta element",
    )
    require(parser.styles, "artifact must contain inline CSS")
    require(
        all(not style["attrs"] for style in parser.styles),
        "artifact style elements must be inline and attribute-free",
    )


def executable_javascript(parser: ReferenceParser) -> str:
    require(len(parser.scripts) == 2, "reference must contain exactly one data script and one executable script")
    executable: list[str] = []
    data_scripts = 0
    for script in parser.scripts:
        attrs = script["attrs"]
        if attrs.get("id") == "workflow-data":
            data_scripts += 1
            require(
                attrs == {"type": "application/octet-stream", "id": "workflow-data"},
                "#workflow-data must have only id and application/octet-stream type attributes",
            )
            continue
        require(not attrs, "executable script must be inline and have no attributes or type")
        content = "".join(script["content"])
        require(content.strip(), "executable script must not be empty")
        executable.append(content)
    require(data_scripts == 1, "reference must contain exactly one #workflow-data script")
    require(len(executable) == 1, "reference must contain exactly one executable inline script")
    return executable[0]


def embedded_model(parser: ReferenceParser) -> dict[str, Any]:
    matches = [
        script
        for script in parser.scripts
        if script["attrs"].get("id") == "workflow-data"
    ]
    require(len(matches) == 1, "reference must contain exactly one #workflow-data script")
    script = matches[0]
    require(
        script["attrs"].get("type") == "application/octet-stream",
        "#workflow-data must be non executable application/octet-stream data",
    )
    encoded = "".join(script["content"])
    require(
        re.fullmatch(r"[A-Za-z0-9+/=\s]+", encoded) is not None,
        "#workflow-data must contain Base64 characters only",
    )
    compact = re.sub(r"\s+", "", encoded)
    try:
        decoded = base64.b64decode(compact, validate=True).decode("utf-8")
        model = json.loads(decoded)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(f"#workflow-data does not decode to UTF 8 JSON: {error}") from error
    require(isinstance(model, dict), "embedded workflow model must be a JSON object")
    require(
        model.get("schema_version") == "workflow-canvas/1",
        "embedded workflow model schema_version must be workflow-canvas/1",
    )
    return model


def _strip_javascript_noncode(source: str) -> str:
    """Remove comments and string bodies while preserving executable token spacing."""
    output = list(source)
    index = 0
    state = "code"
    quote = ""
    template_depth: list[int] = []
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if state == "code":
            if character == "/" and following == "/":
                output[index] = output[index + 1] = " "
                index += 2
                state = "line_comment"
                continue
            if character == "/" and following == "*":
                output[index] = output[index + 1] = " "
                index += 2
                state = "block_comment"
                continue
            if character in {"'", '"'}:
                quote = character
                output[index] = " "
                index += 1
                state = "string"
                continue
            if character == "`":
                output[index] = " "
                index += 1
                state = "template"
                continue
            if template_depth:
                if character == "{":
                    template_depth[-1] += 1
                elif character == "}":
                    if template_depth[-1] == 0:
                        output[index] = " "
                        template_depth.pop()
                        index += 1
                        state = "template"
                        continue
                    template_depth[-1] -= 1
        elif state == "line_comment":
            if character in "\r\n":
                state = "code"
            else:
                output[index] = " "
        elif state == "block_comment":
            output[index] = " "
            if character == "*" and following == "/":
                output[index + 1] = " "
                index += 2
                state = "code"
                continue
        elif state == "string":
            output[index] = " "
            if character == "\\":
                if index + 1 < len(source):
                    output[index + 1] = " "
                index += 2
                continue
            if character == quote:
                state = "code"
        elif state == "template":
            output[index] = " "
            if character == "\\":
                if index + 1 < len(source):
                    output[index + 1] = " "
                index += 2
                continue
            if character == "`":
                state = "code"
            elif character == "$" and following == "{":
                output[index + 1] = " "
                template_depth.append(0)
                index += 2
                state = "code"
                continue
        index += 1
    return "".join(output)


def _javascript_tokens(source: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    index = 0
    while index < len(source):
        character = source[index]
        following = source[index + 1] if index + 1 < len(source) else ""
        if character.isspace():
            index += 1
            continue
        if character == "/" and following == "/":
            index += 2
            while index < len(source) and source[index] not in "\r\n":
                index += 1
            continue
        if character == "/" and following == "*":
            end = source.find("*/", index + 2)
            index = len(source) if end < 0 else end + 2
            continue
        if character in {"'", '"', "`"}:
            quote = character
            token_kind = "template" if quote == "`" else "string"
            index += 1
            value: list[str] = []
            while index < len(source):
                current = source[index]
                if current == "\\" and index + 1 < len(source):
                    value.append(source[index + 1])
                    index += 2
                    continue
                if current == quote:
                    index += 1
                    break
                value.append(current)
                index += 1
            tokens.append((token_kind, "".join(value)))
            continue
        if character.isalpha() or character in {"_", "$"}:
            end = index + 1
            while end < len(source) and (source[end].isalnum() or source[end] in {"_", "$"}):
                end += 1
            tokens.append(("identifier", source[index:end]))
            index = end
            continue
        tokens.append(("punctuation", character))
        index += 1
    return tokens


def _anchor_download_variables(javascript: str) -> set[str]:
    tokens = _javascript_tokens(javascript)
    anchors: set[str] = set()
    for index in range(len(tokens) - 9):
        window = tokens[index : index + 10]
        values = [token[1] for token in window]
        if (
            values[0] in {"const", "let", "var"}
            and window[1][0] == "identifier"
            and values[2:7] == ["=", "document", ".", "createElement", "("]
            and window[7] == ("string", "a")
            and values[8:10] == [")", ";"]
        ):
            anchors.add(values[1])
    return anchors


def _strip_css_comments(css: str) -> str:
    return re.sub(r"/\*.*?\*/", "", css, flags=re.DOTALL)


def _strip_quoted_strings(value: str) -> str:
    return re.sub(r"(['\"])(?:\\.|(?!\1).)*\1", "", value, flags=re.DOTALL)


def _validate_css_no_remote_paths(css: str, context: str) -> None:
    css_without_comments = _strip_css_comments(css)
    require(
        re.search(r"@\s*import\b", css_without_comments, re.IGNORECASE) is None,
        f"{context} must not use CSS @import",
    )
    require(
        re.search(
            r"(?:^|[^-])\bimage-set\s*\(|-webkit-image-set\s*\(",
            css_without_comments,
            re.IGNORECASE,
        )
        is None,
        f"{context} must not use CSS image-set",
    )
    require(
        "\\" not in _strip_quoted_strings(css_without_comments),
        f"{context} must not use escaped CSS identifiers",
    )
    for match in re.finditer(
        r"(?<![A-Za-z0-9_.-])url\s*\(\s*([^)]*?)\s*\)",
        css_without_comments,
        re.IGNORECASE | re.DOTALL,
    ):
        value = match.group(1).strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1].strip()
        require(
            re.fullmatch(r"#[A-Za-z_][A-Za-z0-9_.:-]*", value) is not None,
            f"{context} contains non-fragment CSS URL: {value}",
        )


def _first_call_argument(
    tokens: list[tuple[str, str]], open_parenthesis: int
) -> list[tuple[str, str]]:
    argument: list[tuple[str, str]] = []
    depth = 0
    for token in tokens[open_parenthesis + 1 :]:
        if token[0] != "punctuation":
            argument.append(token)
            continue
        value = token[1]
        if value in {"(", "[", "{"}:
            depth += 1
            argument.append(token)
            continue
        if value in {")",
            "]",
            "}",
        }:
            if value == ")" and depth == 0:
                return argument
            depth -= 1
            argument.append(token)
            continue
        if value == "," and depth == 0:
            return argument
        argument.append(token)
    return argument


def _constant_string(tokens: list[tuple[str, str]]) -> str | None:
    if not tokens or len(tokens) % 2 == 0:
        return None
    parts: list[str] = []
    for index, token in enumerate(tokens):
        if index % 2 == 0:
            if token[0] != "string":
                return None
            parts.append(token[1])
        elif token != ("punctuation", "+"):
            return None
    return "".join(parts)


def _validate_javascript_resource_setters(javascript: str) -> None:
    tokens = _javascript_tokens(javascript)
    for index, token in enumerate(tokens):
        if token != ("punctuation", "["):
            continue
        depth = 0
        for closing_index in range(index + 1, len(tokens)):
            candidate = tokens[closing_index]
            if candidate == ("punctuation", "["):
                depth += 1
            elif candidate == ("punctuation", "]"):
                if depth:
                    depth -= 1
                    continue
                if (
                    closing_index + 1 < len(tokens)
                    and tokens[closing_index + 1] == ("punctuation", "(")
                ):
                    method_name = _constant_string(tokens[index + 1 : closing_index])
                    require(
                        method_name not in {"setAttribute", "setAttributeNS"},
                        "artifact must not call attribute setters through bracket notation",
                    )
                break

    for index, token in enumerate(tokens):
        if token in {
            ("identifier", "setAttributeNS"),
            ("string", "setAttributeNS"),
        }:
            raise ValidationError(
                "artifact must not use setAttributeNS because it can assign resource attributes"
            )
        if token == ("string", "setAttribute"):
            if (
                index > 0
                and index + 1 < len(tokens)
                and tokens[index - 1] == ("punctuation", "[")
                and tokens[index + 1] == ("punctuation", "]")
            ):
                raise ValidationError(
                    "artifact must not call setAttribute through bracket notation"
                )
            continue
        if token != ("identifier", "setAttribute"):
            continue
        require(
            index > 0
            and index + 1 < len(tokens)
            and tokens[index - 1] == ("punctuation", ".")
            and tokens[index + 1] == ("punctuation", "("),
            "artifact must use direct setAttribute calls only",
        )
        attribute = _constant_string(_first_call_argument(tokens, index + 1))
        require(
            attribute is not None,
            "artifact setAttribute names must be one constant string",
        )
        normalized_attribute = attribute.strip().lower()
        require(
            normalized_attribute not in DYNAMIC_RESOURCE_ATTRIBUTES
            and normalized_attribute != "style"
            and not normalized_attribute.startswith("on"),
            f"artifact must not dynamically assign unsafe attribute {normalized_attribute}",
        )


def validate_no_remote_or_executable_paths(
    artifact: str, parser: ReferenceParser, javascript: str
) -> None:
    for tag, attrs in parser.elements:
        for attribute in RESOURCE_ATTRIBUTES.get(tag, set()):
            if attribute not in attrs:
                continue
            require(
                not attrs[attribute].strip(),
                f"artifact {tag} {attribute} resource attribute must be empty",
            )
        require(
            not (tag == "iframe" and "srcdoc" in attrs),
            "artifact must not use iframe srcdoc",
        )
        require(
            not (
                tag == "meta"
                and attrs.get("http-equiv", "").strip().lower() == "refresh"
            ),
            "artifact must not use meta refresh",
        )
        for attribute, value in attrs.items():
            require(
                not attribute.startswith("on"),
                f"artifact contains inline event handler attribute {attribute}",
            )
            compact_value = re.sub(r"[\x00-\x20]+", "", value).lower()
            require(
                not compact_value.startswith("javascript:"),
                f"artifact contains javascript URI in {tag} {attribute}",
            )
            require(
                not compact_value.startswith("data:"),
                f"artifact contains data URI in {tag} {attribute}",
            )
        if "style" in attrs:
            _validate_css_no_remote_paths(
                attrs["style"],
                f"artifact inline style on {tag}",
            )

    css = "\n".join("".join(style["content"]) for style in parser.styles)
    _validate_css_no_remote_paths(css, "artifact CSS")
    _validate_javascript_resource_setters(javascript)

    code = _strip_javascript_noncode(javascript)
    code_without_blob_download = code
    anchor_variables = _anchor_download_variables(javascript)
    blob_url_variables = re.findall(
        r"\b(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*URL\s*\.\s*createObjectURL\s*\(",
        code,
    )
    for anchor in anchor_variables:
        code_without_blob_download = re.sub(
            rf"\b{re.escape(anchor)}\s*\.\s*href\s*=\s*URL\s*\.\s*createObjectURL\s*\(\s*[A-Za-z_$][\w$]*\s*\)",
            "",
            code_without_blob_download,
        )
        for variable in blob_url_variables:
            code_without_blob_download = re.sub(
                rf"\b{re.escape(anchor)}\s*\.\s*href\s*=\s*{re.escape(variable)}\b",
                "",
                code_without_blob_download,
            )
    forbidden_javascript = {
        "import": r"(?<![.$])\bimport\b",
        "fetch": r"\bfetch\s*\(",
        "XMLHttpRequest": r"\bXMLHttpRequest\b",
        "WebSocket": r"\bWebSocket\b",
        "EventSource": r"\bEventSource\b",
        "Worker": r"\b(?:SharedWorker|Worker)\b",
        "sendBeacon": r"\bnavigator\s*\.\s*sendBeacon\s*\(",
        "service worker": r"\bnavigator\s*\.\s*serviceWorker\b",
        "importScripts": r"\bimportScripts\s*\(",
        "navigation": r"(?:\b(?:window|document|top|parent|self)\s*\.\s*(?:open|location)\b|(?<![.$])\blocation\s*(?:=|\.\s*(?:assign|replace)\s*\())",
        "eval": r"(?<![.$])\beval\s*\(",
        "Function constructor": r"(?:\bnew\s+Function\b|(?<![.$])\bFunction\s*\()",
        "resource property assignment": r"\.\s*(?:src|srcset|href|action|formAction|poster|data|srcdoc)\s*=",
    }
    for label, pattern in forbidden_javascript.items():
        require(
            re.search(pattern, code_without_blob_download, re.DOTALL) is None,
            f"artifact must not use {label}",
        )

def _require_unique(values: list[Any], label: str) -> None:
    require(all(isinstance(value, str) and value for value in values), f"{label} must be nonempty strings")
    require(len(values) == len(set(values)), f"{label} must be unique")


def _require_list(value: Any, label: str) -> list[Any]:
    require(isinstance(value, list), f"{label} must be an array")
    return value


def _require_object(value: Any, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} must be an object")
    return value


def _require_exact_keys(
    value: dict[str, Any],
    required: set[str],
    label: str,
    optional: set[str] | None = None,
) -> None:
    allowed = required | (optional or set())
    keys = set(value)
    missing = required - keys
    unexpected = keys - allowed
    require(not missing, f"{label} is missing keys: {sorted(missing)}")
    require(not unexpected, f"{label} has unexpected keys: {sorted(unexpected)}")


def _require_boolean(value: Any, label: str) -> bool:
    require(isinstance(value, bool), f"{label} must be a boolean")
    return value


def _require_finite_number(
    value: Any,
    label: str,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
    positive: bool = False,
) -> float:
    require(
        isinstance(value, (int, float)) and not isinstance(value, bool),
        f"{label} must be a finite number",
    )
    try:
        numeric = float(value)
    except (OverflowError, ValueError):
        raise ValidationError(f"{label} must be a finite number") from None
    require(math.isfinite(numeric), f"{label} must be a finite number")
    if minimum is not None:
        require(numeric >= minimum, f"{label} must be at least {minimum:g}")
    if maximum is not None:
        require(numeric <= maximum, f"{label} must be at most {maximum:g}")
    if positive:
        require(numeric > 0, f"{label} must be positive")
    return numeric


def _normalized_integer(
    value: Any,
    label: str,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
    positive: bool = False,
) -> int:
    numeric = _require_finite_number(
        value,
        label,
        minimum=minimum,
        maximum=maximum,
        positive=positive,
    )
    require(numeric.is_integer(), f"{label} must be an integer")
    normalized = int(numeric)
    return 0 if normalized == 0 else normalized


def _validate_port(
    port: Any,
    label: str,
    schema_ids: set[str],
) -> dict[str, Any]:
    port = _require_object(port, label)
    require(isinstance(port.get("id"), str) and port["id"], f"{label}.id is required")
    require(isinstance(port.get("label"), str), f"{label}.label must be a string")
    schema = port.get("schema")
    require(
        isinstance(schema, str) and (schema == "any" or schema in schema_ids),
        f"{label} references unknown schema {schema}",
    )
    _require_boolean(port.get("required"), f"{label}.required")
    _require_boolean(port.get("multiple"), f"{label}.multiple")
    return port


def validate_model(model: dict[str, Any]) -> None:
    artifact = _require_object(model.get("artifact"), "artifact")
    catalog = _require_object(model.get("catalog"), "catalog")
    graph = _require_object(model.get("graph"), "graph")
    runtime = _require_object(model.get("runtime"), "runtime")
    require(isinstance(artifact.get("id"), str) and artifact["id"], "artifact.id is required")
    require(isinstance(artifact.get("version"), str) and artifact["version"], "artifact.version is required")
    require(isinstance(artifact.get("title"), str), "artifact.title must be a string")
    require(isinstance(artifact.get("purpose"), str), "artifact.purpose must be a string")

    graph_metadata = _require_object(graph.get("metadata"), "graph.metadata")
    require(isinstance(graph_metadata.get("name"), str), "graph.metadata.name must be a string")
    require(isinstance(graph_metadata.get("description"), str), "graph.metadata.description must be a string")
    require(
        graph_metadata.get("mode") in ALLOWED_GRAPH_MODES,
        "graph.metadata.mode is invalid",
    )

    categories = _require_list(catalog.get("categories"), "catalog.categories")
    node_types = _require_list(catalog.get("node_types"), "catalog.node_types")
    schemas = _require_list(graph.get("schemas"), "graph.schemas")
    nodes = _require_list(graph.get("nodes"), "graph.nodes")
    edges = _require_list(graph.get("edges"), "graph.edges")

    category_ids = [item.get("id") for item in categories if isinstance(item, dict)]
    type_ids = [item.get("type") for item in node_types if isinstance(item, dict)]
    schema_ids = [item.get("id") for item in schemas if isinstance(item, dict)]
    node_ids = [item.get("id") for item in nodes if isinstance(item, dict)]
    edge_ids = [item.get("id") for item in edges if isinstance(item, dict)]
    require(len(category_ids) == len(categories), "every category must be an object")
    require(len(type_ids) == len(node_types), "every node type must be an object")
    require(len(schema_ids) == len(schemas), "every graph schema must be an object")
    require(len(node_ids) == len(nodes), "every graph node must be an object")
    require(len(edge_ids) == len(edges), "every graph edge must be an object")
    _require_unique(category_ids, "category IDs")
    _require_unique(type_ids, "node type IDs")
    _require_unique(schema_ids, "schema IDs")
    _require_unique(node_ids, "node IDs")
    _require_unique(edge_ids, "edge IDs")

    category_id_set = set(category_ids)
    type_id_set = set(type_ids)
    schema_id_set = set(schema_ids)
    for index, schema in enumerate(schemas):
        schema = _require_object(schema, f"graph.schemas[{index}]")
        require(isinstance(schema.get("label"), str), f"graph.schemas[{index}].label must be a string")

    for index, node_type in enumerate(node_types):
        node_type = _require_object(node_type, f"catalog.node_types[{index}]")
        node_type_id = node_type["type"]
        require(
            node_type.get("category") in category_id_set,
            f"node type {node_type_id} references an unknown category",
        )
        ports = _require_object(node_type.get("ports"), f"node type {node_type_id} ports")
        type_port_ids: list[str] = []
        for direction in ("inputs", "outputs"):
            for port_index, port in enumerate(
                _require_list(ports.get(direction), f"node type {node_type_id} {direction}")
            ):
                validated = _validate_port(
                    port,
                    f"node type {node_type_id} {direction}[{port_index}]",
                    schema_id_set,
                )
                type_port_ids.append(validated["id"])
        _require_unique(type_port_ids, f"node type {node_type_id} port IDs")

    node_by_id: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(nodes):
        node = _require_object(node, f"graph.nodes[{index}]")
        node_id = node["id"]
        node_by_id[node_id] = node
        require(node.get("type") in type_id_set, f"node {node_id} references an unknown type")
        require(node.get("category") in category_id_set, f"node {node_id} references an unknown category")
        require(node.get("status") in ALLOWED_NODE_STATUSES, f"node {node_id} has an invalid status")
        for field in ("label", "description", "owner"):
            require(isinstance(node.get(field), str), f"node {node_id}.{field} must be a string")
        position = _require_object(node.get("position"), f"node {node_id} position")
        for axis in ("x", "y"):
            _normalized_integer(position.get(axis), f"node {node_id} position.{axis}")
        ports = _require_object(node.get("ports"), f"node {node_id} ports")
        port_ids: list[str] = []
        for direction in ("inputs", "outputs"):
            for port_index, port in enumerate(
                _require_list(ports.get(direction), f"node {node_id} {direction}")
            ):
                validated = _validate_port(
                    port,
                    f"node {node_id} {direction}[{port_index}]",
                    schema_id_set,
                )
                port_ids.append(validated["id"])
        _require_unique(port_ids, f"node {node_id} port IDs")
        metadata = _require_object(node.get("metadata"), f"node {node_id} metadata")
        require(
            metadata.get("confidence") in {"high", "medium", "low"},
            f"node {node_id} metadata.confidence is invalid",
        )
        require(
            metadata.get("fact_status") in {"observed", "inferred", "proposed", "unknown"},
            f"node {node_id} metadata.fact_status is invalid",
        )
        evidence = _require_list(metadata.get("evidence"), f"node {node_id} metadata.evidence")
        require(all(isinstance(item, str) for item in evidence), f"node {node_id} evidence must be strings")
        if metadata["fact_status"] == "observed":
            require(bool(evidence), f"node {node_id} observed status requires evidence")

    connections: set[tuple[str, str, str, str]] = set()
    incoming: dict[tuple[str, str], int] = {}
    for edge in edges:
        edge = _require_object(edge, "graph edge")
        edge_id = edge["id"]
        source = _require_object(edge.get("source"), f"edge {edge_id} source")
        target = _require_object(edge.get("target"), f"edge {edge_id} target")
        source_node = node_by_id.get(source.get("node"))
        target_node = node_by_id.get(target.get("node"))
        require(source_node is not None, f"edge {edge_id} source node does not exist")
        require(target_node is not None, f"edge {edge_id} target node does not exist")
        require(source.get("node") != target.get("node"), f"edge {edge_id} is a self connection")
        source_port = next(
            (port for port in source_node["ports"]["outputs"] if port["id"] == source.get("port")),
            None,
        )
        target_port = next(
            (port for port in target_node["ports"]["inputs"] if port["id"] == target.get("port")),
            None,
        )
        require(source_port is not None, f"edge {edge_id} source must reference an output port")
        require(target_port is not None, f"edge {edge_id} target must reference an input port")
        require(edge.get("kind") in ALLOWED_EDGE_KINDS, f"edge {edge_id} has an invalid kind")
        require(isinstance(edge.get("label"), str), f"edge {edge_id}.label must be a string")
        _require_boolean(edge.get("async"), f"edge {edge_id}.async")
        connection = (
            source["node"],
            source["port"],
            target["node"],
            target["port"],
        )
        require(connection not in connections, f"edge {edge_id} duplicates a connection")
        connections.add(connection)
        incoming_key = (target["node"], target["port"])
        incoming[incoming_key] = incoming.get(incoming_key, 0) + 1
        source_schema = source_port["schema"]
        target_schema = target_port["schema"]
        require(
            source_schema == "any" or target_schema == "any" or source_schema == target_schema,
            f"edge {edge_id} connects incompatible schemas {source_schema} and {target_schema}",
        )

    for node_id, node in node_by_id.items():
        for port in node["ports"]["inputs"]:
            count = incoming.get((node_id, port["id"]), 0)
            require(
                not port["required"] or count > 0,
                f"node {node_id} required input {port['id']} is unconnected",
            )
            require(
                port["multiple"] or count <= 1,
                f"node {node_id} input {port['id']} exceeds multiplicity",
            )

    preview = _require_object(runtime.get("preview"), "runtime.preview")
    require(preview.get("kind") == "synthetic", "runtime.preview.kind must be synthetic")
    require(preview.get("label") == "Synthetic preview", "runtime.preview.label must be Synthetic preview")
    for index, step in enumerate(_require_list(preview.get("steps"), "runtime.preview.steps")):
        step = _require_object(step, f"runtime.preview.steps[{index}]")
        require(step.get("node_id") in node_by_id, "runtime.preview step references an unknown node")
        _normalized_integer(
            step.get("offset_ms"),
            f"runtime.preview.steps[{index}].offset_ms",
            minimum=0,
            maximum=MAX_RUNTIME_MS,
        )
        _normalized_integer(
            step.get("duration_ms"),
            f"runtime.preview.steps[{index}].duration_ms",
            maximum=MAX_RUNTIME_MS,
            positive=True,
        )
        if "status" in step:
            require(
                step["status"] in ALLOWED_STEP_STATUSES,
                f"runtime.preview.steps[{index}].status is invalid",
            )
    _require_list(runtime.get("observed_runs"), "runtime.observed_runs")


def validate_ui_and_labels(reference: str, parser: ReferenceParser, javascript: str) -> None:
    landmarks = [
        ("header", {"class": "toolbar", "aria-label": "Workflow toolbar"}),
        ("aside", {"class": "palette", "aria-label": "Node palette"}),
        ("section", {"class": "canvas-shell", "aria-label": "Workflow canvas"}),
        ("aside", {"class": "inspector", "aria-label": "Inspector"}),
        ("section", {"id": "bottom-panel", "aria-label": "Workflow diagnostics"}),
        ("div", {"id": "minimap", "aria-label": "Workflow minimap"}),
        ("svg", {"id": "edge-layer", "aria-label": "Workflow connections"}),
        ("div", {"id": "node-layer"}),
    ]
    for tag, attrs in landmarks:
        require(parser.has_element(tag, **attrs), f"reference is missing required {tag} landmark {attrs}")

    required_ids = {
        "app",
        "canvas",
        "world",
        "palette-search",
        "inspector-content",
        "bottom-content",
        "import-file",
        "import-button",
        "export-button",
        "undo-button",
        "redo-button",
        "save-button",
        "validate-button",
        "preview-button",
        "zoom-in",
        "zoom-out",
        "fit-view",
        "palette-collapse",
        "inspector-collapse",
        "bottom-collapse",
    }
    missing_ids = required_ids - parser.values("id")
    require(not missing_ids, f"reference is missing required UI IDs: {sorted(missing_ids)}")
    require(
        {"design", "contracts", "preview", "trace", "docs"}
        <= parser.values("data-mode"),
        "reference is missing required canvas modes",
    )
    require(
        {"validation", "preview", "diagnostics", "json"}
        <= parser.values("data-tab"),
        "reference is missing required bottom panel tabs",
    )

    require(reference.count("Synthetic preview") >= 6, "reference must label every preview surface Synthetic preview")
    synthetic_markers = [
        'data-mode="preview" title="Synthetic preview"',
        '>Synthetic preview <span class="tab-count"',
        'preview: ["Synthetic preview", "Generated locally; no nodes execute"]',
        "Synthetic preview started for",
        "Synthetic preview completed in",
        "function startSyntheticPreview()",
    ]
    for marker in synthetic_markers:
        require(marker in reference, f"reference is missing synthetic preview marker: {marker}")

    media_widths = [
        int(value)
        for value in re.findall(r"@media\s*\(\s*max-width\s*:\s*(\d+)px\s*\)", reference)
    ]
    require(len(media_widths) >= 2, "reference must include at least two responsive max-width breakpoints")
    require(min(media_widths) <= 1080, "reference must include a compact responsive breakpoint")
    require(
        re.search(r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)", reference) is not None,
        "reference must honor prefers-reduced-motion",
    )
    require("palette-collapsed" in reference, "reference must support palette collapse")
    require("inspector-collapsed" in reference, "reference must support inspector collapse")

    unsafe_dom_patterns = {
        "innerHTML": r"\.innerHTML\b",
        "outerHTML": r"\.outerHTML\b",
        "insertAdjacentHTML": r"\binsertAdjacentHTML\s*\(",
        "document.write": r"\bdocument\.write\s*\(",
    }
    for label, pattern in unsafe_dom_patterns.items():
        require(re.search(pattern, javascript) is None, f"reference must not use unsafe DOM API {label}")
    for marker in ("document.createElement", ".textContent", ".setAttribute", ".replaceChildren"):
        require(marker in javascript, f"reference must use safe DOM construction marker {marker}")


def _parse_javascript_string_set(javascript: str, constant_name: str) -> set[str]:
    match = re.search(
        rf"const\s+{re.escape(constant_name)}\s*=\s*new\s+Set\s*\(\s*\[(.*?)\]\s*\)\s*;",
        javascript,
        re.DOTALL,
    )
    require(match is not None, f"reference is missing {constant_name} Set")
    return set(re.findall(r"['\"]([^'\"]+)['\"]", match.group(1)))


def _javascript_function_body(javascript: str, function_name: str) -> str:
    match = re.search(
        rf"\b(?:async\s+)?function\s+{re.escape(function_name)}\s*\([^)]*\)\s*\{{",
        javascript,
    )
    require(match is not None, f"reference is missing function {function_name}")
    opening = match.end() - 1
    depth = 0
    state = "code"
    index = opening
    while index < len(javascript):
        character = javascript[index]
        following = javascript[index + 1] if index + 1 < len(javascript) else ""
        if state == "code":
            if character == "/" and following == "/":
                state = "line_comment"
                index += 2
                continue
            if character == "/" and following == "*":
                state = "block_comment"
                index += 2
                continue
            if character in {"'", '"', "`"}:
                state = character
            elif character == "{":
                depth += 1
            elif character == "}":
                depth -= 1
                if depth == 0:
                    return javascript[opening + 1 : index]
        elif state == "line_comment":
            if character in {"\r", "\n"}:
                state = "code"
        elif state == "block_comment":
            if character == "*" and following == "/":
                state = "code"
                index += 2
                continue
        elif character == "\\":
            index += 2
            continue
        elif character == state:
            state = "code"
        index += 1
    raise ValidationError(f"function {function_name} has an unterminated body")


def _require_function_markers(
    javascript: str,
    function_name: str,
    markers: tuple[str, ...],
) -> str:
    body = _javascript_function_body(javascript, function_name)
    require(body.strip(), f"function {function_name} must not be empty")
    for marker in markers:
        require(marker in body, f"function {function_name} is missing required state action: {marker}")
    return body


def require_artifact_before_graph(function_body: str) -> None:
    artifact_position = function_body.find("artifact:")
    graph_position = function_body.find("graph:")
    require(
        artifact_position >= 0 and graph_position >= 0 and artifact_position < graph_position,
        "graphDigestPayload must preserve artifact before graph field order",
    )


def validate_core_interactions(javascript: str) -> None:
    _require_function_markers(
        javascript,
        "mutate",
        (
            "pushHistory()",
            "action()",
            "invalidateObservedRuns()",
            "state.issues = validateGraph()",
            "renderAll()",
        ),
    )
    _require_function_markers(
        javascript,
        "mutateLive",
        (
            "pushHistory()",
            "action()",
            "invalidateObservedRuns()",
            "state.issues = validateGraph()",
        ),
    )
    _require_function_markers(
        javascript,
        "connectPorts",
        (
            "connectionRejection(",
            "state.model.graph.edges.push(",
            "mutate(",
            'selectEntity("edge", edgeId)',
        ),
    )
    _require_function_markers(
        javascript,
        "addNodeFromType",
        ("state.model.graph.nodes.push(node)", "mutate(", 'selectEntity("node", id)'),
    )
    _require_function_markers(
        javascript,
        "duplicateNode",
        ("state.model.graph.nodes.push(clone)", "mutate(", 'selectEntity("node", clone.id)'),
    )
    _require_function_markers(
        javascript,
        "addPort",
        ("list.push(", "mutate(", 'selectEntity("node", node.id)'),
    )
    _require_function_markers(
        javascript,
        "removePort",
        ("state.model.graph.edges = state.model.graph.edges.filter(", "mutate("),
    )
    _require_function_markers(
        javascript,
        "deleteSelected",
        (
            "state.model.graph.nodes = state.model.graph.nodes.filter(",
            "state.model.graph.edges = state.model.graph.edges.filter(",
            "mutate(",
        ),
    )
    for function_name in ("undo", "redo"):
        _require_function_markers(
            javascript,
            function_name,
            ("restoreDesign(", "invalidateObservedRuns()", "state.issues = validateGraph()"),
        )
    start_drag_body = _require_function_markers(
        javascript,
        "startNodeDrag",
        ('selectEntity("node", node.id)', "moved: false"),
    )
    require("pushHistory()" not in start_drag_body, "node pointer down must not push history or clear redo")
    move_drag_body = _require_function_markers(
        javascript,
        "moveNodeDrag",
        (
            "if (!state.drag.moved)",
            "pushHistory()",
            "invalidateObservedRuns()",
            "node.position.x = x",
            "node.position.y = y",
        ),
    )
    first_move = move_drag_body.find("if (!state.drag.moved)")
    history_push = move_drag_body.find("pushHistory()", first_move)
    x_assignment = move_drag_body.find("node.position.x = x")
    require(
        first_move >= 0 and history_push > first_move and x_assignment > history_push,
        "node drag must push history only on the first actual movement before mutation",
    )
    end_drag_body = _require_function_markers(
        javascript,
        "endNodeDrag",
        ("state.drag.moved", 'diagnostic("node_moved"'),
    )
    require(
        "history.pop" not in end_drag_body and "state.future" not in end_drag_body,
        "no-op node drag must preserve undo and redo history",
    )
    render_nodes_body = _require_function_markers(
        javascript,
        "renderNodes",
        (
            'head.addEventListener("pointerdown"',
            'card.addEventListener("pointerdown"',
            'event.target.closest(".port")',
            'selectEntity("node", node.id)',
        ),
    )
    require(
        'head.addEventListener("click"' not in render_nodes_body,
        "node pointer selection must be owned by the full card rather than only its header",
    )
    _require_function_markers(
        javascript,
        "renderNodeInspector",
        ("mutateLive(", "mutate(", "node.status =", "node.metadata.fact_status ="),
    )
    _require_function_markers(
        javascript,
        "renderPortEditor",
        ("mutate(", "port.label =", "port.schema =", "port[key] ="),
    )
    _require_function_markers(
        javascript,
        "renderEdgeInspector",
        ("mutateLive(", "mutate(", "edge.label =", "edge.kind ="),
    )
    _require_function_markers(
        javascript,
        "bindEvents",
        ("state.model.graph.metadata.name =", "state.model.artifact.title =", "mutate("),
    )


def validate_runtime_security(javascript: str, fixture_digest: str | None = None) -> None:
    anchors = _parse_javascript_string_set(javascript, "TRUSTED_OBSERVED_DIGESTS")
    require(
        all(re.fullmatch(r"[0-9a-f]{64}", digest) for digest in anchors),
        "trusted observed digest anchors must be lowercase SHA 256 hex",
    )
    if fixture_digest is not None:
        require(fixture_digest in anchors, "fixture digest must be independently anchored in the artifact")

    graph_payload_body = _require_function_markers(
        javascript,
        "graphDigestPayload",
        (
            'schema_version: "workflow-canvas-graph/1"',
            "title: model.artifact.title",
            "purpose: model.artifact.purpose",
            "position: { x: integer(node.position.x), y: integer(node.position.y) }",
            ".sort(byId)",
            ".sort(compareText)",
        ),
    )
    require_artifact_before_graph(graph_payload_body)

    verify_body = _require_function_markers(
        javascript,
        "verifyObservedRun",
        (
            "run.artifact_id === model.artifact.id",
            "run.artifact_version === model.artifact.version",
            "run.graph_digest",
            "activeNodeIds.has(step.node_id)",
            "TRUSTED_OBSERVED_DIGESTS.has(claimedDigest)",
            "workflowGraphDigest(model)",
            "activeGraphDigest !== run.graph_digest",
            "observedDigest(run)",
            "computedDigest !== claimedDigest",
            'kind: "observed"',
            'status: "verified"',
        ),
    )
    signature = re.search(r"\basync\s+function\s+verifyObservedRun\s*\(([^)]*)\)", javascript)
    require(
        signature is not None and signature.group(1).replace(" ", "") == "run,model",
        "verifyObservedRun must require the model being verified",
    )
    _require_function_markers(
        javascript,
        "verifyObservedRuns",
        ("verifyObservedRun(run, model)",),
    )
    require("model" in verify_body, "verifyObservedRun must bind verification to its model argument")

    observed_markers = [
        'const OBSERVED_DIGEST_ALGORITHM = "SHA-256"',
        'kind: "unverified"',
        'claimed_kind: "observed"',
        'verification.trusted === true',
        'verification.algorithm === OBSERVED_DIGEST_ALGORITHM',
        'run.kind === "observed" && run.verification && run.verification.status === "verified"',
        'const embeddedModel = normalizeModel(parseInitialModel(), { trustedClaims: true })',
        'const normalized = normalizeModel(parsed)',
        'saved.runtime.observed_runs = []',
    ]
    for marker in observed_markers:
        require(marker in javascript, f"reference is missing observed trace verification marker: {marker}")
    require(
        "if (mode === \"trace\") button.disabled = !observedAvailable" in javascript,
        "Trace mode must remain disabled without a verified observed run",
    )

    normalize_model_body = _require_function_markers(
        javascript,
        "normalizeModel",
        (
            "integer(node.position && node.position.x",
            "integer(node.position && node.position.y",
            "offset_ms: clamp(integer(step.offset_ms",
            "duration_ms: clamp(integer(step.duration_ms",
        ),
    )
    require("finite(node.position" not in normalize_model_body, "node coordinates must normalize to integers")
    _require_function_markers(
        javascript,
        "normalizeObservedRun",
        (
            "offset_ms: clamp(integer(step.offset_ms",
            "duration_ms: clamp(integer(step.duration_ms",
        ),
    )
    _require_function_markers(
        javascript,
        "observedDigestPayload",
        ("offset_ms: integer(step.offset_ms)", "duration_ms: integer(step.duration_ms)"),
    )

    preview_body = _require_function_markers(
        javascript,
        "startSyntheticPreview",
        (
            "const playbackScale = total > 5000 ? 5000 / total : 1",
            "state.preview.events = steps.flatMap(",
            "while (state.preview.eventIndex < state.preview.events.length",
            "window.requestAnimationFrame(advancePreview)",
            "if (changed || completed) renderAll()",
        ),
    )
    require("setTimeout" not in preview_body, "synthetic preview must use one proportional scheduler")
    _require_function_markers(
        javascript,
        "stopPreviewTimers",
        ("window.cancelAnimationFrame(state.preview.frameId)", "state.preview.active = false"),
    )
    _require_function_markers(
        javascript,
        "resetSyntheticPreview",
        ("stopPreviewTimers()", "state.preview.statuses = new Map()", "state.preview.logs = []"),
    )

    import_body = _javascript_function_body(javascript, "importFile")
    standalone_verify = import_body.find("verifyObservedRun(normalizedRun, state.model)")
    candidate_verify = import_body.find(
        "verifyObservedRuns(normalized.runtime.observed_runs, normalized)"
    )
    candidate_assign = import_body.find("state.model = normalized")
    standalone_reset = import_body.find("resetSyntheticPreview()", standalone_verify)
    standalone_trace = import_body.find('state.mode = "trace"', standalone_verify)
    candidate_reset = import_body.find("resetSyntheticPreview()", candidate_verify)
    require(standalone_verify >= 0, "standalone observed import must verify against the active model")
    require(
        standalone_reset > standalone_verify and standalone_trace > standalone_reset,
        "standalone observed import must clear synthetic preview before switching to Trace",
    )
    require(
        candidate_verify >= 0
        and candidate_reset > candidate_verify
        and candidate_assign > candidate_reset,
        "full model import must verify, cancel preview, then assign active state",
    )

    require(
        'const EMBEDDED_ARTIFACT_ID = embeddedModel.artifact.id' in javascript
        and 'const LOCAL_STORAGE_KEY = `workflow-canvas:${EMBEDDED_ARTIFACT_ID}:v1`' in javascript,
        "local storage must bind to the embedded artifact ID",
    )
    storage_calls = re.findall(
        r"\blocalStorage\.(getItem|setItem|removeItem)\s*\(\s*([^,)]+)",
        javascript,
    )
    require(storage_calls, "reference must contain local storage persistence calls")
    require(
        all(argument.strip() == "LOCAL_STORAGE_KEY" for _method, argument in storage_calls),
        "local storage calls must use only LOCAL_STORAGE_KEY",
    )
    require(
        not re.search(r"last[-_ ]?opened|lastOpened", javascript, re.IGNORECASE),
        "reference must not use a global last opened storage pointer",
    )
    save_body = _require_function_markers(
        javascript,
        "saveLocal",
        ("state.model.artifact.id", "EMBEDDED_ARTIFACT_ID", "LOCAL_STORAGE_KEY"),
    )
    require(
        re.search(
            r"state\.model\.artifact\.id\s*!==\s*EMBEDDED_ARTIFACT_ID",
            save_body,
        )
        is not None,
        "saveLocal must reject a foreign active artifact",
    )
    load_body = _require_function_markers(
        javascript,
        "loadLocal",
        ("LOCAL_STORAGE_KEY", "EMBEDDED_ARTIFACT_ID", "JSON.parse(raw)", "normalizeModel("),
    )
    raw_parse = load_body.find("JSON.parse(raw)")
    normalization = load_body.find("normalizeModel(")
    artifact_check = load_body.find("artifact.id")
    require(
        raw_parse >= 0 and artifact_check > raw_parse and normalization > artifact_check,
        "loadLocal must check the raw stored artifact ID before normalization",
    )

    import_limit = re.search(r"const\s+IMPORT_LIMIT_BYTES\s*=\s*([^;]+);", javascript)
    require(import_limit is not None, "reference is missing IMPORT_LIMIT_BYTES")
    require(
        import_limit.group(1).strip() in {"1048576", "1024 * 1024"},
        "IMPORT_LIMIT_BYTES must be exactly 1 MiB",
    )
    size_check = import_body.find("file.size > IMPORT_LIMIT_BYTES")
    file_read = import_body.find("await file.text()")
    require(size_check >= 0 and file_read > size_check, "import size must be checked before reading file text")


def validate_diagnostics(javascript: str) -> None:
    limit = re.search(r"const\s+DIAGNOSTIC_LIMIT\s*=\s*(\d+)\s*;", javascript)
    require(limit is not None and int(limit.group(1)) == 200, "DIAGNOSTIC_LIMIT must be 200")
    allowed = _parse_javascript_string_set(javascript, "ALLOWED_DIAGNOSTIC_FIELDS")
    require(
        allowed == EXPECTED_DIAGNOSTIC_FIELDS,
        f"diagnostic field allowlist must be {sorted(EXPECTED_DIAGNOSTIC_FIELDS)}",
    )
    markers = [
        'const diagnosticTokens = new Map()',
        'const prefix = kind === "node_id" ? "n" : kind === "edge_id" ? "e" : "p"',
        'diagnosticTokens.set(mapKey, `${prefix}-${++diagnosticTokenSequence}`)',
        'record[key] = diagnosticToken(key, value)',
        "if (!ALLOWED_DIAGNOSTIC_FIELDS.has(key)) continue",
        "if (state.diagnostics.length > DIAGNOSTIC_LIMIT)",
        'downloadJson("workflow-canvas.diagnostics.json"',
        'window.addEventListener("error"',
        'window.addEventListener("unhandledrejection"',
        'SAFE_ERROR_CODES.has(message)',
        'SAFE_ERROR_NAMES.has(name)',
        'return "unexpected_error"',
    ]
    for marker in markers:
        require(marker in javascript, f"reference is missing diagnostic safety marker: {marker}")
    require("message.replace" not in javascript, "diagnostics must not transform raw error messages")
    require(
        re.search(r"error_code\s*:\s*[^,}\n]*\.message", javascript) is None,
        "diagnostics must not record raw error messages",
    )
    require(
        javascript.count('workflow-canvas.diagnostics.json') == 1,
        "diagnostics export must use one constant filename",
    )


def validate_javascript_syntax(javascript: str) -> None:
    node = shutil.which("node")
    if node is None:
        return
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".js",
            delete=False,
        ) as handle:
            handle.write(javascript)
            temporary_path = Path(handle.name)
        result = subprocess.run(
            [node, "--check", str(temporary_path)],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise ValidationError(f"could not check inline JavaScript syntax: {error}") from error
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)
    require(
        result.returncode == 0,
        f"inline JavaScript syntax check failed: {(result.stderr or result.stdout).strip()}",
    )


def _utf16_ordinal_key(value: str) -> bytes:
    return value.encode("utf-16-be", errors="surrogatepass")


def _canonical_digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(
        value,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def canonical_graph_payload(model: dict[str, Any]) -> dict[str, Any]:
    graph = model["graph"]
    return {
        "schema_version": "workflow-canvas-graph/1",
        "artifact": {
            "id": model["artifact"]["id"],
            "version": model["artifact"]["version"],
            "title": model["artifact"]["title"],
            "purpose": model["artifact"]["purpose"],
        },
        "graph": {
            "metadata": {
                "name": graph["metadata"]["name"],
                "description": graph["metadata"]["description"],
                "mode": graph["metadata"]["mode"],
            },
            "schemas": sorted(
                (
                    {"id": schema["id"], "label": schema["label"]}
                    for schema in graph["schemas"]
                ),
                key=lambda item: _utf16_ordinal_key(item["id"]),
            ),
            "nodes": sorted(
                (
                    {
                        "id": node["id"],
                        "type": node["type"],
                        "label": node["label"],
                        "description": node["description"],
                        "category": node["category"],
                        "owner": node["owner"],
                        "status": node["status"],
                        "position": {
                            "x": _normalized_integer(node["position"]["x"], f"node {node['id']} position.x"),
                            "y": _normalized_integer(node["position"]["y"], f"node {node['id']} position.y"),
                        },
                        "ports": {
                            "inputs": sorted(
                                (
                                    {
                                        "id": port["id"],
                                        "label": port["label"],
                                        "schema": port["schema"],
                                        "required": port["required"],
                                        "multiple": port["multiple"],
                                    }
                                    for port in node["ports"]["inputs"]
                                ),
                                key=lambda item: _utf16_ordinal_key(item["id"]),
                            ),
                            "outputs": sorted(
                                (
                                    {
                                        "id": port["id"],
                                        "label": port["label"],
                                        "schema": port["schema"],
                                        "required": port["required"],
                                        "multiple": port["multiple"],
                                    }
                                    for port in node["ports"]["outputs"]
                                ),
                                key=lambda item: _utf16_ordinal_key(item["id"]),
                            ),
                        },
                        "metadata": {
                            "confidence": node["metadata"]["confidence"],
                            "fact_status": node["metadata"]["fact_status"],
                            "evidence": sorted(
                                node["metadata"]["evidence"],
                                key=_utf16_ordinal_key,
                            ),
                        },
                    }
                    for node in graph["nodes"]
                ),
                key=lambda item: _utf16_ordinal_key(item["id"]),
            ),
            "edges": sorted(
                (
                    {
                        "id": edge["id"],
                        "source": {
                            "node": edge["source"]["node"],
                            "port": edge["source"]["port"],
                        },
                        "target": {
                            "node": edge["target"]["node"],
                            "port": edge["target"]["port"],
                        },
                        "kind": edge["kind"],
                        "label": edge["label"],
                        "async": edge["async"],
                    }
                    for edge in graph["edges"]
                ),
                key=lambda item: _utf16_ordinal_key(item["id"]),
            ),
        },
    }


def canonical_graph_digest(model: dict[str, Any]) -> str:
    return _canonical_digest(canonical_graph_payload(model))


def canonical_observed_payload(run: dict[str, Any]) -> dict[str, Any]:
    provenance = run["provenance"]
    return {
        "schema_version": "workflow-observed-run/1",
        "observed_run": {
            "id": run["id"],
            "kind": "observed",
            "label": run["label"],
            "captured_at": run["captured_at"],
            "sanitized": True,
            "artifact_id": run["artifact_id"],
            "artifact_version": run["artifact_version"],
            "graph_digest": run["graph_digest"],
            "provenance": {
                "type": provenance["type"],
                "source": provenance["source"],
            },
            "steps": [
                {
                    "node_id": step["node_id"],
                    "status": step["status"],
                    "offset_ms": _normalized_integer(step["offset_ms"], "observed step offset_ms", minimum=0, maximum=MAX_RUNTIME_MS),
                    "duration_ms": _normalized_integer(step["duration_ms"], "observed step duration_ms", minimum=0, maximum=MAX_RUNTIME_MS),
                    "error_code": step["error_code"] or "",
                }
                for step in run["steps"]
            ],
        },
    }


def validate_graph_digest_regression(
    model: dict[str, Any],
    graph_digest: str,
    fixture_graph_digest: str,
) -> None:
    require(model["graph"]["nodes"], "graph digest regression probe requires a node")
    require(model["graph"]["edges"], "graph digest regression probe requires an edge")

    changed_label = copy.deepcopy(model)
    changed_label["graph"]["nodes"][0]["label"] += " regression probe"
    changed_label_digest = canonical_graph_digest(changed_label)
    require(
        changed_label_digest != graph_digest and changed_label_digest != fixture_graph_digest,
        "changed node label must invalidate the fixture graph digest",
    )

    removed_edge = copy.deepcopy(model)
    removed_edge["graph"]["edges"].pop()
    removed_edge_digest = canonical_graph_digest(removed_edge)
    require(
        removed_edge_digest != graph_digest and removed_edge_digest != fixture_graph_digest,
        "removed edge must invalidate the fixture graph digest",
    )


def validate_fixture(
    fixture: Any,
    model: dict[str, Any],
    graph_digest: str,
) -> str:
    fixture = _require_object(fixture, "observed run fixture")
    _require_exact_keys(
        fixture,
        {"schema_version", "observed_run"},
        "observed run fixture",
    )
    require(
        fixture["schema_version"] == "workflow-observed-run/1",
        "observed run fixture schema_version must be workflow-observed-run/1",
    )
    run = _require_object(fixture["observed_run"], "fixture observed_run")
    _require_exact_keys(
        run,
        {
            "id",
            "kind",
            "label",
            "captured_at",
            "sanitized",
            "artifact_id",
            "artifact_version",
            "graph_digest",
            "provenance",
            "verification",
            "steps",
        },
        "fixture observed_run",
    )
    require(isinstance(run["id"], str) and run["id"], "fixture observed_run.id is required")
    require(run["kind"] == "observed", "fixture observed_run.kind must be observed")
    require(isinstance(run["label"], str), "fixture observed_run.label must be a string")
    require(run["sanitized"] is True, "fixture observed_run must be sanitized")
    require("fixture" in run["label"].lower(), "observed fixture label must say fixture")
    require(
        re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", str(run["captured_at"])) is not None,
        "fixture captured_at must be an ISO UTC timestamp",
    )

    provenance = _require_object(run["provenance"], "fixture provenance")
    _require_exact_keys(provenance, {"type", "source"}, "fixture provenance")
    require(
        isinstance(provenance["type"], str)
        and provenance["type"]
        and isinstance(provenance["source"], str)
        and provenance["source"],
        "fixture provenance type and source are required",
    )
    verification = _require_object(run["verification"], "fixture verification")
    _require_exact_keys(
        verification,
        {"trusted", "algorithm", "digest"},
        "fixture verification",
    )
    require(verification["trusted"] is True, "fixture verification.trusted must be true")
    require(verification["algorithm"] == "SHA-256", "fixture verification algorithm must be SHA-256")

    require(
        run["artifact_id"] == model["artifact"]["id"],
        "fixture artifact_id does not match the embedded model",
    )
    require(
        run["artifact_version"] == model["artifact"]["version"],
        "fixture artifact_version does not match the embedded model",
    )
    require(
        isinstance(run["graph_digest"], str)
        and re.fullmatch(r"[0-9a-f]{64}", run["graph_digest"]) is not None,
        "fixture graph_digest must be lowercase SHA 256 hex",
    )
    require(
        run["graph_digest"] == graph_digest,
        "fixture graph_digest does not match the canonical embedded graph",
    )

    model_node_ids = {node["id"] for node in model["graph"]["nodes"]}
    steps = _require_list(run["steps"], "fixture steps")
    require(steps, "fixture must contain at least one observed step")
    for index, step in enumerate(steps):
        step = _require_object(step, f"fixture steps[{index}]")
        _require_exact_keys(
            step,
            {"node_id", "status", "offset_ms", "duration_ms", "error_code"},
            f"fixture steps[{index}]",
        )
        require(step["node_id"] in model_node_ids, "fixture step references an unknown graph node")
        require(step["status"] in ALLOWED_STEP_STATUSES, "fixture step has an invalid status")
        _normalized_integer(
            step["offset_ms"],
            f"fixture steps[{index}].offset_ms",
            minimum=0,
            maximum=MAX_RUNTIME_MS,
        )
        _normalized_integer(
            step["duration_ms"],
            f"fixture steps[{index}].duration_ms",
            minimum=0,
            maximum=MAX_RUNTIME_MS,
        )
        require(isinstance(step["error_code"], str), "fixture step error_code must be a string")

    validate_graph_digest_regression(model, graph_digest, run["graph_digest"])
    digest = _canonical_digest(canonical_observed_payload(run))
    claimed_digest = verification["digest"]
    require(
        isinstance(claimed_digest, str)
        and re.fullmatch(r"[0-9a-f]{64}", claimed_digest) is not None,
        "fixture verification digest must be lowercase SHA 256 hex",
    )
    require(digest == claimed_digest, "fixture digest does not match its canonical normalized payload")

    forbidden_keys = {
        "prompt",
        "message",
        "request",
        "response",
        "headers",
        "cookie",
        "token",
        "email",
        "username",
        "customer_id",
    }

    def inspect(value: Any) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                require(key.lower() not in forbidden_keys, f"fixture contains forbidden sensitive field {key}")
                inspect(child)
        elif isinstance(value, list):
            for child in value:
                inspect(child)

    inspect(fixture)
    return digest


def validate_artifact(path: Path | str) -> dict[str, Any]:
    """Validate one generated workflow canvas HTML file and return parsed parts."""
    artifact_path = Path(path).expanduser().resolve()
    require(artifact_path.is_file(), f"artifact file does not exist: {artifact_path}")
    try:
        artifact = artifact_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as error:
        raise ValidationError(f"cannot read artifact {artifact_path}: {error}") from error
    parser = parse_reference(artifact)
    validate_html_structure(parser)
    javascript = executable_javascript(parser)
    model = embedded_model(parser)
    validate_no_remote_or_executable_paths(artifact, parser, javascript)
    validate_model(model)
    validate_ui_and_labels(artifact, parser, javascript)
    validate_core_interactions(javascript)
    validate_runtime_security(javascript)
    validate_diagnostics(javascript)
    validate_javascript_syntax(javascript)
    return {
        "path": artifact_path,
        "artifact": artifact,
        "parser": parser,
        "javascript": javascript,
        "model": model,
    }


def main(argv: list[str] | None = None) -> None:
    arguments = list(sys.argv[1:] if argv is None else argv)
    if len(arguments) != 1:
        print("usage: python scripts/validate-artifact.py /path/to/workflow-canvas.html", file=sys.stderr)
        raise SystemExit(2)
    try:
        validated = validate_artifact(arguments[0])
    except ValidationError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print(f"Workflow canvas artifact validation passed: {validated['path']}")


if __name__ == "__main__":
    main()
