# Codex Setup

This repo ships two Codex plugin bundles under `plugins/`:

- `plugins/dev-skills/` (engineering workflows)
- `plugins/output-skills/` (interactive HTML output + caveman)

## Manual Install

Codex loads user skills from `$CODEX_HOME/skills`. If `CODEX_HOME` is not set, the default is `~/.codex/skills`.

Windows PowerShell:

```powershell
$dest = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME "skills" } else { Join-Path $env:USERPROFILE ".codex\skills" }
New-Item -ItemType Directory -Force $dest
Get-ChildItem .\plugins\dev-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
Get-ChildItem .\plugins\output-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
```

macOS/Linux:

```bash
dest="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$dest"
cp -R plugins/dev-skills/skills/* "$dest/"
cp -R plugins/output-skills/skills/* "$dest/"
```

Restart Codex after installing or updating skills.

## Installing One Skill

Windows PowerShell:

```powershell
$dest = if ($env:CODEX_HOME) { Join-Path $env:CODEX_HOME "skills" } else { Join-Path $env:USERPROFILE ".codex\skills" }
New-Item -ItemType Directory -Force $dest
Copy-Item -Recurse .\plugins\dev-skills\skills\code-review-and-quality $dest
```

macOS/Linux:

```bash
dest="${CODEX_HOME:-$HOME/.codex}/skills"
mkdir -p "$dest"
cp -R plugins/dev-skills/skills/code-review-and-quality "$dest/"
```

## Plugin Layout

The plugin manifests live at:

```text
plugins/dev-skills/.codex-plugin/plugin.json
plugins/output-skills/.codex-plugin/plugin.json
```

Each declares:

```json
{
  "skills": "./skills/"
}
```

Use the plugin manifests in Codex environments that support plugin installation. For direct local use, copying the skill folders is enough.

## Verify the Bundle

From the repository root:

```bash
python scripts/validate-skills.py
```

The validator checks skill frontmatter, both Codex manifests, and accidental restoration of non-Codex artifacts.
