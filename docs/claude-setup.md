# Claude Code Setup

This repo ships two Claude Code manifests:

- `.claude-plugin/plugin.json` — the plugin definition. The plugin name is `agent-skills-codex`. Claude Code auto-discovers `skills/*/SKILL.md` from the plugin root, so the same skill folders that drive Codex drive Claude Code too.
- `.claude-plugin/marketplace.json` — the marketplace listing. It declares one plugin (`agent-skills-codex`) whose source is `"./"`, i.e. the marketplace repo itself. This lets the repo be installed via `/plugin marketplace add <owner>/<repo>`.

Both files live at the repo root. The marketplace listing is the entry point Claude Code expects when you add a repo as a marketplace; without it, `/plugin install` cannot find anything to install.

There are three install paths. Pick one.

## Option 1: Install as a Plugin via Marketplace (recommended)

Inside Claude Code:

```text
/plugin marketplace add alangmartini/agent-skills
/plugin install agent-skills-codex
```

The first command adds the GitHub repo as a marketplace by reading `.claude-plugin/marketplace.json` on the default branch. The second installs the `agent-skills-codex` plugin listed inside it. Replace `alangmartini/agent-skills` with the actual `owner/repo` if you forked.

To install from a local checkout instead of GitHub (useful while developing, or before the marketplace lands on the default branch):

```text
/plugin marketplace add /absolute/path/to/agent-skills-codex
/plugin install agent-skills-codex
```

To inspect or remove the plugin later:

```text
/plugin list
/plugin uninstall agent-skills-codex
/plugin marketplace remove agent-skills-codex
```

Restart Claude Code (or run `/plugin reload`) after installing or updating skills.

### Recovering from the upstream marketplace

If you previously ran `/plugin marketplace add alangmartini/agent-skills` before this repo had its own `marketplace.json`, Claude Code may have cached the **upstream** marketplace (named `addy-agent-skills`, listing a plugin called `agent-skills` with a `github`-typed source that some Claude Code versions reject). Remove it and re-add:

```text
/plugin marketplace remove addy-agent-skills
/plugin marketplace add alangmartini/agent-skills
/plugin install agent-skills-codex
```

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

The Claude Code manifests live at:

```text
.claude-plugin/plugin.json       # what gets installed
.claude-plugin/marketplace.json  # what /plugin marketplace add reads
```

`plugin.json` declares the plugin metadata (`name`, `version`, `description`, `author`, …). It does **not** need to enumerate skills: Claude Code looks for `skills/*/SKILL.md` under the plugin root automatically.

`marketplace.json` declares a marketplace (`name: agent-skills-codex`) that lists this one plugin with `source: "./"`. The path-string source form is portable across Claude Code versions; object-form sources like `{source: "github", repo: "..."}` are not supported by older builds.

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

- **`Plugin "agent-skills-codex" not found in any marketplace`.** The marketplace you added does not list a plugin with that name. Run `/plugin marketplace list` and confirm you see a marketplace named `agent-skills-codex`. If you instead see `addy-agent-skills`, you added the wrong (upstream) marketplace — see [Recovering from the upstream marketplace](#recovering-from-the-upstream-marketplace).
- **`Failed to install: This plugin uses a source type your Claude Code version does not support`.** The marketplace listing uses an object-form `source` (e.g. `{source: "github", ...}`) that your Claude Code build does not parse. This repo uses the path-string form (`source: "./"`) specifically to avoid this. If you see this error, you are installing from a different marketplace; remove it and add this repo.
- **Marketplace add succeeded but the marketplace name surprised you.** `/plugin marketplace add <owner>/<repo>` reads the default branch. If the default branch is still on the upstream layout, you will get the upstream marketplace name (`addy-agent-skills`) rather than this fork's name (`agent-skills-codex`). Either wait for the dual-target PR to merge into `main`, install from the `codex-only` branch checkout locally, or change the GitHub default branch.
- **Skills do not appear after `/plugin install`.** Run `/plugin list` to confirm the install, then `/plugin reload` or restart Claude Code. Marketplace caches can be refreshed with `/plugin marketplace update <name>`.
- **`SKILL.md` is loaded but ignored.** Open the file and confirm the YAML frontmatter has both `name` and `description`, and that `name` exactly matches the directory name (kebab-case). The validator catches this.
- **Project-level skill not picking up.** Check that the file is at `.claude/skills/<skill-name>/SKILL.md` relative to the project root Claude Code is running in, not the parent directory.
- **Skill description does not trigger when expected.** Descriptions drive routing; rewrite the description to clearly state what the skill does *and* when to use it.
