---
name: make-interactive-visualization
description: Creates source-grounded, self-contained interactive visualizations for complex information. Use when a user asks to visualize diagnostics, incidents, issues, traces, workflows, architecture, dependency maps, timelines, investigations, support cases, release plans, or other multi-part material as an HTML artifact or structured visual model.
---

# Make Interactive Visualization

## Overview

Turn complex source material into a polished, interactive, single-file HTML visualization. The artifact should help a human understand structure, flow, causality, priority, or state faster than prose alone.

This skill is general-purpose. For full codebase architecture maps with agent JSON, prefer `make-architecture-flow`. Use this skill for visual diagnostics, issue triage, incidents, support investigations, timelines, process flows, dependency maps, and mixed evidence packages.

## Core Principle

The visualization is a claim about reality. Build it from evidence, label uncertainty, and make the underlying model inspectable.

## Workflow

### 1. Establish the Visualization Goal

Identify what the user needs to see:

- Structure: components, actors, owners, systems, issue groups, or entities.
- Flow: requests, events, messages, state transitions, reproduction steps, or handoffs.
- Time: incident chronology, release timeline, investigation timeline, or regression window.
- Causality: symptoms, hypotheses, evidence, root causes, mitigations, and confidence.
- Priority: severity, blast radius, customer impact, next actions, risk, and status.
- Comparison: alternatives, versions, environments, clusters, issues, or designs.

If the source material is missing, ask for it. If a workspace or artifacts are already present, use them and state the assumption briefly.

### 2. Gather and Normalize Evidence

Use the available source of truth before designing:

- Code repositories: source files, tests, configs, docs, issue templates, logs, and scripts.
- Diagnostics: monitor output, traces, metrics, logs, stack traces, screenshots, command output, and runbooks.
- Issue sets: GitHub issues, support tickets, Slack threads, PRs, incidents, customer reports, and release notes.
- Plans and workflows: specs, ADRs, tasks, dependency lists, meetings, and design docs.

Capture each fact with provenance:

```json
{
  "claim": "string",
  "evidence": ["path, URL, message id, command output, or user-provided source"],
  "confidence": "high | medium | low",
  "status": "observed | inferred | disputed | unknown"
}
```

Do not turn ambiguous evidence into definite visual truth. Use low confidence styling, question marks, or an uncertainty panel.

### 3. Choose the Right Visual Grammar

Pick the form based on the job:

| User Need | Recommended Visualization |
|---|---|
| Show systems, relationships, ownership, or dependencies | Node-link map with grouped lanes |
| Show a request, event, or operational process | Swimlane or step flow |
| Show incident or investigation chronology | Timeline with evidence cards |
| Show symptoms to root cause | Diagnostic tree or hypothesis graph |
| Show many issues or tickets | Cluster map plus triage board |
| Show severity and priority | Risk matrix or impact/effort grid |
| Show state across environments or versions | Comparison matrix |
| Show nested scope | Treemap, hierarchy, or expandable outline |
| Show competing options | Decision map with tradeoff table |

Combine grammars only when it improves comprehension. For example, an incident visualization can use a timeline plus a cause-effect graph plus an action board.

### 4. Build a Visual Data Model

Create a compact model before writing the UI. Use stable IDs so interactions can link entities, flows, evidence, and issues.

Recommended shape:

```json
{
  "schema_version": "1.0",
  "title": "string",
  "generated_at": "ISO-8601 timestamp",
  "scope": "string",
  "summary": {
    "purpose": "string",
    "primary_view": "graph | timeline | swimlane | tree | matrix | board | hybrid",
    "key_takeaways": ["string"]
  },
  "entities": [],
  "relationships": [],
  "events": [],
  "groups": [],
  "issues": [],
  "actions": [],
  "evidence": [],
  "uncertainties": []
}
```

Entity fields:

```json
{
  "id": "string",
  "label": "string",
  "kind": "service | file | person | team | issue | symptom | hypothesis | cause | action | system | state | external | other",
  "group": "string",
  "status": "active | resolved | blocked | unknown | healthy | degraded | failing | proposed",
  "severity": "critical | high | medium | low | info | none",
  "description": "string",
  "evidence": ["evidence_id"],
  "metadata": {}
}
```

