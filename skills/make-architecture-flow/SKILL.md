---
name: make-architecture-flow
description: Creates a source-grounded architecture package from a codebase. Use when a user asks for an architecture map, system map, dependency map, data-flow diagram, codebase tour, interactive HTML architecture visualization, or AI-agent-consumable JSON context for a repository.
---

# Make Architecture Flow

## Overview

Produce two durable architecture artifacts from a real codebase:

1. A self-contained interactive HTML architecture map.
2. A structured JSON context file that another coding agent can consume.

The output must be grounded in the repository, not inferred from naming alone. Treat this as architecture discovery plus artifact generation.

## When to Use

Use this skill when the user asks for:

- A visual architecture map of a project.
- A single-file HTML system map or dependency diagram.
- A codebase overview for onboarding.
- A data-flow, API, database, or external-service map.
- A JSON summary for another AI coding agent.

Do not use this skill for a quick prose explanation unless the user requests generated architecture artifacts.

## Workflow

### 1. Establish Scope

- If no codebase or path is available, ask the user for the repository or target directory.
- If a workspace is already available, use it and state the assumption briefly.
- Read local instruction files first, including `AGENTS.md`, `CLAUDE.md`, `.cursorrules`, `.github/copilot-instructions.md`, and package-specific guidance when present.
- Inspect `git status --short --branch` before editing. Preserve unrelated user changes.
- Default artifact names:
  - `architecture-map.html`
  - `architecture-agent-context.json`
- If those files already exist and appear user-authored, inspect them before replacing. Update in place only when that is clearly the requested artifact.

### 2. Inventory the Codebase

Use fast local search first:

```bash
rg --files
```

Identify:

- Languages, frameworks, package managers, build tools, test tools, and runtime versions.
- Entry points such as server boot files, CLI commands, frontend roots, workers, scheduled jobs, migrations, and scripts.
- Configuration sources, environment variables, feature flags, secrets boundaries, and deployment files.
- API routes, RPC handlers, message consumers, queue processors, webhooks, sockets, and background loops.
- Databases, caches, files, object stores, queues, search indexes, and local state.
- External services and SDK clients.
- Tests, fixtures, smoke scripts, playgrounds, and docs that reveal intended behavior.

Prefer source files and executable config over README claims. Use docs as supporting evidence, not the only source of truth.

### 3. Trace Architecture

Create a source-grounded model with:

- Components: modules, packages, services, UI surfaces, workers, stores, dispatchers, clients, and infrastructure boundaries.
- Dependencies: direct imports, runtime calls, SDK clients, API consumers, storage access, and operational coupling.
- Data flows: ingress, routing, validation, persistence, external calls, background processing, user-facing output, and failure handling.
- Entry points: commands, HTTP routes, event handlers, process boot paths, scheduled jobs, test harnesses, and replay paths.
- Constraints: concurrency model, persistence assumptions, idempotency, security boundaries, runtime requirements, deployment assumptions, and known scale limits.
- Architecture decisions: choices visible in source, with file evidence and observed consequences.
- Architectural issues: risks, design debt, ambiguity, correctness hazards, security gaps, availability risks, or maintainability bottlenecks.

Every major claim needs either a file path, a command result, or an explicit label such as `inferred` or `unknown`.

### 4. Produce the JSON Artifact

Write a clean, parseable JSON file for agent consumption. Use this top-level shape unless the user requested a different schema:

```json
{
  "schema_version": "1.0",
  "generated_at": "ISO-8601 timestamp",
  "repository": {
    "name": "string",
    "root": "string",
    "branch": "string",
    "commit": "string or unknown"
  },
  "summary": {
    "purpose": "string",
    "architecture_style": "string",
    "primary_runtime": "string",
    "key_risks": ["string"]
  },
  "tech_stack": [],
  "entry_points": [],
  "components": [],
  "external_services": [],
  "data_stores": [],
  "api_endpoints": [],
  "data_flows": [],
  "component_dependencies": [],
  "constraints": [],
  "architecture_decisions": [],
  "architectural_issues": [],
  "testing_and_verification": [],
  "agent_notes": []
}
```

Use stable identifiers. For example, component IDs should be lowercase snake case or kebab case and reused by dependencies, flows, issues, and map nodes.

For each component include at least:

```json
{
  "id": "string",
  "name": "string",
  "kind": "service | module | ui | worker | store | external | config | test | docs | unknown",
  "responsibilities": ["string"],
  "key_files": ["relative/path"],
  "dependencies": ["component_id"],
  "dependents": ["component_id"],
  "runtime_notes": ["string"],
  "evidence": ["relative/path"]
}
```

