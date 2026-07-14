# Workflow Canvas Contract

This contract defines the portable data model, interaction behavior, runtime truthfulness rules, security boundaries, and diagnostic fields for artifacts created by `make-workflow-canvas`.

## Output Shape

The default deliverable is one self-contained HTML file that:

1. Opens directly from `file://`.
2. Contains all CSS, JavaScript, SVG, icons, and model data inline.
3. Stores model JSON as UTF 8 Base64 in the non executable `#workflow-data` element. Raw JSON must not be pasted into an HTML raw text element because closing tag text can escape before normalization.
4. Makes no network requests.
5. Uses no remote fonts, scripts, styles, images, iframes, or media.
6. Requires no package install, build step, or server.
7. Allows normalized JSON export and validated JSON import.

## Top-Level Model

```json
{
  "schema_version": "workflow-canvas/1",
  "artifact": {},
  "catalog": {},
  "graph": {},
  "runtime": {}
}
```

### Artifact

```json
{
  "id": "sample-workflow",
  "title": "Sample Workflow",
  "purpose": "Demonstrate a local workflow canvas",
  "version": "1.0.0",
  "generated_at": "2026-01-01T00:00:00.000Z",
  "provenance": {
    "status": "proposed",
    "sources": []
  }
}
```

Rules:

- `id` is stable, lowercase, and safe for a local storage key.
- `provenance.status` is one of `observed`, `inferred`, `proposed`, or `unknown`.
- `observed` requires at least one concrete source reference in `provenance.sources`.
- Models loaded from the Base64 bundle may preserve evidence backed observed claims. Models imported at runtime normalize with `trustedClaims: false`, so imported observed claims downgrade to inferred rather than becoming fact from self assertion.
- Real architecture claims include source paths, URLs, command evidence, or explicit uncertainty.

### Catalog

```json
{
  "categories": [
    {
      "id": "triggers",
      "label": "Triggers",
      "icon": "bolt",
      "color": "#eda100"
    }
  ],
  "node_types": [
    {
      "type": "trigger.webhook",
      "label": "Webhook",
      "description": "Receives an external event.",
      "category": "triggers",
      "owner": "integration",
      "badge": "EXT",
      "ports": {
        "inputs": [],
        "outputs": [
          {
            "id": "event",
            "label": "event",
            "schema": "event/v1",
            "required": false,
            "multiple": true
          }
        ]
      }
    }
  ]
}
```

Rules:

- Category identity uses icon plus text, never color alone.
- Node type IDs are stable machine-readable strings.
- Palette descriptions are one short sentence.
- Port IDs are unique within a node type and use lowercase machine-readable strings.

### Graph

```json
{
  "metadata": {
    "name": "Sample Workflow",
    "description": "A fabricated example workflow.",
    "mode": "design"
  },
  "schemas": [
    {
      "id": "event/v1",
      "label": "Event v1"
    }
  ],
  "nodes": [
    {
      "id": "node-webhook",
      "type": "trigger.webhook",
      "label": "Incoming Webhook",
      "description": "Accepts a signed event.",
      "category": "triggers",
      "owner": "integration",
      "status": "active",
      "position": { "x": 96, "y": 160 },
      "ports": {
        "inputs": [],
        "outputs": [
          {
            "id": "event",
            "label": "event",
            "schema": "event/v1",
            "required": false,
            "multiple": true
          }
        ]
      },
      "metadata": {
        "evidence": [],
        "confidence": "high",
        "fact_status": "proposed"
      }
    }
  ],
  "edges": [
    {
      "id": "edge-webhook-parser",
      "source": { "node": "node-webhook", "port": "event" },
      "target": { "node": "node-parser", "port": "event" },
      "kind": "data",
      "label": "event",
      "async": false
    }
  ]
}
```

Node rules:

- Node IDs are globally unique and stable across export and import.
- Positions use finite integer canvas coordinates. Normalize imported coordinates to integers before rendering, export, or digest construction, and normalize negative zero to zero.
- `status` is one of `active`, `draft`, `paused`, `failing`, or `unknown`.
- `metadata.fact_status` is one of `observed`, `inferred`, `proposed`, or `unknown`.
- `observed` requires one or more concrete `metadata.evidence` references.
- Runtime imports downgrade observed node claims to inferred. A user can deliberately reclassify a node only when evidence exists.
- Imported metadata is data only. It never becomes executable code.

Port rules:

- Inputs and outputs use distinct arrays.
- Each port has `id`, `label`, and `schema`.
- Required inputs without an incoming edge produce a validation issue.
- An input with `multiple: false` accepts at most one incoming edge.
- Output-to-input is the only valid connection direction.