Relationship fields:

```json
{
  "id": "string",
  "from": "entity_id",
  "to": "entity_id",
  "label": "string",
  "kind": "depends_on | causes | mitigates | blocks | calls | owns | duplicates | relates_to | follows | contradicts",
  "confidence": "high | medium | low",
  "evidence": ["evidence_id"]
}
```

Keep this model either embedded in the HTML or written as a sidecar JSON file when the user asks for machine-readable output.

### 5. Design the HTML Artifact

Create a single HTML file that opens directly in a browser:

- Inline all CSS and JavaScript.
- Do not use CDNs, remote fonts, external images, or network calls.
- Use SVG, Canvas, or semantic HTML depending on the visual grammar.
- Make the first viewport the actual visualization, not a landing page.
- Use compact controls: search, filters, zoom, reset, and view mode toggles.
- Make nodes, events, cards, and matrix cells clickable.
- Show a details panel with evidence, status, confidence, metadata, and related items.
- Use hover states and highlighted paths to show relationships.
- Include a summary panel for top takeaways, risks, unknowns, and next actions.
- Use semantic colors consistently: severity, health, status, confidence, or group. Avoid decorative palettes.
- Keep text readable and contained at mobile and desktop widths.

For graph-like views:

- Add pan and zoom.
- Group entities into lanes or regions.
- Keep edge labels short.
- Add search and type/status/severity filters.
- Highlight inbound and outbound relationships when an entity is selected.

For timelines:

- Add filtering by actor, severity, source, or phase.
- Use absolute timestamps when available.
- Show gaps and uncertain ordering explicitly.

For diagnostics:

- Separate symptoms, hypotheses, evidence, root cause, mitigation, and follow-up.
- Show confidence and status for each hypothesis.
- Make contradictory evidence visible.

For issue triage:

- Group by theme, subsystem, customer impact, severity, owner, or status.
- Show duplicates and related issues.
- Include recommended next actions and open questions.

### 6. Validate the Output

Run lightweight checks before responding:

- Confirm the HTML file exists and is non-empty.
- Check that no `script`, `link`, `img`, `iframe`, `source`, `video`, or `audio` tag loads `http` or `https`.
- Syntax-check inline JavaScript when a local runtime is available.
- If a sidecar JSON file exists, parse it with `node`, `python`, or `jq`.
- If browser tooling is available and the visualization is substantial, open it and check for console errors and obvious layout failures.

Example checks:

```bash
node -e "const fs=require('fs'); const html=fs.readFileSync('visualization.html','utf8'); if (!html.trim()) throw new Error('empty html'); if (/<(script|link|img|iframe|source|video|audio)[^>]+(?:src|href)=['\"]https?:/i.test(html)) throw new Error('external resource found'); for (const m of html.matchAll(/<script>([\\s\\S]*?)<\\/script>/g)) new Function(m[1]); console.log('html ok')"
node -e "const fs=require('fs'); JSON.parse(fs.readFileSync('visualization-data.json','utf8')); console.log('json ok')"
```

Report checks that could not run.

## Readability Principles

These are durable lessons from prior iterations. Apply them by default when producing any artifact under this skill. They live here, not in any single example, so the family stays coherent.

### Plain English on the surface

The first viewport of any artifact reads like a customer report, not a developer log.

- No file paths, code identifiers, function names, version numbers, threshold values, or internal jargon above the fold.
- Three surface blocks side by side carry the load: WHAT (disputed color), WHY (inferred color), FIX (observed color). Same three colors used everywhere else so the reader internalizes the system after the second report.
- Apply caveman style to surface prose. Short sentences. Numbers beat words. Identifiers in backticks. Cut hedging (`likely`, `appears`, `probably`, `seems`, `might`).
- Surface body type is 17px sans. Anything smaller and the eye skips it.

### One thing per node, one fact per line

