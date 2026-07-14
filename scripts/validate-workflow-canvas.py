#!/usr/bin/env python3
"""Validate the committed make-workflow-canvas bundle and repository fixtures."""

from __future__ import annotations

import copy
import importlib.util
import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from types import ModuleType
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "plugins" / "output-skills" / "skills" / "make-workflow-canvas"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
CONTRACT_PATH = SKILL_ROOT / "references" / "workflow-canvas-contract.md"
REFERENCE_PATH = SKILL_ROOT / "examples" / "workflow-canvas-reference.html"
FIXTURE_PATH = SKILL_ROOT / "examples" / "observed-run-fixture.json"
BUNDLED_VALIDATOR_PATH = SKILL_ROOT / "scripts" / "validate-artifact.py"
CLAUDE_MANIFEST_PATH = ROOT / "plugins" / "output-skills" / ".claude-plugin" / "plugin.json"
CODEX_MANIFEST_PATH = ROOT / "plugins" / "output-skills" / ".codex-plugin" / "plugin.json"
EXPECTED_PLUGIN_VERSION = "1.1.0"


def _load_bundled_validator() -> ModuleType:
    if not BUNDLED_VALIDATOR_PATH.is_file():
        raise RuntimeError(f"{BUNDLED_VALIDATOR_PATH.relative_to(ROOT)} is missing")
    spec = importlib.util.spec_from_file_location(
        "alanistic_workflow_canvas_artifact_validator",
        BUNDLED_VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("could not load bundled workflow canvas artifact validator")
    module = importlib.util.module_from_spec(spec)
    previous_dont_write_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous_dont_write_bytecode
    return module


CORE = _load_bundled_validator()
ValidationError = CORE.ValidationError


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        raise ValidationError(
            f"{path.relative_to(ROOT)} is not valid UTF-8 JSON: {error}"
        ) from error


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    require(match is not None, f"{path.relative_to(ROOT)} is missing YAML frontmatter")
    metadata: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        key, separator, value = line.partition(":")
        if separator:
            metadata[key.strip()] = value.strip().strip('"').strip("'")
    return metadata


def require_repository_files() -> None:
    for path in (
        SKILL_PATH,
        CONTRACT_PATH,
        REFERENCE_PATH,
        FIXTURE_PATH,
        BUNDLED_VALIDATOR_PATH,
        CLAUDE_MANIFEST_PATH,
        CODEX_MANIFEST_PATH,
    ):
        require(path.is_file(), f"{path.relative_to(ROOT)} is missing")
    metadata = parse_frontmatter(SKILL_PATH)
    require(
        metadata.get("name") == "make-workflow-canvas",
        f"{SKILL_PATH.relative_to(ROOT)} name must be make-workflow-canvas",
    )
    require(
        bool(metadata.get("description")),
        f"{SKILL_PATH.relative_to(ROOT)} must include a description",
    )


def validate_plugin_versions() -> None:
    claude_manifest = CORE._require_object(
        load_json(CLAUDE_MANIFEST_PATH), "Claude output plugin manifest"
    )
    codex_manifest = CORE._require_object(
        load_json(CODEX_MANIFEST_PATH), "Codex output plugin manifest"
    )
    claude_version = claude_manifest.get("version")
    codex_version = codex_manifest.get("version")
    require(
        claude_version == codex_version,
        "Claude and Codex output plugin versions must match",
    )
    require(
        claude_version == EXPECTED_PLUGIN_VERSION,
        f"output plugin version must be {EXPECTED_PLUGIN_VERSION}",
    )


def validate_generated_artifact_path() -> None:
    with tempfile.TemporaryDirectory(prefix="workflow-canvas-validator-") as directory:
        copied_artifact = Path(directory) / "generated-workflow-canvas.html"
        shutil.copyfile(REFERENCE_PATH, copied_artifact)
        validated = CORE.validate_artifact(copied_artifact)
        require(
            validated["path"] == copied_artifact.resolve(),
            "bundled validator must validate the supplied generated artifact path",
        )


def validate_remote_scanner_regressions(validated: dict[str, Any]) -> None:
    artifact = validated["artifact"]
    parser = validated["parser"]
    javascript = validated["javascript"]
    harmless = javascript + "\n// fetch('comment only')\nconst uiText = \"new Worker and window.location are labels\";"
    CORE.validate_no_remote_or_executable_paths(artifact, parser, harmless)
    executable_cases = {
        "comment-spaced import": "import /* generated */ ('./module.js');",
        "network API": "fetch ('https://example.invalid');",
        "network constructor": "const socket = new WebSocket('wss://example.invalid');",
        "worker": "const worker = new Worker('worker.js');",
        "navigation": "window.location = 'https://example.invalid';",
        "resource assignment": "image.src = 'https://example.invalid/image.png';",
        "resource setAttribute": "image.setAttribute('src', 'https://example.invalid/image.png');",
        "computed resource setAttribute": "probe.setAttribute('s' + 'rc', remoteUrl);",
        "template resource setAttribute": "probe.setAttribute(`${prefix}src`, remoteUrl);",
        "resource setAttributeNS": "image.setAttributeNS(null, 'href', 'https://example.invalid/image.svg');",
        "bracket resource setAttributeNS": "probe['setAttributeNS'](null, 'href', remoteUrl);",
        "computed bracket resource setter": "probe['set' + 'AttributeNS'](null, 'href', remoteUrl);",
    }
    for label, snippet in executable_cases.items():
        try:
            CORE.validate_no_remote_or_executable_paths(
                artifact,
                parser,
                javascript + "\n" + snippet,
            )
        except ValidationError:
            continue
        raise ValidationError(f"remote resource scanner missed {label}")

    css_cases = {
        "CSS identifier escape": ".\\78 { color: red; }",
        "CSS import": "@import 'theme.css';",
        "CSS remote URL": ".x { background: url('https://example.invalid/x.png'); }",
        "CSS image-set": ".x { background: image-set(url('#one') 1x); }",
    }
    for label, snippet in css_cases.items():
        candidate = artifact.replace("</style>", snippet + "\n</style>", 1)
        candidate_parser = CORE.parse_reference(candidate)
        try:
            CORE.validate_no_remote_or_executable_paths(
                candidate,
                candidate_parser,
                CORE.executable_javascript(candidate_parser),
            )
        except ValidationError:
            continue
        raise ValidationError(f"remote resource scanner missed {label}")

    inline_style = artifact.replace(
        "<body>",
        '<body style="background:url(https://example.invalid/image.png)">',
        1,
    )
    inline_style_parser = CORE.parse_reference(inline_style)
    try:
        CORE.validate_no_remote_or_executable_paths(
            inline_style,
            inline_style_parser,
            CORE.executable_javascript(inline_style_parser),
        )
    except ValidationError:
        pass
    else:
        raise ValidationError("remote resource scanner missed inline style URL")


def validate_artifact_before_graph_regression() -> None:
    for body in (
        "graph: {}",
        "artifact: {}",
        "graph: {}, artifact: {}",
    ):
        try:
            CORE.require_artifact_before_graph(body)
        except ValidationError:
            continue
        raise ValidationError(
            "artifact-before-graph regression must reject missing or reversed markers"
        )


def validate_integer_digest_regression(
    model: dict[str, Any],
    fixture: dict[str, Any],
) -> None:
    float_model = copy.deepcopy(model)
    integer_model = copy.deepcopy(model)
    node = float_model["graph"]["nodes"][0]
    integer_node = integer_model["graph"]["nodes"][0]
    node_id = node["id"]
    node["position"]["x"] = float(integer_node["position"]["x"])
    node["position"]["y"] = -0.0
    integer_node["position"]["y"] = 0
    CORE.validate_model(float_model)
    float_payload = CORE.canonical_graph_payload(float_model)
    integer_payload = CORE.canonical_graph_payload(integer_model)
    float_position = next(
        item["position"] for item in float_payload["graph"]["nodes"] if item["id"] == node_id
    )
    require(
        isinstance(float_position["x"], int)
        and isinstance(float_position["y"], int)
        and float_position["y"] == 0,
        "canonical graph positions must normalize integral floats and negative zero to integers",
    )
    require(
        CORE.canonical_graph_digest(float_model)
        == CORE.canonical_graph_digest(integer_model),
        "integer-equivalent graph coordinates must produce the same digest",
    )

    float_run = copy.deepcopy(fixture["observed_run"])
    integer_run = copy.deepcopy(fixture["observed_run"])
    for index, step in enumerate(float_run["steps"]):
        step["offset_ms"] = -0.0 if index == 0 else float(step["offset_ms"])
        step["duration_ms"] = float(step["duration_ms"])
        integer_run["steps"][index]["offset_ms"] = (
            0 if index == 0 else int(integer_run["steps"][index]["offset_ms"])
        )
        integer_run["steps"][index]["duration_ms"] = int(
            integer_run["steps"][index]["duration_ms"]
        )
    float_observed_payload = CORE.canonical_observed_payload(float_run)
    integer_observed_payload = CORE.canonical_observed_payload(integer_run)
    require(
        float_observed_payload == integer_observed_payload,
        "canonical observed timings must normalize integral floats and negative zero",
    )
    require(
        CORE._canonical_digest(float_observed_payload)
        == CORE._canonical_digest(integer_observed_payload),
        "integer-equivalent observed timings must produce the same digest",
    )


def validate_workflow_canvas(root: Path | None = None) -> None:
    """Validate the committed workflow canvas skill without mutating files."""
    if root is not None:
        require(
            root.resolve() == ROOT.resolve(),
            "workflow canvas validator root does not match its repository",
        )
    require_repository_files()
    validated = CORE.validate_artifact(REFERENCE_PATH)
    model = validated["model"]
    javascript = validated["javascript"]
    graph_digest = CORE.canonical_graph_digest(model)
    fixture = load_json(FIXTURE_PATH)
    fixture_digest = CORE.validate_fixture(fixture, model, graph_digest)
    CORE.validate_runtime_security(javascript, fixture_digest)
    validate_integer_digest_regression(model, fixture)
    validate_artifact_before_graph_regression()
    validate_remote_scanner_regressions(validated)
    validate_generated_artifact_path()
    validate_plugin_versions()


def main() -> None:
    try:
        validate_workflow_canvas()
    except ValidationError as error:
        print(f"error: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    print("Workflow canvas validation passed.")


if __name__ == "__main__":
    main()