Edge rules:

- Endpoints must identify existing nodes and ports.
- Self-connections and exact duplicate connections are rejected.
- Edge kinds are `data`, `control`, `error`, `event`, or `trace`.
- Incompatible non-empty schemas produce an actionable issue or rejection.
- Removing a node or port removes dependent edges.

### Runtime

```json
{
  "preview": {
    "kind": "synthetic",
    "label": "Synthetic preview",
    "steps": []
  },
  "observed_runs": []
}
```

Synthetic preview rules:

- `kind` is always `synthetic`.
- Every related toolbar, banner, timeline, log, and status label includes the word `Synthetic`.
- Preview data demonstrates rendering only. It never calls nodes or external systems.
- Preview step offsets and durations are normalized nonnegative integers. Playback may compress wall time proportionally to about five seconds, but displayed offsets and durations remain the original normalized values.
- Use one cancellable scheduler for preview playback. Process every due event in each frame and render at most once per frame.

Observed run shape:

```json
{
  "id": "observed-fixture-1",
  "kind": "observed",
  "label": "Observed run fixture",
  "captured_at": "2026-01-01T00:00:00.000Z",
  "sanitized": true,
  "artifact_id": "sample-workflow",
  "artifact_version": "1.0.0",
  "graph_digest": "0000000000000000000000000000000000000000000000000000000000000000",
  "provenance": {
    "type": "fixture",
    "source": "local sanitized fixture"
  },
  "verification": {
    "trusted": true,
    "algorithm": "SHA-256",
    "digest": "0000000000000000000000000000000000000000000000000000000000000000"
  },
  "steps": [
    {
      "node_id": "node-webhook",
      "status": "succeeded",
      "offset_ms": 0,
      "duration_ms": 12,
      "error_code": ""
    }
  ]
}
```

The zero digests above are shape placeholders. Generated artifacts must replace them with real SHA 256 values.

Observed trace rules:

- Every imported `kind: "observed"` value starts as an unverified claim.
- Trace mode stays disabled until at least one run passes trusted run digest and active graph binding verification.
- A structurally valid claim has exactly the documented fields, `kind: "observed"`, an ISO capture timestamp, `sanitized: true`, direct `artifact_id`, `artifact_version`, and `graph_digest` fields, provenance type and source, and one or more bounded steps. Unknown fields at any fixture object level are rejected rather than ignored.
- `artifact_id` and `artifact_version` must equal the supplied normalized model.
- `graph_digest` must equal the SHA 256 digest of the canonical payload for that same normalized model.
- Every observed step must reference a node in that model.
- A verified run additionally has `verification.trusted: true`, `algorithm: "SHA-256"`, a 64 character lowercase run digest, a digest that matches the canonical normalized run payload, and the same run digest in the HTML's independently maintained `TRUSTED_OBSERVED_DIGESTS` set.
- Standalone observed run import verifies against the current active normalized model. Full model import first normalizes and validates a temporary candidate, then verifies its observed runs against that same temporary candidate before assigning it to active state.
- The canonical run payload is `schema_version` plus `observed_run` with fields in this exact order: `id`, `kind`, `label`, `captured_at`, `sanitized`, `artifact_id`, `artifact_version`, `graph_digest`, `provenance`, and `steps`. It omits `verification`. Every step contains `node_id`, `status`, integer `offset_ms`, integer `duration_ms`, and `error_code`, using an empty string when no error code exists. Normalize negative zero to zero before serialization.
- The canonical graph payload uses `schema_version: "workflow-canvas-graph/1"`, then `artifact`, then `graph`. `artifact` contains `id`, `version`, `title`, and `purpose`. `graph` contains `metadata`, `schemas`, `nodes`, and `edges` in that order.
- Graph metadata contains `name`, `description`, and `mode`. Schemas contain `id` and `label`. Nodes contain `id`, `type`, `label`, `description`, `category`, `owner`, `status`, `position`, `ports`, and `metadata`. Position contains integer `x` and `y`, with negative zero normalized to zero. Each port contains `id`, `label`, `schema`, `required`, and `multiple`. Node metadata contains `confidence`, `fact_status`, and sorted `evidence`. Edges contain `id`, `source`, `target`, `kind`, `label`, and `async`.
- Sort schemas, nodes, input ports, output ports, and edges by stable ID with ordinal string comparison before compact `JSON.stringify` serialization. Preserve the declared field order above. Hash the UTF 8 bytes with SHA 256 and encode lowercase hexadecimal.
- Any graph or model edit immediately downgrades every verified run, clears the selected observed run, switches Trace to Design, and disables Trace. This includes title changes, node movement, node or edge edits, port edits, creation, deletion, duplication, undo, and redo.
- A digest or trusted marker supplied only by imported JSON is not a trust anchor. An operator must verify the sanitized source and add its run digest to the generated HTML separately.
- Unanchored, artifact mismatched, graph mismatched, unsupported, or unverifiable claims retain `kind: "unverified"`, keep `verification.status: "unverified"`, and never switch the interface into Trace.
- Fixture data remains visibly labeled as a fixture. When adapting the reference to another workflow, remove the fixture anchor unless an independently verified run for that exact graph is bundled.
- Observed records contain workflow identity, graph digest, node IDs, status, timing, and safe error codes only. They do not contain request bodies, prompts, messages, headers, tokens, or customer data.