- A node, pill, card, or block carries one idea. If it has two, split it.
- In learning or knowledge sections: one caveman headline plus one ASCII flow plus one rule of thumb. Not paragraphs.
- ASCII flows beat prose for protocols, state machines, and ordering. Use box-drawing chars (`─ ┐ ├ ┤ │ ┘ ●`) with color spans.

### Visual encoding carries the weight

If color plus stroke plus arrowhead already encode meaning, drop the text label.

- Confidence trio (observed mint, inferred amber, disputed red) is used identically across every lens, every card, every chip.
- Edge labels are caveman. One word, lowercase mono: `in`, `amp`, `fix`, `?`, `yes`, `→`. Not `amplified by` or `mitigated by`.
- Skip edge labels entirely when the arrowhead already says it (mint head = mitigation, dashed amber = inferred, coral hatch = disputed).
- Do not restate in text what the visual shows. Two encodings of the same fact is clutter.

### Layered information model

The artifact has three layers. The eye lands on Layer 1 and stops if that is all the reader needs.

- Layer 1: surface (WHAT, WHY, FIX in plain English).
- Layer 2: lenses (one canvas per diagnostic question, click anything for detail).
- Layer 3: evidence ledger (citations with code, scrolled into view from refs in Layer 2).

For investigation reports, also split top-level tabs into Diagnostic (the case) and Learning (reusable knowledge pills about the domain). Diagnostic answers "what happened here". Learning answers "what should I remember for next time".

### Type sizes

- Surface body: 17px sans.
- Section heads: 14 to 16px sans.
- Running body in Layer 2: 13px sans.
- Node labels in diagrams: 13px sans minimum.
- Meta inside narrow boxes: 11px mono. Drop suffixes (`conf high`) when the stroke style already encodes them.
- Mono is reserved for identifiers and code. Everything human-readable is sans.

### Layout: stack when wide, hide when empty

- Two dense columns become two rows. Vertical space is cheap.
- If a side rail or sub-panel has no content for the current view, hide it. Do not show an empty 280px sidebar.
- Tables become cards become single-column on narrow viewports.
- If two panels show the same data in different framings, drop one. A timeline lens already shows ordering; a "story" column that retells it in prose is redundant.

### Band separators in layered graphs

In node graphs with layered rows (symptom > hypothesis > factor > mitigation):

- Draw a full-width horizontal rule between each band. 2px solid in the strong rule color. Not dashed, not thin.
- Label each band in mono caps (`SYMPTOM`, `HYPOTHESES`, `FACTORS`, `MITIGATIONS`) so the reader does not have to parse layout.
- This works even when the graph itself is dense, because the bands give the eye anchors.

### Design tokens, not ad-hoc colors

- Use the Typesense Visual Docs token system (see `examples/not-ready-or-lagging/design-tokens.css`): IBM Plex Sans/Mono/Serif, ink/lime/indigo brand, `paper`/`cream`/`ink` surfaces via `data-surface` on `<html>`.
- Confidence trio is `--c-observed` (forest), `--c-inferred` (amber), `--c-disputed` (red).
- Density is switchable via `data-density="dense"` or `data-density="airy"`. Do not hardcode pixel sizes that override the token ladder.

### Self-contained, offline, portable

- Inline all CSS and JavaScript.
- IBM Plex Sans/Mono/Serif via Google Fonts is the one allowed remote dependency. Everything else is inline.
- The artifact must work when opened from a USB drive with no network.

## Output Naming

Choose names that match the subject:

- `diagnostics-map.html`
- `incident-timeline.html`
- `issue-triage-map.html`
- `workflow-map.html`
- `dependency-map.html`
- `visualization.html` when the user did not specify a topic.

Use a sidecar JSON only when requested, useful for future agent consumption, or when the source model is large enough to inspect separately.

## Reference Example

A worked example lives at `examples/not-ready-or-lagging/`:

- `data.json`: structured causal model (entities, relationships, timeline events, evidence anchors, uncertainties) for a Typesense Cloud HA-upgrade investigation.
- `report.html`: self-contained interactive artifact built on the layered information model (Layer 1 plain-English WHAT/WHY/FIX surface, Layer 2 three lens views, Layer 3 evidence ledger).
- `report-editorial-v1.html`: earlier editorial direction, preserved as a sibling reference.
- `DESIGN-NOTES.md`: the design system (tokens, components, layout, port instructions). Read this before producing a new investigation report so the family stays visually coherent.

Use the example to calibrate scope, evidence density, and how to keep disputed hypotheses visible rather than smoothing them away. Follow `DESIGN-NOTES.md` when generating a new investigation report.

## Quality Bar

- The visual should answer the user's actual question without requiring them to read all source material.
- The model should preserve evidence, uncertainty, and relationships.
- The UI should be interactive enough to explore, not just decorative.
- The artifact should be portable and offline.
- The final response should link the artifact and summarize validation.

## Accuracy Rules

- Do not invent entities, causes, owners, timelines, or relationships.
- Label inferred relationships clearly.
- Preserve exact timestamps, IDs, file paths, URLs, issue numbers, and command names when available.
- Show contradictions and unknowns rather than smoothing them away.
- Do not hide low-confidence claims inside confident visuals.
- Avoid changing source files unless the visualization task explicitly requires it.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "A pretty diagram is enough." | The diagram must encode evidence, relationships, status, and uncertainty. |
| "The user can inspect the source if they need details." | The visualization should surface evidence and make inspection faster. |
| "Remote CSS is fine for a one-off artifact." | Self-contained output stays portable and works offline. |
| "Ambiguity will clutter the visual." | Hidden ambiguity is worse. Use visual treatment for uncertainty. |
| "Everything belongs in one graph." | Use the grammar that matches the question. Timelines, boards, and matrices often beat graphs. |
| "The surface needs the function name so the reader knows what is broken." | Layer 1 stays plain English. The function name lives in Layer 2 and Layer 3 where the reader chose to look. |
| "Two visual encodings reinforce each other." | Two encodings of the same fact is clutter. Drop the redundant one. |
| "More columns fit more information." | Columns make text narrow and dense. Stack to rows when content is wide. |
| "A side rail is always useful." | An empty side rail is wasted real estate. Hide it on views that have nothing to focus. |

## Red Flags

- No evidence model.
- Generic pastel graph with no hierarchy, status, confidence, or source links.
- HTML depends on a CDN or external image.
- No search or filtering for dense material.
- Causal claims appear without supporting evidence.
- Timeline order is guessed but not labeled as inferred.
- Issues are shown without severity, status, impact, or next action.
- Surface text (Layer 1) contains file paths, function names, threshold values, or version numbers.
- Edge labels are verbose (`amplified by`, `mitigated by`) when one-word caveman forms (`amp`, `fix`) would carry the same meaning.
- Side rail or focus panel is visible on a view that has no entities to focus on.
- Two panels restate the same information in different framings (Story column duplicating Minute lens, etc.).
- Node labels or meta text overflow narrow boxes because font size was bumped without adjusting node width.
- Layered causal graph has no horizontal band separators between symptom, hypothesis, factor, and mitigation rows.
- Knowledge or learning section is paragraphs of prose instead of one caveman headline plus one ASCII flow plus one rule.
- Body type smaller than 13px in any view the reader is meant to read, or 11px on identifiers.
- Surface prose uses hedging words (`likely`, `appears`, `probably`, `seems`, `might`).
- Ad-hoc colors instead of the confidence trio and the design tokens.

## Verification

Before final response, confirm:

- [ ] Source material was gathered and normalized.
- [ ] The visual grammar matches the user's goal.
- [ ] The HTML is self-contained.
- [ ] Interactive controls work at a code-inspection level.
- [ ] Evidence and uncertainty are visible.
- [ ] Any sidecar JSON parses.
- [ ] Layer 1 surface text is plain English with no file paths, identifiers, or jargon.
- [ ] Edge labels are short. Skip them where arrowhead and stroke already carry the meaning.
- [ ] Side rail is hidden on views with no entities to focus on.
- [ ] No two panels restate the same information in different framings.
- [ ] Final response includes artifact path and validation results.
