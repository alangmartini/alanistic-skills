#!/usr/bin/env python3
"""Validate the agent skills marketplace (core plugin + interactive-output-skills)."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


REMOVED_ARTIFACTS = [
    ".claude",
    ".gemini",
    ".opencode",
    "CLAUDE.md",
    "hooks",
    "agents",
    "docs/copilot-setup.md",
    "docs/cursor-setup.md",
    "docs/gemini-cli-setup.md",
    "docs/opencode-setup.md",
    "docs/windsurf-setup.md",
    "references/orchestration-patterns.md",
]


# Each entry describes a plugin that ships in this repo.
#   root:    directory that contains .claude-plugin/ and .codex-plugin/
#   name:    expected plugin name in both manifests
#   skills:  directory that holds the registered skills for this plugin
PLUGINS = [
    {
        "root": ROOT,
        "name": "alanistic-skills",
        "skills": ROOT / "skills",
    },
    {
        "root": ROOT / "plugins" / "output",
        "name": "interactive-output-skills",
        "skills": ROOT / "plugins" / "output" / "skills",
    },
]


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def parse_frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.DOTALL)
    if not match:
        fail(f"{path.relative_to(ROOT)} is missing YAML frontmatter")

    data: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if not line.strip() or line.startswith(" "):
            continue
        key, sep, value = line.partition(":")
        if sep:
            data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def validate_codex_plugin(plugin_root: Path, expected_name: str) -> None:
    manifest_path = plugin_root / ".codex-plugin" / "plugin.json"
    rel = manifest_path.relative_to(ROOT)
    if not manifest_path.is_file():
        fail(f"{rel} is missing")

    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    if manifest.get("name") != expected_name:
        fail(f"{rel} name must be {expected_name}")
    if manifest.get("skills") != "./skills/":
        fail(f"{rel} must point skills at ./skills/")


def validate_claude_plugin(plugin_root: Path, expected_name: str) -> None:
    manifest_path = plugin_root / ".claude-plugin" / "plugin.json"
    rel = manifest_path.relative_to(ROOT)
    if not manifest_path.is_file():
        fail(f"{rel} is missing")

    with manifest_path.open(encoding="utf-8") as handle:
        manifest = json.load(handle)

    if manifest.get("name") != expected_name:
        fail(f"{rel} name must be {expected_name}")
    if not manifest.get("description"):
        fail(f"{rel} must include a description")


def validate_claude_marketplace() -> None:
    marketplace_path = ROOT / ".claude-plugin" / "marketplace.json"
    if not marketplace_path.is_file():
        fail(".claude-plugin/marketplace.json is missing")

    with marketplace_path.open(encoding="utf-8") as handle:
        marketplace = json.load(handle)

    if marketplace.get("name") != "alanistic-skills":
        fail(".claude-plugin/marketplace.json name must be alanistic-skills")

    plugins = marketplace.get("plugins")
    if not isinstance(plugins, list) or not plugins:
        fail(".claude-plugin/marketplace.json must declare at least one plugin")

    plugin_names = {entry.get("name") for entry in plugins if isinstance(entry, dict)}
    expected_names = {p["name"] for p in PLUGINS}
    missing = expected_names - plugin_names
    if missing:
        fail(
            f".claude-plugin/marketplace.json must list these plugins: {sorted(missing)}"
        )

    for entry in plugins:
        if not isinstance(entry, dict):
            continue
        source = entry.get("source")
        if not isinstance(source, str):
            fail(
                ".claude-plugin/marketplace.json plugin source must be a path string; "
                "object-form sources (github, etc.) are not portable across Claude Code versions"
            )


def validate_removed_artifacts() -> None:
    for relative in REMOVED_ARTIFACTS:
        if (ROOT / relative).exists():
            fail(f"non-Codex artifact should not exist: {relative}")


def validate_skills(skills_dir: Path) -> None:
    rel = skills_dir.relative_to(ROOT)
    if not skills_dir.is_dir():
        fail(f"{rel} directory is missing")

    skill_dirs = sorted(path for path in skills_dir.iterdir() if path.is_dir())
    if not skill_dirs:
        fail(f"{rel} contains no skill directories")

    for skill_dir in skill_dirs:
        skill_path = skill_dir / "SKILL.md"
        if not skill_path.is_file():
            fail(f"{skill_dir.relative_to(ROOT)} is missing SKILL.md")

        metadata = parse_frontmatter(skill_path)
        expected_name = skill_dir.name
        actual_name = metadata.get("name")
        description = metadata.get("description")

        if actual_name != expected_name:
            fail(f"{skill_path.relative_to(ROOT)} name is {actual_name!r}, expected {expected_name!r}")
        if not description:
            fail(f"{skill_path.relative_to(ROOT)} is missing description")
        if len(description) > 1024:
            fail(f"{skill_path.relative_to(ROOT)} description is longer than 1024 characters")


def main() -> None:
    for plugin in PLUGINS:
        validate_codex_plugin(plugin["root"], plugin["name"])
        validate_claude_plugin(plugin["root"], plugin["name"])
        validate_skills(plugin["skills"])
    validate_claude_marketplace()
    validate_removed_artifacts()
    plugin_count = len(PLUGINS)
    print(
        f"Skill bundle validation passed ({plugin_count} plugins, Codex + Claude Code manifests)."
    )


if __name__ == "__main__":
    main()
