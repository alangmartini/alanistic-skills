---
name: html-output
description: >-
  Generates self-contained HTML artifacts (explainer pages, slide decks, interactive diagrams and charts, work-story recaps) to present information visually instead of plain text or markdown. Use when the user explicitly asks for HTML output, a visual page, a slideshow, an explainer, a diagram, or a "show me" artifact. Also proactively offer this skill when a response would land better as a visual artifact: dense multi-part explanations, architecture or data-flow walkthroughs, teaching a concept, onboarding or reference docs, or recapping the work done in a task. Produces one portable .html file that opens in any browser with no build step. Not for production application UIs (use frontend-ui-engineering) and not when the user just wants a quick plain-text answer.
---

# HTML Output

## Overview

HTML is almost as cheap for an agent to generate as markdown: both are just text the model types out. But HTML is far richer to *consume*. It carries layout, color, spatial relationships, hierarchy, motion, and interactivity, where markdown gives you headings, bold, and tables.

The bottleneck in agent-to-human communication is the human's reading bandwidth, not the agent's writing speed, and vision is the widest channel into the brain. When content has real structure (relationships, sequences, comparisons, before-and-after states), an HTML artifact transfers it faster and makes it stick longer than a wall of prose.

There is a deeper payoff: a good HTML artifact keeps the human *in the loop*. Long markdown plans go unread, and the agent ends up making calls nobody saw. A page someone actually opens and reads is a page whose decisions get checked.

This skill turns an explanation, a lesson, a diagram, or a task recap into a single portable HTML file. It is a presentation layer over true content, not a new default response mode.

## When to Use

Use it when the user explicitly asks for an HTML page, a visual version, a slideshow or deck, an explainer, a diagram or chart, or a "show me / make it visual" artifact.

Proactively *offer* it (one line, build only on yes) when a response would clearly land better as a visual artifact:

- A dense, multi-part explanation that would otherwise be a long markdown dump
- Teaching or onboarding material a junior reader needs to navigate
- An architecture, data-flow, or state-machine walkthrough
- A recap of the work done in a task, to share with a teammate

Skip it when the user wants a quick plain-text answer, when the content fits in a few sentences, when there is no browser to open it in, or when the job is a production application UI (use the `frontend-ui-engineering` skill).

This skill never changes the default output mode. Offer, do not impose.

### What it costs

HTML is not free. It takes roughly 2 to 4 times longer to generate than the equivalent markdown, uses more tokens, and diffs badly in version control. That is the case for restraint: reach for an artifact when the visual genuinely earns those costs, and regenerate it rather than hand-diffing it. The payoff on the other side is sharing: one self-contained file is a link you can send, not an attachment nobody renders.

## Start with the job, not the file

The most common failure is opening a `<style>` tag before knowing what the artifact is for. The trick of this whole technique is not the HTML, it is knowing what you want the artifact to *do* and how it will be *used*. Answer two questions first:

1. **What should the reader walk away with?** A concept understood, a decision reviewable, a flow they can trace, a sense of what changed and why.
2. **How will they use it?** Read once and discard, return to as reference, present from live, share as a link, click through to explore.

The answers pick the format and set the depth. "Present from live" means a slide deck with big type. "Return to as reference" means a scrollable explainer with a table of contents. "Trace a flow" means an interactive diagram. Get this right and the rest is mostly craft.

Then **gather the real content before writing any HTML.** Real file names, real numbers, real code, the real decisions and their rationale. If you are recapping a task, the content is in the conversation and the diff. A beautiful empty template is worse than three honest sentences of plain text: the HTML is a presentation layer over true facts, and if the facts are not ready, the artifact is not ready.

## The four formats

| Format | Reach for it when the reader needs to... | Shape |
|---|---|---|
| **Explainer / doc page** | understand a concept or how something works, and come back to it | Scrollable page, anchored sections, a table of contents on long pages, diagrams inline next to the prose they explain |
| **Slide deck** | follow a narrative you present or they click through | Full-screen slides, keyboard navigation, a slide counter, one focal point per slide, big readable type |
| **Interactive diagram / chart** | see relationships, structure, or data and explore them | Inline SVG diagram or a real chart, interactivity that reveals detail (hover, click, step through) |
| **Work-story recap** | grasp what was done in a task and why | A narrative: the problem, what changed, the result, with a timeline, files touched, before/after, and the reasoning behind non-obvious calls |

