# AGENTS.md

This repository is originally derived from `addyosmani/agent-skills` and is packaged for OpenAI Codex and Claude Code. The two agents share the same `SKILL.md` format, so each plugin's `skills/` tree serves both.

The repo is structured as a Claude Code marketplace that ships two plugins:

- `alanistic-skills` (the core engineering plugin) lives at the repo root. Its skills are under `skills/`.
- `interactive-output-skills` lives under `plugins/output/`. Its skills are under `plugins/output/skills/`.

`.claude-plugin/marketplace.json` lists both. Each plugin has its own `.claude-plugin/plugin.json` and `.codex-plugin/plugin.json`.

## Repository Purpose

The repo packages software engineering workflows as agent skills. The durable artifacts are:

- `skills/<skill-name>/SKILL.md` (core plugin) for engineering workflow skills
- `plugins/output/skills/<skill-name>/SKILL.md` for interactive HTML output skills
- `references/*.md` for optional supporting material
- `.codex-plugin/plugin.json` and `plugins/output/.codex-plugin/plugin.json` for Codex plugin metadata
- `.claude-plugin/plugin.json` and `plugins/output/.claude-plugin/plugin.json` for Claude Code plugin metadata
- `.claude-plugin/marketplace.json` for the marketplace listing
- `plugins/output/workspace/` and `plugins/output/drafts/` for plugin-local, non-skill assets (eval workspaces, WIP drafts). `workspace/` is git-ignored by default.
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
- When adding a new reusable workflow, add it as a skill directory under the relevant plugin's `skills/` directory (`skills/` for the core plugin, `plugins/output/skills/` for the interactive output plugin). Pick the plugin whose theme matches the workflow.
- When adding supporting material, place it in `references/` or inside the skill directory only if it is tightly coupled to that skill.

## Validation

Run the validator after changing manifests, skills, or docs:

```bash
python scripts/validate-skills.py
```

The validator checks (for each plugin: core + interactive-output-skills):

- the plugin's `.codex-plugin/plugin.json` exists, has the expected name, and points at `./skills/`
- the plugin's `.claude-plugin/plugin.json` exists, has the expected name, and has a description
- every `<plugin>/skills/*/SKILL.md` has required frontmatter
- each skill `name` matches its directory
- `.claude-plugin/marketplace.json` lists every expected plugin and only uses path-string sources
- packaging for other agents (Gemini, opencode, etc.) stays removed

If material for an additional agent is intentionally added later, document why it belongs in this fork.

## Project Structure

```text
.claude-plugin/
  marketplace.json        # lists both plugins
  plugin.json             # core plugin (alanistic-skills)
.codex-plugin/
  plugin.json             # core plugin (Codex)
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
    SKILL.md              # core engineering skills
plugins/
  output/
    .claude-plugin/plugin.json   # interactive-output-skills
    .codex-plugin/plugin.json    # interactive-output-skills (Codex)
    skills/
      <skill-name>/
        SKILL.md          # interactive HTML output skills
    workspace/            # plugin-local eval workspaces (gitignored)
    drafts/               # plugin-local draft / WIP skills
scripts/
  validate-skills.py
```

## Release Criteria

Before pushing changes to this branch:

- `python scripts/validate-skills.py` passes
- `git status --short` contains only intentional changes
- docs describe Codex and Claude Code behavior only
- no packaging for other agents has been reintroduced
