# AGENTS.md

This repository is a fork of `addyosmani/agent-skills` packaged for OpenAI Codex and Claude Code. The two agents share the same `SKILL.md` format, so a single `skills/` tree serves both.

## Repository Purpose

The repo packages software engineering workflows as agent skills. The durable artifacts are:

- `skills/<skill-name>/SKILL.md` for on-demand skills (consumed by both Codex and Claude Code)
- `references/*.md` for optional supporting material
- `.codex-plugin/plugin.json` for Codex plugin metadata
- `.claude-plugin/plugin.json` for Claude Code plugin metadata
- `docs/` for usage and contribution docs

Do not reintroduce packaging for other agents (Gemini, Copilot, Cursor, Windsurf, opencode, etc.), command folders, hook scripts, or agent-specific personas. Only Codex and Claude Code manifests belong here.

## Skill Rules

- Treat each `SKILL.md` as a workflow, not a blog post.
- Keep frontmatter valid and minimal: `name` and `description` are required.
- The skill directory name must exactly match the `name` field.
- Descriptions must say both what the skill does and when the agent should use it. Stay agent-neutral where possible; "Codex" and "Claude Code" both consume the same metadata.
- Keep `SKILL.md` focused. Move long examples, checklists, or provider-specific details to directly linked reference files.
- Avoid adding README files inside individual skill directories.

## Editing Guidance

- Preserve existing skill behavior unless the task explicitly changes it.
- Use ASCII for new docs unless an existing file clearly requires another character set.
- Prefer small, scoped edits over broad rewrites.
- When adding a new reusable workflow, add it as a skill directory under `skills/`.
- When adding supporting material, place it in `references/` or inside the skill directory only if it is tightly coupled to that skill.

## Validation

Run the validator after changing manifests, skills, or docs:

```bash
python scripts/validate-skills.py
```

The validator checks:

- `.codex-plugin/plugin.json` exists, is named `agent-skills-codex`, and points at `./skills/`
- `.claude-plugin/plugin.json` exists, is named `agent-skills-codex`, and has a description
- every `skills/*/SKILL.md` has required frontmatter
- each skill `name` matches its directory
- packaging for other agents (Gemini, opencode, etc.) stays removed

If material for an additional agent is intentionally added later, document why it belongs in this fork.

## Project Structure

```text
.codex-plugin/
  plugin.json
.claude-plugin/
  plugin.json
docs/
  codex-setup.md
  claude-setup.md
  getting-started.md
  skill-anatomy.md
references/
  accessibility-checklist.md
  performance-checklist.md
  security-checklist.md
  testing-patterns.md
skills/
  <skill-name>/
    SKILL.md
scripts/
  validate-skills.py
```

## Release Criteria

Before pushing changes to this branch:

- `python scripts/validate-skills.py` passes
- `git status --short` contains only intentional changes
- docs describe Codex and Claude Code behavior only
- no packaging for other agents has been reintroduced
