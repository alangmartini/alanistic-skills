---
name: improve-skill
description: Runs a retrospective on a finished session to find concrete speed and accuracy improvements for the skills and MCP tools that were exercised. Walks the transcript, attributes each gap to a fixable artifact (a SKILL.md step, a step ordering, a missing agent fan-out, or a slow or missing MCP tool), and proposes evidence-backed edits. Use when a skill or workflow run just finished (for example a long investigation, build, or review) and you want the next run to be faster or more accurate, when the user says "improve this skill", "what could be faster", "retro this run", or after any session that felt slow, serial, or that skipped a cross-check.
---

# Improve Skill

## Overview

Every skill run leaves evidence of how it could be faster or more accurate: independent calls that ran one after another, a source-of-truth that was never cross-checked, an MCP call that returned a huge payload you then filtered by hand, a hypothesis locked in before all signals were read. This skill turns a finished session into a short list of concrete, evidence-backed edits to the skills and MCP tools that were used, so the next run improves instead of repeating the same cost.

The output is not vague advice. It is a ranked set of changes, each tied to a real artifact (a `SKILL.md` step or an MCP tool) and justified by something that actually happened in the session under review.

## When to Use

- A long or multi-step skill or workflow just finished (an investigation, a build, a review, a research run) and you want to capture what to change before the lesson is lost.
- A run felt slow, serial, repetitive, or relied on a manual workaround.
- The user asks to "improve this skill", "make this faster next time", "retro this", or "what did we miss".
- Periodically, to audit a skill you run often against how it actually behaves in practice.

Do NOT use this:

- To grade the outcome of the task itself (was the bug fixed, was the answer right). That is the job of the skill that ran. This skill grades the *process*.
- To rewrite a skill from scratch. Edits here are small and scoped. A redesign is a separate task.
- On a trivial one-step run with nothing to attribute.

## What to Hunt For

Run two passes over the session. Do not stop after the first finding.

### Speed pass

| Observable signal in the session | Lever |
|---|---|
| Independent calls or subtasks ran sequentially | Fan them out: parallel tool calls in one turn, or one subagent per independent unit |
| One MCP call returned a large payload and you filtered or summarized it yourself | Push the filter, limit, or aggregation server-side into the tool |
| The same data was fetched more than once | Capture the result once and pass it forward |
| A call was retried, polled, or looped before it succeeded | Add a precondition check or a narrower query so the first call lands |
| A long serial chain where each step waited on the previous one without needing to | Reorder so independent steps start early |
| Large reference material loaded that was never used | Tighten what the skill pulls into context (see `context-engineering`) |

### Accuracy pass

| Observable signal in the session | Lever |
|---|---|
| A claim was stated without checking the source of truth (the source repo, the spec, the schema) | Add a cross-check step against that source |
| The run stopped at the first plausible cause or answer | Add a gate: read all relevant signal sources before concluding |
| A signal source that exists was never queried | Add it to the skill's checklist of sources |
| A workaround reached around the available tools (manual steps, a browser, copy-paste) | That is a missing tool, not a step. File the capability gap |
| A result was used without being verified or reproduced | Add a verification or reproduction step |

## Core Process

1. **Scope the retrospective.** Identify the session to analyze (usually the current one, already in your context) and which skill(s) and MCP tools it exercised. If analyzing a past run, locate its saved transcript before continuing. Name the skill(s) and tools in scope so findings can be attributed.

2. **Reconstruct the action ledger.** Walk the transcript in order and list each significant action: tool call, MCP call, subagent spawn, and skill step. For each, record an *observable* signal, not a guess: payload size returned, number of retries, whether it blocked the next step, whether it duplicated an earlier call, whether independent work ran serially. This ledger is the evidence base. Findings that do not trace back to a ledger entry are not allowed.

3. **Diagnose gaps.** Apply the speed pass and the accuracy pass above to the ledger. Both passes are mandatory: a retrospective that only found speed wins (or only accuracy wins) did not finish.

4. **Attribute each gap to a fixable artifact.** A gap is only actionable once it points at something you can change. Use this decision table:

   | Gap | Target | Kind of edit |
   |---|---|---|
   | Independent calls ran serially | the skill | Add a step naming what is independent and telling the agent to fan out |
   | A cross-check everyone forgets (source repo, schema) was skipped | the skill | Add the step to the process and a matching red flag |
   | Stopped at first hypothesis | the skill | Add a gate to read all signal sources before concluding |
   | An MCP call returned too much and you post-filtered | the MCP tool | Add a server-side filter, limit, or summary parameter |
   | The tool you needed did not exist (you worked around it) | a new MCP tool | File the capability gap; do not encode the workaround |
   | A call was flaky or repeated | the skill or the tool | Add a precondition, or pass the result forward instead of refetching |
   | A genuine one-off slip with no recurring pattern | nothing | Do not encode it |

   Then locate the real file. For a skill, find its `SKILL.md` (glob for the skill name under a `skills/` directory). For an MCP tool, map the tool-name prefix to its server and source repo. A finding with no located artifact stays a finding, not an edit.

