# Investigation Report . Design System (Layered)

A system for self-contained interactive investigation artifacts, optimized
for **glance comprehension**. The reader should understand **what** and
**why** in 3 seconds, without parsing identifiers, file paths, or numbers.

Reference implementation is `report.html`. Earlier directions preserved:
- `report-editorial-v1.html` . editorial / longform direction.

## Visual tokens . Typesense Visual Docs design system

The token layer (color, type, spacing, radii, shadows, motion) is sourced
from the **Typesense Visual Docs** design system. See `design-tokens.css`
in this folder for the canonical token set, mirrored inline at the top of
`report.html`.

Highlights:
- **Brand**: ink black (`#0A0A0A`), electric lime (`#C5F84A`),
  indigo (`#4F46E5`). Indigo is the default `--accent`.
- **Surfaces**: switchable via `data-surface` on `<html>`. `paper` (white,
  default), `cream` (warm off-white), `ink` (dark). Add the attribute
  to flip the entire palette without touching markup.
- **Confidence**: forest `#0E7A47` (observed), amber `#D97706` (inferred),
  red `#DC2626` (disputed). Same three colors used everywhere from graph
  edges to evidence chips.
- **Type**: IBM Plex Sans for narrative + UI, IBM Plex Mono for
  identifiers and code, IBM Plex Serif available for editorial display.
- **Spacing**: 4-px grid (`--s-1` = 4px through `--s-10` = 128px).
- **Density**: `data-density="dense"` and `data-density="airy"` on
  `<html>` re-scale type and spacing without changing component code.

Legacy token names (`--bg-0`, `--ink-0`, `--observed`, `--ff-sans`, etc.)
are kept as aliases that point at the new system tokens, so existing
report markup continues to work.

## Layered information model

The artifact has **three layers of information**. The eye lands on Layer 1
and stops if that's all the reader needs.

### Layer 1 — Surface (always visible, above the fold)

Plain English. **No file paths, no code identifiers, no version numbers,
no jargon.** Three blocks side by side:

| Block         | Color signal     | Length            | Job                                       |
| ---           | ---              | ---               | ---                                       |
| WHAT HAPPENED | coral (`disputed`) | 1–2 sentences   | The symptom as a customer would describe it |
| WHY IT HAPPENED | amber (`inferred`) | 2–3 sentences | The mechanism in human terms              |
| FIX           | mint (`observed`)| 1–2 sentences     | The action the reader should take         |

Each block carries a tiny `smeta` row at the bottom with one or two
qualifiers (scope, root, tracking-issue links) in mono. That's the only
mono on the surface — everything else is sans, big, conversational.

The colors are the same confidence-trio used everywhere else in the system
(coral / amber / mint), so the reader internalizes after the second report:
**red = the bad thing, amber = the cause, mint = the fix**.

### Layer 2 — Lens views (below the fold)

A `go deeper →` bridge sits directly under Layer 1 with five jump-links:
*causal mechanism · second-by-second · component wiring · evidence · what
we didn't measure.* Click any of them and you scroll to the lens canvas.

Layer 2 is where the file paths, the code identifiers, the timeline ticks,
and the entity graph live. The three lens tabs (Mechanism / Minute / Wiring)
each answer one diagnostic question:

- **Mechanism** — symptom → hypothesis → factor → mitigation (the causal graph)
- **Minute** — second-by-second across node, cloud, client (the timeline)
- **Wiring** — three readers, one atomic boolean, one writer (the arch flow)

Clicking any node, event, or component in a lens populates the sticky side
rail with that entity's detail. Confidence is encoded identically across
all lenses: solid mint stroke = observed, dashed amber = inferred, dashed
coral with hatch = disputed.

### Layer 3 — Evidence cards (deeper still)

The full ledger of 15 cards lives at the bottom of the page. Each card is
a citation: monospace `EV·NN · src/foo.cpp:lines · [conf chip]` header, a
short italic claim, and the actual code snippet in a darker mono block.

Refs in the side rail are clickable and smooth-scroll to the matching
evidence card with a 1.3s flash highlight, so a reader who lands on Layer
1, drills into Layer 2 to inspect a node, and then clicks a ref to verify,
makes a single continuous gesture from "what" to "why" to "proof".

## Tokens (unchanged across iterations)

### Color

Dark-first, cool-neutral. Surfaces (`--bg-0` → `--bg-3`), ink ladder
(`--ink-0` → `--ink-4`), and the confidence trio (`--observed`,
`--inferred`, `--disputed`) plus `--info`. Kind hues used only as 2-px
stripes on cards/nodes, never as fills.

### Type

System sans for everything readable, system mono for identifiers and code.
**Surface text is 17 px sans** — the only place body type is that large,
because the reader's eye should land there first. Type ladder:

| Role          | Size  | Family       | Used for                          |
| ---           | ---   | ---          | ---                               |
| surface body  | 17    | system sans  | What / Why / Fix prose            |
| `--t-h1`      | 16    | system sans  | bottom section heads              |
| `--t-h2`      | 14    | system sans  | canvas titles                     |
| `--t-body`    | 13    | system sans  | running text in Layer 2           |
| `--t-small`   | 12    | system sans  | takeaways, ledger claims          |
| `--t-meta`    | 11    | system mono  | eyebrows, IDs, file paths         |
| `--t-micro`   | 10    | system mono  | status tags, chip labels          |
| surface label | 10    | system mono  | "WHAT HAPPENED" eyebrow caps      |

