# Getting Started

Skills are self-contained folders with a required `SKILL.md`. Codex and Claude Code both read the frontmatter metadata to decide when a skill applies, then load the skill body only when needed. The same skill folder works for both agents.

## Install Skills (Codex)

Install a single skill on Windows:

```powershell
$dest = "$env:USERPROFILE\.codex\skills"
New-Item -ItemType Directory -Force $dest
Copy-Item -Recurse .\plugins\dev-skills\skills\test-driven-development $dest
```

Install all skills on Windows:

```powershell
$dest = "$env:USERPROFILE\.codex\skills"
New-Item -ItemType Directory -Force $dest
Get-ChildItem .\plugins\dev-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
Get-ChildItem .\plugins\output-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
```

Install all skills on macOS/Linux:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R plugins/dev-skills/skills/* "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R plugins/output-skills/skills/* "${CODEX_HOME:-$HOME/.codex}/skills/"
```

Restart Codex after installing or updating skills.

## Install Skills (Claude Code)

**Plugin install (recommended):**

```text
/plugin marketplace add alangmartini/alanistic-skills
/plugin install dev-skills@alanistic-skills
/plugin install output-skills@alanistic-skills
```

**User-level copy on Windows:**

```powershell
$dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force $dest
Get-ChildItem .\plugins\dev-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
Get-ChildItem .\plugins\output-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
```

**User-level copy on macOS/Linux:**

```bash
mkdir -p "$HOME/.claude/skills"
cp -R plugins/dev-skills/skills/* "$HOME/.claude/skills/"
cp -R plugins/output-skills/skills/* "$HOME/.claude/skills/"
```

For project-scoped skills, copy into `.claude/skills/` inside the target project instead. Restart Claude Code after installing or updating skills.

## Use Skills

Start with `using-agent-skills` if you are not sure which workflow applies. Otherwise, name the skill in your request or let the agent choose from the metadata.

Examples:

```text
Use the spec-driven-development skill for this feature.
```

```text
Use test-driven-development to reproduce and fix this bug.
```

```text
Use code-review-and-quality to review the current diff.
```

```text
Use handoff to prepare the next Codex session.
```

```text
Use caveman full for compressed answers.
```

```text
Use create-changelog-fragment for the completed change.
```

```text
Use create-version-release to prepare a patch release.
```

## Recommended Baseline

For day-to-day coding, install these first:

- `using-agent-skills`
- `spec-driven-development`
- `planning-and-task-breakdown`
- `incremental-implementation`
- `test-driven-development`
- `code-review-and-quality`

Add the rest as your work needs them.

## Skill Loading Strategy

Do not load every skill body into a prompt manually. Agent skills are designed for progressive disclosure:

1. Metadata stays visible for routing.
2. `SKILL.md` loads only when the skill applies.
3. References load only when the active skill needs deeper material.

This keeps context smaller and makes skill selection more reliable across both Codex and Claude Code.

## Working Artifacts

Some skills may create files such as `SPEC.md`, `tasks/plan.md`, or `tasks/todo.md`. Treat them as living project artifacts while the work is active:

- Commit them when they are useful for team coordination.
- Update them when scope or decisions change.
- Delete them before merge if the project does not want long-lived planning files.

## Plugin Manifests

The repository ships two plugins from one marketplace named `alanistic-skills`, each with both a Codex and a Claude Code manifest:

- `dev-skills` (engineering workflows): `plugins/dev-skills/.codex-plugin/plugin.json` and `plugins/dev-skills/.claude-plugin/plugin.json`, with skills under `plugins/dev-skills/skills/`.
- `output-skills` (interactive HTML output + caveman): `plugins/output-skills/.codex-plugin/plugin.json` and `plugins/output-skills/.claude-plugin/plugin.json`, with skills under `plugins/output-skills/skills/`.

Manual copy into `~/.codex/skills` or `~/.claude/skills` remains supported when plugin installation is not available.

For per-agent install details, see:

- [codex-setup.md](codex-setup.md)
- [claude-setup.md](claude-setup.md)