5. **Propose prioritized, evidence-backed changes.** For each finding write: the gap, the evidence from this session, the target artifact (file path or tool name), and the exact fix (the lines to add to the `SKILL.md`, or the parameter to add to the tool). Rank by recurrence times impact: a gap that recurs every run and wastes work or risks correctness is high; a rare or low-cost gap is low.

6. **Apply or hand off.** With approval, apply the `SKILL.md` edits as small scoped additions and re-run the skill repo's validator if there is one. For changes that need tool or server code, write them up as a task or issue rather than editing blindly. Keep the operator in the loop before touching anything outside the skill files.

## Locating the Artifacts

- **Skills.** Each skill is a `SKILL.md` inside a `skills/` directory. For marketplace plugins these live under the marketplace clone or plugin cache. Glob for `**/skills/<name>/SKILL.md`. The directory name matches the skill `name`.
- **MCP tools.** The tool-name prefix identifies the server (for example `mcp__<server>__<tool>`). The server is declared in the harness config (the MCP settings or plugin manifest) and is backed by a source repo. Edit the tool there, or file a gap if the capability is missing.
- **Forked or vendored skills.** Some runtimes run a private copy of a skill rather than the marketplace one. If the project documents a fork, edit the copy the run actually used, not just the upstream source.

## Output Template

```
## Retrospective: <skill or workflow> run

### Action ledger (evidence)
- <call / step> -> <observable signal: payload size, retries, serial dependency, duplicate>

### Findings
1. [SPEED|ACCURACY] <gap in one line>
   Evidence:  <what in the ledger shows it>
   Target:    <file path, MCP tool name, or "new tool to file">
   Fix:       <exact lines to add / parameter to add / diff>
   Priority:  <high|med|low> (<recurrence x impact>)

### Proposed edits
<diffs or precise add-this-here instructions>

### Capability gaps to file (no edit yet)
- <missing or slow MCP tool> : <what to build, why the workaround is not the fix>
```

## Common Rationalizations

| Rationalization | Reality |
|---|---|
| "The run succeeded, there is nothing to improve." | Success hides cost. A correct answer reached through a long serial chain still has a speed lever. Read the ledger before concluding nothing. |
| "Add more rules to the skill to be safe." | An edit that would not have changed this session's behavior is noise that dilutes the skill. Only encode load-bearing changes. |
| "The MCP call was just slow, nothing to do." | A slow tool is a gap to fix or file, not a dead end. Narrow the query, ask for a server-side summary, or propose the missing capability. |
| "Fan out everything to go faster." | Parallelize only genuinely independent work. Name the dependency you would break before splitting a chain. |
| "It took about N minutes." | Do not invent durations. Cite observable evidence: payload size, retry count, length of the serial chain, repeated calls. |
| "This one mistake should become a permanent rule." | One-off slips are not patterns. Encode a rule only when the gap will recur on the next run. |
| "I will just script around the missing tool in the skill." | A workaround baked into a skill hides the real gap. File the missing tool so every skill benefits. |

## Red Flags

- A recommendation with no evidence quoted from the analyzed session.
- "Be faster" or "be more thorough" with no specific edit to a specific file.
- Durations or percentages that were never measured.
- Editing MCP server code to add a capability you did not confirm was missing.
- A rewrite that changes a skill's intent instead of a small scoped addition.
- A finding that names a problem but no fixable artifact.
- Only one pass run (speed or accuracy, not both).

## Verification

After completing the retrospective, confirm:

- [ ] Every finding cites concrete evidence from the analyzed session's ledger.
- [ ] Every finding names a target artifact (skill file path, MCP tool, or "new tool to file").
- [ ] Both passes were run: speed and accuracy.
- [ ] Findings are prioritized by recurrence times impact.
- [ ] No fabricated timings or percentages.
- [ ] Applied `SKILL.md` edits keep frontmatter valid; the skill repo's validator passes if one exists.
- [ ] Capability gaps that need tool or server code are filed, not hacked around inside a skill.
