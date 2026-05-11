# Agent Skills (Codex + Claude Code)

Production-grade engineering skills packaged for OpenAI Codex and Claude Code.

This fork keeps the reusable skill workflows from `addyosmani/agent-skills` and strips packaging for other agents (Gemini, Copilot, Cursor, Windsurf, opencode, …). Both Codex and Claude Code consume the same `SKILL.md` format, so a single `skills/` tree drives both — paired with a Codex plugin manifest (`.codex-plugin/plugin.json`) and a Claude Code plugin manifest (`.claude-plugin/plugin.json`).

## Quick Start

Clone the fork:

```bash
git clone https://github.com/alangmartini/agent-skills.git
cd agent-skills
git switch codex-only
```

### Codex

Install one skill on Windows:

```powershell
$dest = "$env:USERPROFILE\.codex\skills"
New-Item -ItemType Directory -Force $dest
Copy-Item -Recurse .\skills\test-driven-development $dest
```

Install all skills on Windows:

```powershell
$dest = "$env:USERPROFILE\.codex\skills"
New-Item -ItemType Directory -Force $dest
Get-ChildItem .\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
```

Restart Codex after installing skills.

On macOS/Linux, Codex skills live in `${CODEX_HOME:-$HOME/.codex}/skills`:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/* "${CODEX_HOME:-$HOME/.codex}/skills/"
```

### Claude Code

Claude Code reads `SKILL.md` files with the same frontmatter Codex uses, so the same `skills/` folder works unchanged. Pick one path:

**As a plugin (recommended).** Add this repo as a marketplace and install:

```text
/plugin marketplace add alangmartini/agent-skills
/plugin install agent-skills-codex
```

Claude Code auto-discovers `skills/*/SKILL.md` from the plugin root declared in `.claude-plugin/plugin.json`.

**As user-level skills.** Copy skills into `~/.claude/skills/`:

```powershell
$dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force $dest
Get-ChildItem .\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
```

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/* "$HOME/.claude/skills/"
```

**As project-level skills.** Copy into `.claude/skills/` inside your project to share them via version control.

Restart Claude Code after installing or updating skills.

## Plugin Manifests

This repo is structured as a plugin root for both agents:

```text
.codex-plugin/plugin.json   # Codex
.claude-plugin/plugin.json  # Claude Code
skills/
references/
docs/
```

Both manifests name the plugin `agent-skills-codex` and point at the same `skills/` tree. Use whichever manifest your agent supports; otherwise copy the desired skill directories into the agent's user-skills folder.

Per-agent setup details:

- [docs/codex-setup.md](docs/codex-setup.md) — Codex install paths and plugin layout
- [docs/claude-setup.md](docs/claude-setup.md) — Claude Code marketplace install, user/project skill folders, troubleshooting

## Skill Routing

Both Codex and Claude Code read each skill's `name` and `description` metadata to decide when to load the full instructions. Keep the `description` field specific: it should say what the skill does and when the agent should use it.

| Work type | Start with |
|---|---|
| Unsure which workflow applies | `using-agent-skills` |
| Explicit compressed communication | `caveman` |
| Handing work to a fresh session | `handoff` |
| Vague idea or product concept | `idea-refine` |
| New project, feature, or significant change | `spec-driven-development` |
| Turning a spec into tasks | `planning-and-task-breakdown` |
| Implementing code | `incremental-implementation` |
| Writing or changing tests | `test-driven-development` |
| Browser UI verification | `browser-testing-with-devtools` |
| Broken tests, builds, or behavior | `debugging-and-error-recovery` |
| Reviewing before merge | `code-review-and-quality` |
| Security-sensitive work | `security-and-hardening` |
| Performance-sensitive work | `performance-optimization` |
| Capturing release notes | `create-changelog-fragment` |
| Preparing a version release | `create-version-release` |
| Preparing a release | `shipping-and-launch` |

## Skills

### Meta

