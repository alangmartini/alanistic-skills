# Alanistic Skills (Codex + Claude Code)

Production-grade engineering and output-format skills packaged for OpenAI Codex and Claude Code.

Originally derived from `addyosmani/agent-skills`, this repo keeps the reusable skill workflows and strips packaging for other agents (Gemini, Copilot, Cursor, Windsurf, opencode, etc.). Both Codex and Claude Code consume the same `SKILL.md` format. The repo is a marketplace named `alanistic-skills` that ships two plugins, `dev-skills` and `output-skills`, each with both a Codex (`.codex-plugin/plugin.json`) and a Claude Code (`.claude-plugin/plugin.json`) manifest.

## Quick Start

Clone the repo:

```bash
git clone https://github.com/alangmartini/alanistic-skills.git
cd alanistic-skills
```

### Codex

Install one skill on Windows:

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

Restart Codex after installing skills.

On macOS/Linux, Codex skills live in `${CODEX_HOME:-$HOME/.codex}/skills`:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R plugins/dev-skills/skills/* "${CODEX_HOME:-$HOME/.codex}/skills/"
cp -R plugins/output-skills/skills/* "${CODEX_HOME:-$HOME/.codex}/skills/"
```

### Claude Code

Claude Code reads `SKILL.md` files with the same frontmatter Codex uses. Pick one path:

**As plugins (recommended).** Add this repo as a marketplace and install:

```text
/plugin marketplace add alangmartini/alanistic-skills
/plugin install dev-skills@alanistic-skills
/plugin install output-skills@alanistic-skills
```

Claude Code auto-discovers `skills/*/SKILL.md` from each plugin root declared in its `.claude-plugin/plugin.json`.

**As user-level skills.** Copy skills into `~/.claude/skills/`:

```powershell
$dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force $dest
Get-ChildItem .\plugins\dev-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
Get-ChildItem .\plugins\output-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
```

```bash
mkdir -p "$HOME/.claude/skills"
cp -R plugins/dev-skills/skills/* "$HOME/.claude/skills/"
cp -R plugins/output-skills/skills/* "$HOME/.claude/skills/"
```

**As project-level skills.** Copy into `.claude/skills/` inside your project to share them via version control.

Restart Claude Code after installing or updating skills.

## Plugin Manifests

This repo is a marketplace that ships two plugins:

```text
.claude-plugin/
  marketplace.json                  # lists both plugins (marketplace: alanistic-skills)
plugins/
  dev-skills/
    .claude-plugin/plugin.json      # dev-skills
    .codex-plugin/plugin.json       # dev-skills (Codex)
    skills/                         # engineering workflow skills
  output-skills/
    .claude-plugin/plugin.json      # output-skills
    .codex-plugin/plugin.json       # output-skills (Codex)
    skills/                         # html-output, make-architecture-flow, make-interactive-visualization, caveman
references/
docs/
```

The `dev-skills` plugin covers engineering workflows. The `output-skills` plugin covers self-contained interactive HTML generation plus the caveman compression mode. Both Codex and Claude Code consume the same `SKILL.md` format, so each plugin ships both manifests.

Per-agent setup details:

- [docs/codex-setup.md](docs/codex-setup.md) — Codex install paths and plugin layout
- [docs/claude-setup.md](docs/claude-setup.md) — Claude Code marketplace install, user/project skill folders, troubleshooting

## Skill Routing

Both Codex and Claude Code read each skill's `name` and `description` metadata to decide when to load the full instructions. Keep the `description` field specific: it should say what the skill does and when the agent should use it.

| Work type | Start with |
|---|---|
| Unsure which workflow applies | `using-agent-skills` |
| Explicit compressed communication | `caveman` *(output-skills)* |
| Handing work to a fresh session | `handoff` |
| Vague idea or product concept | `idea-refine` |
| New project, feature, or significant change | `spec-driven-development` |
| Turning a spec into tasks | `planning-and-task-breakdown` |
| Creating a codebase architecture map | `make-architecture-flow` *(output-skills)* |
| Visualizing diagnostics, incidents, issues, or workflows | `make-interactive-visualization` *(output-skills)* |
| Producing a single-file interactive HTML report | `html-output` *(output-skills)* |
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

### Meta (dev-skills)

| Skill | Purpose |
|---|---|
| [using-agent-skills](plugins/dev-skills/skills/using-agent-skills/SKILL.md) | Discover which skill applies to a task |
| [handoff](plugins/dev-skills/skills/handoff/SKILL.md) | Compact current context for a fresh agent session |

### Define

| Skill | Purpose |
|---|---|
| [idea-refine](plugins/dev-skills/skills/idea-refine/SKILL.md) | Turn rough ideas into concrete proposals |
| [spec-driven-development](plugins/dev-skills/skills/spec-driven-development/SKILL.md) | Write a structured spec before implementation |

### Plan

| Skill | Purpose |
|---|---|
| [planning-and-task-breakdown](plugins/dev-skills/skills/planning-and-task-breakdown/SKILL.md) | Break specs into small, verifiable tasks |

### Build

| Skill | Purpose |
|---|---|
| [incremental-implementation](plugins/dev-skills/skills/incremental-implementation/SKILL.md) | Build in thin, verified slices |
| [test-driven-development](plugins/dev-skills/skills/test-driven-development/SKILL.md) | Red, green, refactor with evidence |
| [context-engineering](plugins/dev-skills/skills/context-engineering/SKILL.md) | Give Codex the right context at the right time |
| [source-driven-development](plugins/dev-skills/skills/source-driven-development/SKILL.md) | Ground implementation choices in source docs |
| [frontend-ui-engineering](plugins/dev-skills/skills/frontend-ui-engineering/SKILL.md) | Build accessible, production-quality UI |
| [api-and-interface-design](plugins/dev-skills/skills/api-and-interface-design/SKILL.md) | Design stable contracts and boundaries |

### Verify

| Skill | Purpose |
|---|---|
| [browser-testing-with-devtools](plugins/dev-skills/skills/browser-testing-with-devtools/SKILL.md) | Verify browser behavior with DevTools MCP |
| [debugging-and-error-recovery](plugins/dev-skills/skills/debugging-and-error-recovery/SKILL.md) | Reproduce, localize, fix, and guard failures |

### Review

| Skill | Purpose |
|---|---|
| [code-review-and-quality](plugins/dev-skills/skills/code-review-and-quality/SKILL.md) | Review across correctness, readability, architecture, security, and performance |
| [code-simplification](plugins/dev-skills/skills/code-simplification/SKILL.md) | Reduce complexity while preserving behavior |
| [security-and-hardening](plugins/dev-skills/skills/security-and-hardening/SKILL.md) | Harden auth, input, data, dependencies, and boundaries |
| [performance-optimization](plugins/dev-skills/skills/performance-optimization/SKILL.md) | Measure first, then optimize bottlenecks |

### Ship

| Skill | Purpose |
|---|---|
| [git-workflow-and-versioning](plugins/dev-skills/skills/git-workflow-and-versioning/SKILL.md) | Keep commits atomic and history useful |
| [ci-cd-and-automation](plugins/dev-skills/skills/ci-cd-and-automation/SKILL.md) | Build quality gates and release automation |
| [deprecation-and-migration](plugins/dev-skills/skills/deprecation-and-migration/SKILL.md) | Remove or migrate systems deliberately |
| [documentation-and-adrs](plugins/dev-skills/skills/documentation-and-adrs/SKILL.md) | Document decisions, APIs, and operating context |
| [create-changelog-fragment](plugins/dev-skills/skills/create-changelog-fragment/SKILL.md) | Write release-ready changelog fragments from completed work |
| [create-version-release](plugins/dev-skills/skills/create-version-release/SKILL.md) | Prepare version bumps and release notes from repo history |
| [shipping-and-launch](plugins/dev-skills/skills/shipping-and-launch/SKILL.md) | Launch with monitoring, rollout gates, and rollback plans |

### Orchestrator

| Skill | Purpose |
|---|---|
| [implement](plugins/dev-skills/skills/implement/SKILL.md) | End-to-end implementation orchestration (spec, plan, TDD, review, simplify, ship, changelog) |

## Output Skills (separate plugin)

These ship as a second plugin in the same marketplace, `output-skills`, living at `plugins/output-skills/`. Install separately when you want them.

| Skill | Purpose |
|---|---|
| [html-output](plugins/output-skills/skills/html-output/SKILL.md) | Produce a single-file interactive HTML report from any source material |
| [make-architecture-flow](plugins/output-skills/skills/make-architecture-flow/SKILL.md) | Generate an interactive architecture map and agent JSON from a codebase |
| [make-interactive-visualization](plugins/output-skills/skills/make-interactive-visualization/SKILL.md) | Generate self-contained interactive visualizations from complex source material |
| [caveman](plugins/output-skills/skills/caveman/SKILL.md) | Switch to explicit compressed communication modes |

Claude Code install:

```text
/plugin marketplace add alangmartini/alanistic-skills
/plugin install output-skills@alanistic-skills
```

Codex install (copy the skills directly):

```powershell
$dest = "$env:USERPROFILE\.codex\skills"
New-Item -ItemType Directory -Force $dest
Get-ChildItem .\plugins\output-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
```

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R plugins/output-skills/skills/* "${CODEX_HOME:-$HOME/.codex}/skills/"
```

## References

Reference material is intentionally separate from skill entry points so the agent can load it only when needed:

| Reference | Used for |
|---|---|
| [testing-patterns.md](references/testing-patterns.md) | Test structure, naming, mocks, API tests, and E2E examples |
| [security-checklist.md](references/security-checklist.md) | Security review and hardening checks |
| [performance-checklist.md](references/performance-checklist.md) | Frontend and backend performance checks |
| [accessibility-checklist.md](references/accessibility-checklist.md) | WCAG-oriented UI review |

## Contributing

New skills belong under the right plugin's `skills/` directory: `plugins/dev-skills/skills/<skill-name>/SKILL.md` for engineering workflows, `plugins/output-skills/skills/<skill-name>/SKILL.md` for output-format skills. Each skill must include frontmatter with `name` and `description`, and the directory name must match the skill name.

Run the validator before committing:

```bash
python scripts/validate-skills.py
```

Keep this repo scoped to Codex and Claude Code. Do not add command folders, manifests, hooks, or setup guides for other agents (Gemini, Copilot, Cursor, Windsurf, opencode, etc.).