### Spacing

`3 / 6 / 10 / 14 / 20 / 28`. Surface block padding is 20 / 14. Section
margins are 20 or 28.

## Component patterns

### Surface block

```
┌─────────────────────────────────────┐
│ ● WHAT HAPPENED                     │ ← label (color = confidence)
│                                     │
│ Every node returned roughly         │ ← body (17 px, plain English)
│ one minute of HTTP 503 errors       │
│ after rejoining the cluster…        │
│                                     │
│                                     │
│ scope · three nodes  · customer T-… │ ← smeta (mono, dim)
└─────────────────────────────────────┘
```

A surface block has exactly three parts: a colored mono eyebrow label
with a glowing dot, a 1–3 sentence prose answer, and a small bottom
smeta row with qualifiers. **No file paths, no chips, no expand handles.**
The reader gets one thing per block.

The grid template is `1fr 1.4fr 1fr` — the WHY column gets ~40% more
horizontal room because the mechanism explanation is the longest of the
three.

### Lens views

(Carried over from the previous iteration — slim underlined tabs above a
single shared canvas; click switches; the canvas head shows
`Exhibit · Title · subtitle`.)

### Side rail (selected)

(Carried over — 280 px wide, compact entity/event card with kind stripe,
chip row, description, and clickable source refs that smooth-scroll to
the matching evidence card.)

### Evidence card

(Carried over — citation header `EV·NN · src/foo.cpp:lines · [conf chip]`,
italic claim, code block.)

### Uncertainty band

(Carried over — amber-bordered always-visible block, never collapsed.)

## Layout — top to bottom

```
┌──────────────────────────────────────────────────────────────┐
│ CASE 4006 · cluster · build · topo · region · reporter · DATE│ ← 38 px
├──────────────────────────────────────────────────────────────┤
│ ┌──WHAT HAPPENED──┬──WHY IT HAPPENED────┬──FIX─────────────┐ │
│ │ plain English   │ plain English       │ plain English    │ │ ← Layer 1
│ │ no jargon       │ no jargon           │ no jargon        │ │   ~200 px
│ │ ●coral          │ ●amber              │ ●mint            │ │
│ └─────────────────┴─────────────────────┴──────────────────┘ │
│                                                              │
│ GO DEEPER · causal mechanism · second-by-second · wiring …   │ ← bridge
├──────────────────────────────────────────────────────────────┤
│ I Mechanism · II Minute · III Wiring     search   legend     │ ← lens tabs
├─────────────────────────────────────┬────────────────────────┤
│  canvas (active lens)               │  focused (selected)    │
│  Layer 2: the diagrams              │  280 px rail           │ ← Layer 2
└─────────────────────────────────────┴────────────────────────┘
┌─────────────────────────┬────────────────────────────────────┐
│ KEY POINTS (5)          │ EVIDENCE LEDGER (15)               │
│ UNCERTAINTY (3)         │ Layer 3: code + citations          │ ← Layer 3
└─────────────────────────┴────────────────────────────────────┘
```

## Lifting onto a new investigation

The system holds whether the topic is a database flap, a deploy regression,
or a billing anomaly. To port:

1. Swap the `<script id="data">` JSON. Schema is unchanged from `data.json`
   v1.0.
2. Update the **case strip** values (case id, cluster id, build, topo,
   region, reporter, date).
3. **Rewrite the three surface blocks in plain English.** This is the
   load-bearing change. A few rules:
   - WHAT: describe the symptom as the affected customer/user would.
     Don't use internal identifiers. One or two sentences.
   - WHY: explain the mechanism in conversational terms. Inline a few
     italicized key phrases (using `<em>`) where the eye should grab —
     these inherit the block's color so the reader sees the cause
     highlighted in amber.
   - FIX: the action the reader should take. Inline `<em><span class="mono">…</span></em>`
     for any literal config snippet (it picks up the mint color from the
     block).
4. Update each block's `smeta` row with scope / root / tracking refs.
5. The lens diagrams, evidence ledger, key points, and uncertainty band
   are all data-driven from `data.json`.

That's it. Everything else is reusable.

## Anti-goals respected

- **Plain English on the surface.** No `read_caught_up`, no
  `raft_server.cpp:917`, no `apply_lag > 1000` in Layer 1. Those live in
  Layer 2 and Layer 3 where the reader has chosen to look at them.
- **Complexity not hidden, just layered.** All 10 entities, all 12
  components, all 14 events, all 15 evidence items are still in the
  artifact. They just don't fight the WHAT/WHY/FIX surface for the
  reader's attention.
- **Uncertainty stays loud.** The "what we didn't measure" link is one
  of the five "go deeper" jump-targets. The amber band itself stays
  always-visible at the bottom of the page.

## Data contract — still stable

No required fields renamed or removed. The Layer 1 surface text is
*hand-written prose* per investigation — it's the editorial heart of each
report and resists being templated. If a future template generator needs
this auto-filled, the minimum addition would be an optional
`summary.surface` object on `data.json`:

```json
"summary": {
  "surface": {
    "what":  { "html": "…", "meta": "scope · three nodes …" },
    "why":   { "html": "…", "meta": "root · server-side …" },
    "fix":   { "html": "…", "meta": "tracked · #665 #729 …" }
  }
}
```

…rendered by a small loop in the script. Optional, additive, doesn't
break old artifacts.