| Skill | Purpose |
|---|---|
| [using-agent-skills](skills/using-agent-skills/SKILL.md) | Discover which skill applies to a task |
| [caveman](skills/caveman/SKILL.md) | Switch to explicit compressed communication modes |
| [handoff](skills/handoff/SKILL.md) | Compact current context for a fresh agent session |

### Define

| Skill | Purpose |
|---|---|
| [idea-refine](skills/idea-refine/SKILL.md) | Turn rough ideas into concrete proposals |
| [spec-driven-development](skills/spec-driven-development/SKILL.md) | Write a structured spec before implementation |

### Plan

| Skill | Purpose |
|---|---|
| [planning-and-task-breakdown](skills/planning-and-task-breakdown/SKILL.md) | Break specs into small, verifiable tasks |

### Build

| Skill | Purpose |
|---|---|
| [incremental-implementation](skills/incremental-implementation/SKILL.md) | Build in thin, verified slices |
| [test-driven-development](skills/test-driven-development/SKILL.md) | Red, green, refactor with evidence |
| [context-engineering](skills/context-engineering/SKILL.md) | Give Codex the right context at the right time |
| [source-driven-development](skills/source-driven-development/SKILL.md) | Ground implementation choices in source docs |
| [frontend-ui-engineering](skills/frontend-ui-engineering/SKILL.md) | Build accessible, production-quality UI |
| [api-and-interface-design](skills/api-and-interface-design/SKILL.md) | Design stable contracts and boundaries |

### Verify

| Skill | Purpose |
|---|---|
| [browser-testing-with-devtools](skills/browser-testing-with-devtools/SKILL.md) | Verify browser behavior with DevTools MCP |
| [debugging-and-error-recovery](skills/debugging-and-error-recovery/SKILL.md) | Reproduce, localize, fix, and guard failures |

### Review

| Skill | Purpose |
|---|---|
| [code-review-and-quality](skills/code-review-and-quality/SKILL.md) | Review across correctness, readability, architecture, security, and performance |
| [code-simplification](skills/code-simplification/SKILL.md) | Reduce complexity while preserving behavior |
| [security-and-hardening](skills/security-and-hardening/SKILL.md) | Harden auth, input, data, dependencies, and boundaries |
| [performance-optimization](skills/performance-optimization/SKILL.md) | Measure first, then optimize bottlenecks |

### Ship

| Skill | Purpose |
|---|---|
| [git-workflow-and-versioning](skills/git-workflow-and-versioning/SKILL.md) | Keep commits atomic and history useful |
| [ci-cd-and-automation](skills/ci-cd-and-automation/SKILL.md) | Build quality gates and release automation |
| [deprecation-and-migration](skills/deprecation-and-migration/SKILL.md) | Remove or migrate systems deliberately |
| [documentation-and-adrs](skills/documentation-and-adrs/SKILL.md) | Document decisions, APIs, and operating context |
| [create-changelog-fragment](skills/create-changelog-fragment/SKILL.md) | Write release-ready changelog fragments from completed work |
| [create-version-release](skills/create-version-release/SKILL.md) | Prepare version bumps and release notes from repo history |
| [shipping-and-launch](skills/shipping-and-launch/SKILL.md) | Launch with monitoring, rollout gates, and rollback plans |

## References

Reference material is intentionally separate from skill entry points so the agent can load it only when needed:

| Reference | Used for |
|---|---|
| [testing-patterns.md](references/testing-patterns.md) | Test structure, naming, mocks, API tests, and E2E examples |
| [security-checklist.md](references/security-checklist.md) | Security review and hardening checks |
| [performance-checklist.md](references/performance-checklist.md) | Frontend and backend performance checks |
| [accessibility-checklist.md](references/accessibility-checklist.md) | WCAG-oriented UI review |

## Contributing

New skills belong under `skills/<skill-name>/SKILL.md`. Each skill must include frontmatter with `name` and `description`, and the directory name must match the skill name.

Run the validator before committing:

```bash
python scripts/validate-skills.py
```

Keep this branch scoped to Codex and Claude Code. Do not add command folders, manifests, hooks, or setup guides for other agents (Gemini, Copilot, Cursor, Windsurf, opencode, …).