For each architectural issue include:

```json
{
  "id": "string",
  "severity": "critical | high | medium | low",
  "category": "correctness | security | availability | maintainability | performance | operability | configuration | data_integrity",
  "title": "string",
  "description": "string",
  "evidence": ["relative/path"],
  "affected_components": ["component_id"],
  "recommendation": "string"
}
```

Do not include comments, trailing commas, Markdown, or prose outside JSON.

### 5. Produce the HTML Artifact

Build a single-file HTML page that can open directly in a browser. It must be self-contained:

- Inline all CSS and JavaScript.
- Do not depend on CDNs, external fonts, external images, remote scripts, or installed packages.
- Embed the architecture model as JSON inside the page or as a JavaScript constant.
- Use accessible semantic controls where possible.

Minimum interaction requirements:

- Clickable nodes with a details panel.
- Hover states for nodes and edges.
- Search across components, files, endpoints, services, and issues.
- Filters by component kind or layer.
- Zoom and pan for the main map.
- A reset view control.
- Clickable flow summaries that highlight related nodes and edges.
- A visible issues panel with severity and affected components.
- A visible API or entry-point section when the codebase has routes or commands.

Recommended visual hierarchy:

- Group nodes into layers such as ingress, orchestration, domain workflows, execution, persistence, external services, and operations.
- Use distinct colors by kind, not by arbitrary decoration.
- Use compact cards and dense labels for operational tools.
- Make edge labels short and useful.
- Avoid generic marketing layouts. The first viewport should show the map itself.

If Tailwind is requested, approximate the utility style with embedded CSS unless a local, already vendored Tailwind build is available. Self-contained output is more important than using a remote framework.

### 6. Validate Artifacts

Run lightweight validation before final response:

- Parse the JSON with an available runtime, for example `node`, `python`, or `jq`.
- Check the HTML for external `http` or `https` resources in `script`, `link`, `img`, `iframe`, and media tags.
- Syntax-check inline scripts when practical.
- Run project tests, typecheck, or lint only when dependencies are available and the run is relevant to the generated analysis.
- If the HTML is complex and a browser tool is available, open it and inspect for console errors and obvious layout failures.

Example validation commands:

```bash
node -e "const fs=require('fs'); JSON.parse(fs.readFileSync('architecture-agent-context.json','utf8')); console.log('json ok')"
node -e "const fs=require('fs'); const html=fs.readFileSync('architecture-map.html','utf8'); if (/<(script|link|img|iframe|source|video|audio)[^>]+(?:src|href)=['\"]https?:/i.test(html)) throw new Error('external resource found'); for (const m of html.matchAll(/<script>([\\s\\S]*?)<\\/script>/g)) new Function(m[1]); console.log('html ok')"
```

Record failed validation honestly. Do not claim a check passed if dependencies were missing.

## Accuracy Rules

- Do not invent databases, services, queues, or endpoints.
- Distinguish observed, inferred, and unknown facts.
- Prefer exact relative file paths over vague module names.
- Capture architectural issues even when they are uncomfortable.
- Include stale or contradictory docs only as issues or notes, not as unquestioned truth.
- Keep generated artifacts scoped to architecture. Do not refactor application code unless the user explicitly asks.

## Final Response

Keep the final answer short and include:

- Links or paths to both generated artifacts.
- Validation results.
- Any checks that could not run.
- The highest-signal architectural issues, if the user asked for issues to be highlighted and they are not already obvious in the artifacts.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The folder names tell the architecture." | Real architecture is in entry points, runtime calls, state, and failure paths. Verify from source. |
| "The HTML can use a CDN because it is just a report." | The artifact must remain usable offline and portable across agent sessions. |
| "A diagram is enough." | The JSON is the durable machine-readable context future agents need. |
| "Docs say what the system does." | Docs can drift. Cross-check source, tests, and config. |
| "Issues are out of scope." | The user explicitly needs architectural accuracy, including risks and constraints. |

## Red Flags

- No `git status` before writing artifacts.
- JSON does not parse.
- HTML loads remote resources.
- The map has nodes but no data flows.
- Components have no evidence paths.
- External services are listed without source proof.
- Architectural issues are generic, unactionable, or missing evidence.

## Verification

After completing the workflow, confirm:

- [ ] Local instructions were read and followed.
- [ ] The codebase was inventoried from source, config, tests, and docs.
- [ ] `architecture-agent-context.json` parses as JSON.
- [ ] `architecture-map.html` is self-contained and its inline script parses.
- [ ] Main components, key files, data stores, external services, entry points, endpoints, data flows, constraints, and issues are represented.
- [ ] Final response reports artifact paths and validation status.
