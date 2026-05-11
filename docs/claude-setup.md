# Claude Code Setup

This repo ships a Claude Code plugin manifest at `.claude-plugin/plugin.json`. The plugin name is `agent-skills-codex`. Claude Code auto-discovers `skills/*/SKILL.md` from the plugin root, so the same skill folders that drive Codex drive Claude Code too.

There are three install paths. Pick one.

## Option 1: Install as a Plugin via Marketplace (recommended)

A "marketplace" in Claude Code is any source that exposes one or more plugins. This repo is a single-plugin marketplace.

Inside Claude Code:

```text
/plugin marketplace add alangmartini/agent-skills
/plugin install agent-skills-codex
```

The first command adds the GitHub repo as a marketplace; the second installs the plugin from it. Replace `alangmartini/agent-skills` with the actual `owner/repo` if you forked.

To install from a local checkout instead of GitHub (useful while developing):

```text
/plugin marketplace add /absolute/path/to/agent-skills-codex
/plugin install agent-skills-codex
```

To inspect or remove the plugin later:

```text
/plugin list
/plugin uninstall agent-skills-codex
/plugin marketplace remove alangmartini/agent-skills
```

Restart Claude Code (or run `/plugin reload`) after installing or updating skills.

## Option 2: Install as User-Level Skills

Claude Code reads user skills from `~/.claude/skills/`. Copying the skill folders there makes every skill available across all your projects without touching the plugin system.

Windows PowerShell:

```powershell
$dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force $dest
Get-ChildItem .\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
```

macOS/Linux:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/* "$HOME/.claude/skills/"
```

### Installing One Skill

Windows PowerShell:

```powershell
$dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force $dest
Copy-Item -Recurse .\skills\code-review-and-quality $dest
```

macOS/Linux:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R skills/code-review-and-quality "$HOME/.claude/skills/"
```

Restart Claude Code after installing or updating skills.

## Option 3: Install as Project-Level Skills

Claude Code also reads `.claude/skills/` from inside the active project. Use this when you want the skills to ship with the repo so teammates pick them up via version control.

From the project root:

```powershell
New-Item -ItemType Directory -Force .\.claude\skills
Get-ChildItem "<path-to-agent-skills-codex>\skills" -Directory | Copy-Item -Destination .\.claude\skills -Recurse -Force
```

```bash
mkdir -p .claude/skills
cp -R <path-to-agent-skills-codex>/skills/* .claude/skills/
```

Project-level skills override user-level skills with the same `name`.

## Plugin Layout

The Claude Code manifest lives at:

```text
.claude-plugin/plugin.json
```

It declares the plugin metadata (`name`, `version`, `description`, `author`, …). It does **not** need to enumerate skills: Claude Code looks for `skills/*/SKILL.md` under the plugin root automatically.

## Using a Skill

Once a skill is installed, Claude Code reads each `SKILL.md`'s frontmatter to decide when it applies. You can also invoke a skill explicitly:

```text
Use the test-driven-development skill for this bug fix.
Use code-review-and-quality to review the current diff.
Use handoff to prepare the next session.
```

Start with `using-agent-skills` if you are not sure which workflow fits.

## Verify the Bundle

From the repository root:

```bash
python scripts/validate-skills.py
```

The validator checks skill frontmatter, both plugin manifests (`.codex-plugin/plugin.json` and `.claude-plugin/plugin.json`), and that packaging for other agents has not been reintroduced.

## Troubleshooting

- **Skills do not appear after `/plugin install`.** Run `/plugin list` to confirm the install, then `/plugin reload` or restart Claude Code. Marketplace caches can be refreshed with `/plugin marketplace update <name>`.
- **`SKILL.md` is loaded but ignored.** Open the file and confirm the YAML frontmatter has both `name` and `description`, and that `name` exactly matches the directory name (kebab-case). The validator catches this.
- **Project-level skill not picking up.** Check that the file is at `.claude/skills/<skill-name>/SKILL.md` relative to the project root Claude Code is running in, not the parent directory.
- **Skill description does not trigger when expected.** Descriptions drive routing; rewrite the description to clearly state what the skill does *and* when to use it.