## Validation Issue Shape

```json
{
  "id": "required-input:node-transform:input",
  "severity": "error",
  "code": "required_input_unconnected",
  "message": "Transform input is required but has no incoming edge.",
  "entity": {
    "kind": "node",
    "id": "node-transform"
  }
}
```

Allowed severity values are `error`, `warning`, and `info`.

At minimum validate:

1. Schema version.
2. Unique node, edge, schema, and per-node port IDs.
3. Finite node positions.
4. Existing node types and categories.
5. Existing edge nodes and ports.
6. Output-to-input direction.
7. Duplicate and self-connections.
8. Schema compatibility.
9. Required unconnected inputs.
10. Single-input multiplicity.
11. Observed run exact fields, provenance, sanitization, active artifact identity, canonical graph digest, active node membership, explicit trusted marker, supported algorithm, canonical observed digest, and independent digest anchor.

Clicking a validation issue selects and centers its target when the entity still exists.

## Interaction Contract

### Find and Create

- `/` focuses palette search when the user is not typing in a field.
- Search matches visible labels, machine types, descriptions, and category labels.
- Dragging a palette item onto the canvas creates a stable-ID node at the transformed pointer position.

### Select and Edit

- Clicking anywhere on a node card or on an edge selects it. Port interactions remain isolated from card selection.
- Clicking the canvas background clears selection.
- The inspector exposes fields appropriate to the selected graph, node, or edge.
- Port editing exposes label, schema, required, and multiple flags.
- Form edits update the model and canvas immediately.
- Imported strings render through safe text or value APIs.

### Arrange

- Nodes snap to an 8 pixel grid.
- Background pointer drag pans the canvas.
- Wheel or controls zoom within a bounded range.
- Fit view includes all nodes with usable padding.
- The minimap reflects nodes and the current viewport.

### Connect

- Drag begins at an output port and ends at an input port.
- A visible connection preview follows the pointer.
- Rejections explain direction, duplicate, self-connection, multiplicity, or schema problems.

### Correct Mistakes

- Delete removes the selected node or edge when focus is not in a form field.
- Node deletion removes dependent edges.
- Undo and redo use bounded snapshots of graph design data plus the synchronized artifact title.
- Node pointer down does not create a snapshot or clear redo. Push one snapshot only on the first actual snapped coordinate change, before mutating the position.
- Runtime observations and diagnostics never enter undo history.

### Persist and Exchange

- Capture the normalized embedded artifact ID before any local restore.
- Local storage uses only `workflow-canvas:<embedded-artifact-id>:v1`.
- Do not use a global last opened pointer that can restore another artifact under the same origin.
- Restore only when the raw stored model has `artifact.id` exactly equal to the embedded artifact ID. Ignore or reject every foreign artifact.
- Reject local save when the active model artifact ID differs from the embedded artifact ID.
- Storage failure degrades to in-memory operation and emits a sanitized diagnostic.
- Import has a strict byte limit and validates before replacing the current graph.
- A successful full model import cancels the old synthetic preview scheduler and clears preview active, status, and log state before replacing the model. A standalone observed import that switches to Trace clears the same preview state first.
- Runtime model imports downgrade observed artifact and node claims to inferred.
- Standalone observed run imports remain unverified and do not enter Trace unless canonical SHA 256 verification, active graph binding, and an independent trusted anchor all succeed.
- Export emits normalized JSON with stable IDs and positions.

## Visual Contract

Recommended defaults:

- Toolbar: approximately 44 pixels.
- Palette: approximately 240 pixels.
- Inspector: approximately 320 pixels.
- Bottom panel: approximately 216 to 232 pixels.
- Node width: approximately 224 pixels.
- Grid: 8 pixels.
- Surface: near white with a subtle dotted canvas.
- Text: system sans; machine fields and timing use system monospace.
- Borders: one pixel hairlines.
- Shadows: restrained and functional.
- Radius: small and shared.
- Category palette: fixed and color-vision-distinct.
- Status palette: separate from categories and paired with labels or icons.