One artifact can combine these (a recap with an embedded diagram, an explainer with a small chart). Pick the dominant shape and nest the rest.

## Craft

### One self-contained file

Default to zero dependencies. Inline all CSS in a `<style>` tag, inline all JS in a `<script>` tag, hand-roll diagrams as inline SVG. The file must open by double-click with no build step, no dev server, no `npm install`.

```html
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Descriptive, specific title</title>
  <style>/* design tokens, layout, components: all inline */</style>
</head>
<body>
  <!-- real content, semantic HTML -->
  <script>/* behavior, all inline */</script>
</body>
</html>
```

Reach for a CDN library only when the visual genuinely needs it: a real data chart (Chart.js), a graph that is painful to hand-draw (Mermaid), a heavy visualization (D3). When you do, add a comment at the top of the file naming each external dependency and the one-line reason. Never pull in a framework or a utility-CSS library to do what a few rules of hand-written CSS already do.

### Show, do not tell

The artifact exists to move understanding through the eye, which is faster than moving it through prose. So when you have written a paragraph, look at what it is doing: if it describes a flow, a comparison, a before-and-after, a sequence, a hierarchy, or a quantity, that paragraph wants to be a picture. A relationship lands in one glance as a diagram and takes a slow read as a sentence.

Markdown gives you headings, bold, and tables; HTML gives you the whole range, and using it is the point. Tables for anything tabular, inline SVG for flows and structures and illustrations, a chart for data, `<script>` for interaction, absolute positioning or canvas for spatial layouts. Reach for these by default, not as a garnish on top of the prose. For a set of numbers, sorting by magnitude and aligning the values makes the distribution scannable on its own, often without a full chart. If you catch yourself drawing an ASCII diagram or approximating color or layout with text, you have the wrong element.

Prose then does only what prose can: a sharp framing line, the reasoning behind a non-obvious call, a caveat, a caption. Keep it tight. A wall of text inside an HTML file is just the markdown dump this skill exists to replace, with nicer fonts.

### Communicate, do not decorate

The visual hierarchy must map to the information hierarchy. Size, weight, color, and whitespace are how you say "this matters more than that," and that only works if you actually decide what matters: pick the two or three things on a view that carry the most weight and let them stand out against a plain, quiet ground. Emphasis is a budget. If every block is a card, "card" stops meaning anything. If every heading wears a tiny uppercase letter-spaced tag, the tags are noise. If every section gets its own accent color, the color says nothing. Spend emphasis on the few things that earn it and leave the rest plain.

Motion and interactivity follow the same rule: they must reveal information. Hover for detail, click to expand, step through a sequence. For an interactive diagram, that can extend to a "copy as prompt" button so the reader's changes flow back to you. Interactivity that only performs is noise.

### Avoid the AI aesthetic

Generated HTML has a recognizable, unwanted look: gradient hero banners, emoji used as icons, everything boxed in a rounded card, a different accent color on every block, a stack of tiny uppercase labels. It helps to understand *why* the model drifts there. It is usually decoration standing in for substance: when the real content is thin, or the model has not decided what matters, it dresses the page up to make it feel more substantial than it is. The costume does not work. A modest amount of content presented plainly reads as confident; the same content wrapped in five cards, seven badges, and a rainbow of callout boxes reads as filler.

So the fix is not a checklist of banned effects, it is restraint proportional to substance. Match the amount of visual structure to the amount of real information. Three honest paragraphs and one small table do not need a hero, a sidebar, and a card grid; let the content set the scale. Reach for a card, a colored callout, or a labelled badge only when that specific element is doing a job a plain paragraph could not.

