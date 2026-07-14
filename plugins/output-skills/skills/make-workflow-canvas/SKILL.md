---
name: make-workflow-canvas
description: Creates polished, editable, self-contained workflow and architecture canvases with draggable nodes, typed ports, connectable edges, inspectors, validation, import/export, and clearly separated synthetic previews or observed trace overlays. Use when a user asks for a workflow builder, node editor, FlowGraph-style designer, editable architecture canvas, process orchestration map, or interactive flow prototype. Not for static architecture reports, generic dashboards, or production workflow execution engines.
---

# Make Workflow Canvas

## Overview

Create a dense, full-viewport workflow editor that opens directly in a browser and feels like a real internal tool. The output is a self-contained HTML artifact with an editable node canvas, not a static diagram wearing application chrome.

Start from the canonical reference at `examples/workflow-canvas-reference.html`. Preserve its tested interaction runtime and replace the embedded model, copy, palette categories, and domain specific fields. Read `references/workflow-canvas-contract.md` before changing the model or runtime. The embedded model is UTF 8 JSON encoded as Base64 inside a non executable script element. Never paste raw JSON into an HTML raw text element.

## When to Use

Use this skill when the user asks for:

- An editable workflow builder or node editor.
- A draggable architecture or orchestration canvas.
- A FlowGraph-style process designer.
- Typed input and output ports with connectable edges.
- A workflow prototype with inspector, validation, minimap, logs, or traces.
- A local HTML artifact that behaves like a compact operations tool.

Do not use this skill for:

- A source-grounded codebase architecture report plus agent JSON. Use `make-architecture-flow`.
- An incident, timeline, diagnostic report, issue board, or evidence dashboard. Use `make-interactive-visualization`.
- A general single-file report without an editable graph. Use `html-output`.
- A production workflow executor, collaborative editor, backend service, or remote telemetry client.

## Required Inputs

Before writing the artifact, identify:

1. The workflow's purpose and intended operator.
2. Node categories and reusable node types.
3. The initial graph: nodes, ports, edges, positions, and short descriptions.
4. Contracts or schemas that make connections compatible or incompatible.
5. Which facts are observed, inferred, proposed, synthetic, or unknown, plus the evidence that supports every observed artifact or node claim.
6. Whether any real observed run data exists, how it was sanitized, who verified it, which workflow artifact and version it belongs to, which canonical graph digest it binds to, and which independently anchored SHA 256 digest authorizes Trace mode.

If the canvas represents a real codebase, inspect source, config, tests, and executable entry points. Do not infer runtime architecture from folder names alone. Keep exact evidence paths in node metadata when available.

## Workflow

### 1. Read the Reference and Contract

Read these files before creating output:

- `examples/workflow-canvas-reference.html`
- `references/workflow-canvas-contract.md`

Copy the reference to the requested output path. Adapt its embedded model and visible labels. Do not rebuild the runtime from memory unless the user explicitly requests a different implementation.

Serialize the model safely:

1. Produce normalized JSON.
2. Encode the UTF 8 bytes as Base64.
3. Replace only the Base64 text inside `#workflow-data`.
4. Confirm the embedded text matches `^[A-Za-z0-9+/=\\s]+$` and decodes to valid `workflow-canvas/1` JSON.

Do not place raw JSON inside `<script>`, `<template>`, `<textarea>`, or another HTML raw text container. A model string containing a closing tag can otherwise break out before runtime normalization.

Default output name:

```text
workflow-canvas.html
```

### 2. Normalize the Workflow Model

Use stable IDs for categories, nodes, ports, edges, schemas, previews, and observed runs.

Keep these concerns separate:

- `catalog`: reusable node templates shown in the palette.
- `graph`: the editable design model.
- `runtime.preview`: generated synthetic behavior for demonstration only.
- `runtime.observed_runs`: sanitized evidence claims imported from a real system. They remain unverified until a trusted digest anchor validates their canonical content and their artifact and graph binding matches the active normalized workflow.

Every node needs:

- A human label and compact machine type.
- A category with icon and direct text label.
- A short responsibility statement.
- Stable position and typed ports.
- Status and owner labels when meaningful.
- Evidence or provenance when the graph claims to describe a real system.

Every edge needs stable endpoints, an edge kind, and a concise label only when the connection is not obvious from direction and styling.

### 3. Preserve the Product Shell

The first viewport is the editor itself. Preserve this hierarchy:

1. Compact top toolbar with title, modes, import, export, save, validate, and preview actions.
2. Searchable grouped palette on the left.
3. Dotted pan and zoom canvas in the center.
4. Editable inspector on the right.
5. Collapsible validation and diagnostics panel at the bottom.
6. Minimap and viewport controls inside the canvas.

Keep the interface dense but readable:

- System sans for labels and system monospace for IDs, types, schemas, and timings.
- Hairline borders, restrained shadows, small radii, and one primary accent.
- Category colors always paired with icons and text. Color never carries identity alone.
- Status colors always paired with a label or icon.
- Focus rings remain visible.
- `prefers-reduced-motion` disables decorative movement.

