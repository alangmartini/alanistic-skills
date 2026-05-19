# Claude Code Setup

This repo ships two Claude Code plugins from one marketplace named `alanistic-skills`:

- `plugins/dev-skills/.claude-plugin/plugin.json` defines the `dev-skills` plugin (engineering workflows: spec, plan, build, verify, review, ship). Claude Code auto-discovers `plugins/dev-skills/skills/*/SKILL.md`.
- `plugins/output-skills/.claude-plugin/plugin.json` defines the `output-skills` plugin (single-file HTML output: architecture maps, visualizations, reports, plus the caveman compression mode).
- `.claude-plugin/marketplace.json` is the marketplace listing. It declares both plugins so they can be installed via `/plugin marketplace add <owner>/<repo>`.

The marketplace listing is the entry point Claude Code expects when you add a repo as a marketplace; without it, `/plugin install` cannot find anything to install.

There are three install paths. Pick one.

## Option 1: Install as a Plugin via Marketplace (recommended)

Inside Claude Code:

```text
/plugin marketplace add alangmartini/alanistic-skills
/plugin install dev-skills@alanistic-skills
/plugin install output-skills@alanistic-skills
```

The first command adds the GitHub repo as a marketplace by reading `.claude-plugin/marketplace.json` on the default branch. The next two install the plugins.

To install from a local checkout instead of GitHub (useful while developing):

```text
/plugin marketplace add /absolute/path/to/alanistic-skills
/plugin install dev-skills@alanistic-skills
/plugin install output-skills@alanistic-skills
```

To inspect or remove plugins later:

```text
/plugin list
/plugin uninstall dev-skills
/plugin uninstall output-skills
/plugin marketplace remove alanistic-skills
```

Restart Claude Code (or run `/plugin reload`) after installing or updating skills.

## Option 2: Install as User-Level Skills

Claude Code reads user skills from `~/.claude/skills/`. Copying the skill folders there makes every skill available across all your projects without touching the plugin system.

Windows PowerShell:

```powershell
$dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force $dest
Get-ChildItem .\plugins\dev-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
Get-ChildItem .\plugins\output-skills\skills -Directory | Copy-Item -Destination $dest -Recurse -Force
```

macOS/Linux:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R plugins/dev-skills/skills/* "$HOME/.claude/skills/"
cp -R plugins/output-skills/skills/* "$HOME/.claude/skills/"
```

### Installing One Skill

Windows PowerShell:

```powershell
$dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force $dest
Copy-Item -Recurse .\plugins\dev-skills\skills\code-review-and-quality $dest
```

macOS/Linux:

```bash
mkdir -p "$HOME/.claude/skills"
cp -R plugins/dev-skills/skills/code-review-and-quality "$HOME/.claude/skills/"
```

Restart Claude Code after installing or updating skills.

## Option 3: Install as Project-Level Skills

Claude Code also reads `.claude/skills/` from inside the active project. Use this when you want the skills to ship with the repo so teammates pick them up via version control.

From the project root:

```powershell
New-Item -ItemType Directory -Force .\.claude\skills
Get-ChildItem "<path-to-alanistic-skills>\plugins\dev-skills\skills" -Directory | Copy-Item -Destination .\.claude\skills -Recurse -Force
```

```bash
mkdir -p .claude/skills
cp -R <path-to-alanistic-skills>/plugins/dev-skills/skills/* .claude/skills/
```

Project-level skills override user-level skills with the same `name`.

## Plugin Layout

The Claude Code manifests live at:

```text
.claude-plugin/marketplace.json                  # what /plugin marketplace add reads
plugins/dev-skills/.claude-plugin/plugin.json    # dev-skills
plugins/output-skills/.claude-plugin/plugin.json # output-skills
```

`plugin.json` declares the plugin metadata (`name`, `version`, `description`, `author`, etc.). It does **not** need to enumerate skills: Claude Code looks for `skills/*/SKILL.md` under the plugin root automatically.

`marketplace.json` declares a marketplace (`name: alanistic-skills`) that lists both plugins. Each plugin entry uses the path-string `source` form, which is portable across Claude Code versions; object-form sources like `{source: "github", repo: "..."}` are not supported by older builds.

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

The validator checks skill frontmatter, every plugin manifest (`.codex-plugin/plugin.json` and `.claude-plugin/plugin.json` for both plugins), and that packaging for other agents has not been reintroduced.

## Troubleshooting

- **`Plugin "dev-skills" not found in any marketplace`.** The marketplace you added does not list a plugin with that name. Run `/plugin marketplace list` and confirm you see a marketplace named `alanistic-skills`.
- **`Failed to install: This plugin uses a source type your Claude Code version does not support`.** The marketplace listing uses an object-form `source` (e.g. `{source: "github", ...}`) that your Claude Code build does not parse. This repo uses the path-string form (`source: "./plugins/..."`) specifically to avoid this. If you see this error, you are installing from a different marketplace; remove it and add this repo.
- **Skills do not appear after `/plugin install`.** Run `/plugin list` to confirm the install, then `/plugin reload` or restart Claude Code. Marketplace caches can be refreshed with `/plugin marketplace update <name>`.
- **`SKILL.md` is loaded but ignored.** Open the file and confirm the YAML frontmatter has both `name` and `description`, and that `name` exactly matches the directory name (kebab-case). The validator catches this.
- **Project-level skill not picking up.** Check that the file is at `.claude/skills/<skill-name>/SKILL.md` relative to the project root Claude Code is running in, not the parent directory.
- **Skill description does not trigger when expected.** Descriptions drive routing; rewrite the description to clearly state what the skill does *and* when to use it.