When you do need structure, the shadcn/ui design language is a good restrained default: a small set of CSS-variable tokens (`--background`, `--foreground`, `--muted`, `--muted-foreground`, `--border`, `--primary`), hairline 1px borders instead of heavy shadows, one radius reused everywhere, a clean sans-serif like Inter, and a muted-versus-foreground split that carries most of the hierarchy with almost no color. Define those tokens in `:root` with a `prefers-color-scheme: dark` block so the artifact gets a working dark mode for free. To match a specific company style instead, point Claude at that codebase once to generate a design-system HTML file, then pass it as a reference. For deeper visual-polish guidance, follow the `frontend-ui-engineering` skill.

### Slide decks need a navigation engine

A minimal keyboard-driven engine is enough:

```html
<style>
  .slide { display: none; min-height: 100vh; }
  .slide.active { display: flex; }
</style>
<script>
  const slides = document.querySelectorAll('.slide');
  const counter = document.getElementById('counter');
  let i = 0;
  const show = n => {
    i = Math.max(0, Math.min(slides.length - 1, n));
    slides.forEach((s, k) => s.classList.toggle('active', k === i));
    counter.textContent = `${i + 1} / ${slides.length}`;
  };
  addEventListener('keydown', e => {
    if (e.key === 'ArrowRight' || e.key === ' ') show(i + 1);
    if (e.key === 'ArrowLeft') show(i - 1);
  });
  show(0);
</script>
```

### Accessibility

Use semantic HTML (`<nav>`, `<section>`, `<h1>`..`<h3>`, `<figure>`). Give meaningful images and SVGs an accessible label. Keep text contrast readable, make interactive elements keyboard-reachable, and set the viewport meta tag. For a fuller pass, use `references/accessibility-checklist.md`.

### Deliver it

Save the file in the working directory (or where the user asked) with a descriptive kebab-case name, for example `auth-jwt-refactor-recap.html`. Report the path, give a one-line summary of what is inside, and open it in the browser for the user (or offer to). Do not paste the full HTML into the chat: the file is the deliverable.

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "Markdown is faster, I'll just write it out." | Faster for you to write, slower for the human to absorb when the content has structure. Their reading time is the bottleneck this skill exists to fix. |
| "I'll build the polished template now and fill in the content later." | A beautiful empty shell is worse than plain text. Gather the real content first; the HTML is a presentation layer over true facts. |
| "I'll pull in Tailwind and a few libraries to make it nicer." | Every dependency can fail to load and breaks portability. Hand-written CSS and inline SVG cover most needs; add a CDN library only when the visual truly requires it. |
| "HTML is great, I'll render everything this way now." | It does not change the default output mode, and it costs 2-4x the generation time. Offer it when the visual earns that cost; do not impose it on quick answers. |
| "I'll commit the .html into the repo like any doc." | HTML diffs are noisy and hard to review. Treat artifacts as regenerable outputs, not source; commit one only when it is a real, lasting deliverable. |
| "I'll just produce the file and move on." | Report the path, summarize it in one line, and open it or offer to. An artifact nobody is told how to open is a dead file. |

## Red Flags

- Placeholder or lorem text, or invented file names, numbers, or quotes
- It needs a build step, a dev server, or `npm install` to view
- A wall of prose where a diagram, table, or chart would carry the same idea in one glance
- Generic AI aesthetic: decoration filling in for thin content. Everything boxed in a card, every label a tiny uppercase tag, every block its own accent color
- External dependencies pulled in for something inline SVG and CSS could do
- Animation or interactivity that reveals no information
- An HTML file generated for a one-paragraph answer, or produced without offering when plain text was wanted
- The visual hierarchy does not match the information hierarchy: everything looks equally important

## Verification

- [ ] A single `.html` file that opens by double-click in any browser, no build step
- [ ] Renders with no console errors
- [ ] All content is real: actual names, numbers, code, and decisions, zero placeholder text
- [ ] Zero external dependencies, or each CDN library is named in a top-of-file comment with a reason
- [ ] Flows, comparisons, sequences, and quantities are shown as diagrams, tables, or charts rather than described in prose; remaining text is tight
- [ ] Visual hierarchy maps to information hierarchy; each view has one clear focal point
- [ ] Semantic HTML, readable contrast, viewport meta tag set, interactive parts keyboard-reachable
- [ ] You reported the path, summarized it in one line, and opened it or offered to