### 4. Keep the Core Interaction Paths Complete

The artifact must support:

- Palette search by label and machine type.
- Drag from palette to canvas to create a node.
- Node selection and editable inspector fields, including port label, schema, required, and multiple controls.
- Grid-snapped node dragging.
- Background pan, bounded zoom, fit view, and minimap.
- Drag from output port to input port to connect nodes.
- Live connection preview and actionable rejection messages.
- Node and edge deletion with dependent-edge cleanup.
- Bounded session undo and redo.
- Guarded local save scoped only to the embedded artifact ID, normalized JSON export, and bounded validated import.
- Local restore from exactly `workflow-canvas:<embedded-artifact-id>:v1`, with exact stored artifact ID equality and no global last opened pointer.
- Validation issues that select and center the affected entity.

Imported strings must enter the DOM through `textContent`, form values, or explicit attribute setters. Never evaluate imported code or interpolate imported values into `innerHTML`. Normalize imported artifact and node claims with `trustedClaims: false`; downgrade imported `observed` claims to `inferred` until the operator deliberately reclassifies evidence.

### 5. Tell the Truth About Runtime Data

Synthetic behavior is useful for demonstrating a workflow, but it is not a trace.

- Label generated runs `Synthetic preview` in the toolbar, canvas banner, timeline, and logs.
- Use action text such as `Preview run`, never `Run live`.
- Disable observed Trace mode unless at least one run passes trusted digest verification.
- Treat every imported `kind: "observed"` value as a claim, not proof. Normalize it to `unverified` first.
- Every observed run names its `artifact_id`, `artifact_version`, and `graph_digest` directly in the run.
- Canonicalize the active normalized workflow before hashing. Bind artifact ID, version, title, and purpose, graph name, description, and mode, schema IDs and labels, every node ID, type, label, description, category, owner, status, position, typed port and metadata field, and every edge ID, endpoint, kind, label, and async flag. Sort schemas, nodes, ports, evidence, and edges by stable ordinal text before compact JSON serialization.
- Require exact observed fixture fields at every object level. Reject unknown fields rather than silently accepting unsigned data.
- Enable Trace only when the run is sanitized, has provenance and capture time, sets `verification.trusted: true`, uses `SHA-256`, matches its canonical content digest, matches the active artifact ID and version, matches the active graph SHA 256 digest, references only active node IDs, and the run digest appears in the HTML's independently maintained `TRUSTED_OBSERVED_DIGESTS` anchor set.
- Verify a standalone observed run against the current active normalized model. Verify observed runs inside a full model import against the temporary normalized imported model before assigning that model to active state.
- Never trust a digest merely because the imported JSON contains it. Unanchored or graph mismatched runs stay unverified, and standalone imports do not enter Trace.
- Immediately downgrade every verified run and disable Trace after any graph or model edit, including label or description changes, node movement, port edits, edge edits, graph title changes, deletion, duplication, undo, and redo.
- Label test data as a fixture, never as live production evidence. Remove the reference fixture anchor when adapting the canvas unless evidence for that exact graph is intentionally bundled.
- The HTML artifact must not call or execute nodes, services, agents, APIs, or tools.

### 6. Ship Safe Diagnostics

Retain the bounded in-memory diagnostic ring buffer from the reference. Emit stable events for initialization, model loading, rendering, selection, editing, connections, validation, storage, import, export, preview, and unhandled failures.

Diagnostic fields are allowlisted. They may contain only:

- Timestamp, level, and event name.
- Opaque session local references for nodes, edges, or ports. Never raw imported IDs.
- Safe fixed operation codes or allowlisted exception classes. Never derive a code from arbitrary error message text.
- Small counts and duration values.

Never record model bodies, node configuration values, prompts, message text, inputs, outputs, tokens, cookies, headers, user names, email addresses, customer IDs, raw model identifiers, or other PII. Diagnostics stay local and in memory until the user explicitly exports them. Use a constant diagnostics filename rather than an imported artifact ID.

### 7. Validate the Artifact

From the copied `make-workflow-canvas` skill base directory, run the bundled validator against the actual generated output:

```bash
python scripts/validate-artifact.py /path/to/generated-workflow-canvas.html
```

This validator travels with the skill and checks the generated artifact itself. When contributing to the `alanistic-skills` repository, also run the repository validators from the repository root:

```bash
python scripts/validate-skills.py
python scripts/validate-workflow-canvas.py
```

Then open the generated HTML from `file://` and verify at approximately 1600 by 900 and 1280 by 800:

- No external requests and no console errors.
- Palette search, node creation, drag, edit, delete, undo, and redo.
- Pan, zoom, fit, minimap, and responsive side panels.
- Valid and rejected port connections.
- Validation issue navigation and repair.
- Save and reload use only the embedded artifact scoped key, reject a foreign artifact ID, and never consult a global last opened pointer.
- Export and import round trip.
- Synthetic preview labels on every preview surface.
- Observed Trace disabled for self asserted, unanchored, mismatched, unsanitized, artifact mismatched, or graph mismatched run claims; enabled only for a fixture whose run digest and graph binding both verify.
- The trusted fixture fails against a graph with a changed node label or topology, and any edit after verification, including node movement, immediately disables Trace.
- Imported observed artifact and node claims downgrade to inferred.
- Diagnostics use opaque entity references, fixed error codes, and a constant filename without exposing model content or imported IDs.
- Hostile free text containing mixed case closing script tags remains inert because the model is Base64 encoded.
- Keyboard focus, reduced motion, and narrow viewport behavior.

Record checks that could not run. Do not claim visual or interaction verification from static parsing alone.

## Accuracy and Security Rules

- Distinguish observed, inferred, proposed, synthetic, and unknown information.
- Do not invent services, queues, databases, contracts, timings, or traces.
- Do not load remote scripts, fonts, images, styles, iframes, or media.
- Do not make network requests from the artifact.
- Do not use `eval`, `Function`, imported event handlers, or unsafe HTML insertion.
- Base64 encode embedded model JSON so closing tag text cannot escape the data container.
- Bound imported file size and validate structure before replacing the active model.
- Downgrade untrusted imported observed claims and verify Trace data against an independently anchored SHA 256 run digest plus the active artifact ID, artifact version, and canonical graph digest.
- Invalidate verified runs immediately after every graph or model mutation, including the first actual position change during a drag.
- Keep observed run data sanitized and outside undo history and persistent storage.
- Persist only under the embedded artifact scoped key and reject local save or restore when the artifact ID differs.
- Preserve unrelated user files and inspect an existing target before overwriting it.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "A screenshot-like layout is enough." | The value is in the interaction paths. Search, edit, connect, validate, persist, and recover must work. |
| "I can rebuild the canvas faster than reading the reference." | Rebuilding loses calibrated spacing, controls, state transitions, safety checks, and edge cases. Reuse the reference runtime. |
| "The preview looks like a trace, so the label is harmless." | Synthetic output presented as observed evidence is false telemetry. Label it synthetic everywhere. |
| "Imported JSON is trusted because it is local." | Local files can still contain hostile strings or malformed structures. Validate and render as text. |
| "Console logging is enough for debugging." | Console output disappears and often leaks payloads. Use the bounded sanitized Diagnostics panel. |
| "A CDN is acceptable for a prototype." | The artifact must remain portable and open directly from disk without network access. |

## Red Flags

- A marketing hero or summary page appears before the canvas.
- Nodes are decorative cards with no selection, ports, or editable fields.
- Imported data reaches `innerHTML`, raw HTML embedding, or executable code paths.
- Raw JSON is pasted into an HTML raw text element instead of Base64 encoded.
- Trace mode works from self asserted provenance, an unanchored digest, or a run bound to another artifact version or graph.
- Trace remains enabled after a node contract, port, edge, title, undo, or redo change.
- Local restore follows a global last opened pointer or accepts a stored artifact ID different from the embedded artifact.
- Imported artifact or node claims retain observed status automatically.
- Synthetic logs are described as observed or live.
- Diagnostics include raw model IDs, labels, descriptions, configs, prompts, inputs, outputs, arbitrary error messages, or whole errors.
- Category or status meaning depends on color alone.
- The artifact requires a server, build step, package install, or network request.
- Validation issues cannot navigate to the broken node or edge.
- The layout works only at the author's viewport.

## Verification

Before responding, confirm:

- [ ] The canonical reference and contract were read and reused.
- [ ] The output opens directly from `file://` with no remote resources.
- [ ] The first viewport is the workflow editor.
- [ ] Palette, canvas, inspector, minimap, validation, and diagnostics are present.
- [ ] Node creation, editing, dragging, deletion, undo, and redo work.
- [ ] Typed port connection and rejection paths work.
- [ ] Embedded JSON is UTF 8 Base64 and hostile closing tag text cannot escape into HTML.
- [ ] Import is size bounded, structurally validated, and safely rendered.
- [ ] Export and import preserve stable IDs and positions.
- [ ] Imported observed artifact and node claims downgrade to inferred.
- [ ] Synthetic preview is labeled synthetic everywhere.
- [ ] Observed Trace requires a sanitized run whose SHA 256 digest matches the canonical run payload and an independent trusted anchor, and whose artifact ID, artifact version, and graph digest match the active normalized model.
- [ ] Changed labels and topology reject the old trusted fixture, and every edit after successful verification, including node movement, immediately disables Trace.
- [ ] Local save and restore use only the embedded artifact scoped key and reject foreign artifact IDs.
- [ ] Diagnostics are bounded, local, allowlisted, use opaque entity references and fixed codes, and export with a constant filename.
- [ ] Keyboard, reduced-motion, and both target viewport checks passed.
- [ ] Static validators and browser verification results are reported honestly.