Responsive behavior:

- Below a wide desktop layout, collapse palette and inspector before making the canvas unusably narrow.
- Keep controls reachable and non-overlapping around 1280 by 800.
- Preserve visible focus styles.
- Disable decorative movement under `prefers-reduced-motion`.

## Diagnostic Contract

Diagnostics are local, bounded, and safe by construction.

Recommended event names:

```text
app_init
model_loaded
model_validation_failed
render_started
render_completed
render_failed
selection_changed
node_created
node_moved
node_updated
node_deleted
edge_connected
edge_rejected
edge_deleted
history_undo
history_redo
storage_save_succeeded
storage_save_failed
storage_load_succeeded
storage_load_failed
import_started
import_succeeded
import_failed
observed_verification_failed
export_succeeded
validation_completed
preview_started
preview_completed
unhandled_error
unhandled_rejection
```

Allowed diagnostic fields:

```text
ts
level
event
node_id
edge_id
port_id
error_code
count
duration_ms
```

Rules:

- Keep at most 200 recent records.
- Unknown diagnostic keys are discarded.
- `node_id`, `edge_id`, and `port_id` fields contain opaque session local tokens such as `n-1`, not raw imported identifiers.
- Error codes come only from fixed operation codes or an allowlisted exception class mapping. Never transform arbitrary `error.message` text into a diagnostic value.
- Diagnostics are not persisted or sent remotely.
- Explicit export contains only the bounded allowlisted records and uses the constant filename `workflow-canvas.diagnostics.json`.
- Global `error` and `unhandledrejection` handlers feed the same safe buffer.

Never record:

```text
graph bodies
raw artifact, node, edge, or port identifiers
node configuration values
prompts
messages
request or response bodies
inputs or outputs
cookies
tokens
headers
URLs with query strings
user names
email addresses
customer identifiers
raw error messages
```

## Security Contract

- No `eval`, `Function`, dynamic script insertion, imported event handler strings, or executable templates.
- No imported value reaches `innerHTML`.
- Embedded model JSON is compacted, encoded as UTF 8 Base64, and decoded before `JSON.parse`. The Base64 container cannot contain a literal closing script tag.
- JSON import is size bounded before parsing.
- Parsed structures are checked before replacing active state.
- Runtime imports cannot self promote artifact or node claims to observed.
- Trace accepts only canonical SHA 256 verified runs whose digest is independently anchored in the HTML and whose direct artifact identity, graph digest, and step node IDs match the supplied normalized model.
- Every model mutation invalidates verified runs before stale Trace state can survive the change.
- Local persistence is pinned to the embedded artifact ID and rejects foreign stored or active artifact IDs.
- IDs and strings have practical length bounds.
- Numeric coordinates and timings must be finite and clamped where appropriate.
- Diagnostic entity references are opaque tokens, error codes are fixed or class mapped, and the export filename is constant.
- Downloads use locally created `Blob` URLs and revoke them after use.
- The artifact makes no network requests and has no hidden execution path.

## Verification Matrix

| Area | Evidence |
|---|---|
| Startup | Opens from disk with no external requests or console errors |
| Palette | Search filters and drag creates a node |
| Canvas | Pan, zoom, fit, reset, drag, and minimap stay synchronized |
| Selection | Node and edge selection update the inspector |
| Editing | Safe form edits update the model and graph |
| History | Delete, undo, and redo restore expected design state |
| Connections | Compatible ports connect and invalid connections explain rejection |
| Validation | Issues navigate to targets and disappear after repair |
| Persistence | Save and reload use only the embedded artifact scoped key; a foreign stored artifact is not loaded; a foreign active artifact cannot overwrite the embedded draft |
| Embedded model | Base64 decodes to valid JSON; hostile mixed case closing script text remains inert |
| Import and export | Valid model round trips; malformed or oversized input is rejected; imported observed graph claims downgrade to inferred |
| Preview | Every preview surface says Synthetic |
| Trace binding | The trusted fixture enables Trace only for the exact artifact version and canonical graph; changing a node label or topology makes the old fixture fail verification |
| Trace invalidation | Editing a verified graph, including moving a node, immediately disables Trace and downgrades the verified run |
| Trace trust | Self asserted, unanchored, unknown node, mutated, or unsanitized claims remain disabled |
| Diagnostics | Export contains fixed event codes and opaque session references but no raw model IDs, model content, or sensitive data |
| Accessibility | Visible focus, keyboard shortcuts, reduced motion, semantic controls |
| Responsive | Palette and inspector collapse without obscuring the canvas |
