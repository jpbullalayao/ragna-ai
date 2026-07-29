---
name: html-walkthrough
description: >-
  Study a topic from the current project (code, logic, docs, or other provided
  material) and publish a Claude Artifact — a self-contained HTML page — that
  walks the user through it. The walkthrough is concise, visual (flow charts,
  diagrams, listicles, tables), and written so someone unfamiliar with the
  topic deeply understands it. Use when the user invokes
  /html-walkthrough <topic>, or asks to "walk me through", "teach me about",
  or "explain X as a visual walkthrough".
---

# HTML Walkthrough

Produces a Claude Artifact that teaches the user the topic they asked about, grounded in the actual project.

Invocation: `/html-walkthrough <topic>` — the text after `/html-walkthrough` is the topic. If no topic is given, ask for one before doing anything else.

## Workflow

### Step 1: Parse the topic

Identify the subject and its likely scope: a feature flow, a module, an architecture question, a concept, etc. Note any user overrides (audience, depth, format preferences) — the query is authoritative over the defaults below.

### Step 2: Study the source material

Research the topic in the project before writing anything. Never invent behavior.

- Search the codebase for the relevant code, config, and docs (grep/glob for topic keywords, entry points, related types and routes).
- Read the key files end-to-end enough to trace the actual flow: triggers, inputs, decision points, side effects, outputs, and failure paths.
- Cap reads to the files genuinely needed to explain the topic accurately (typically 3–8).
- If the topic isn't found in the project, say so and confirm with the user whether to proceed as a general/conceptual walkthrough instead.

### Step 3: Plan the walkthrough

Before writing HTML, distill the research into a teaching outline:

- One-sentence answer to "what is this and why does it exist."
- The 3–7 steps or concepts a newcomer must grasp, in learning order (not code order).
- For each, the best format: flow chart for branching logic, sequence/step list for linear flows, table for comparisons or field references, short prose for the "why."
- What to cut — implementation trivia that doesn't change understanding stays out.

### Step 4: Build the Artifact

Load the `artifact-design` skill first, then write the HTML file to the scratchpad directory and publish it with the Artifact tool.

Content requirements:

- **Concise.** As short as possible without dropping necessary detail. Every section must earn its place; no filler intros or summaries that restate sections.
- **Client-readable.** A reader unfamiliar with the codebase or domain must be able to follow it. Define jargon on first use; prefer plain language over internal names, but cite real file paths / function names where they anchor the explanation.
- **Visual-first.** Use diagrams (mermaid via `<pre class="mermaid">`), numbered step lists, callout boxes, and tables wherever they explain faster than prose. Flow charts for anything with branches; step lists for linear sequences.
- **Grounded.** Every claim comes from the code or material studied in Step 2. Cite the source file for load-bearing claims.
- **Structured.** Lead with the one-sentence summary, then the big-picture diagram or overview, then the steps/details, ending with gotchas or edge cases only if they matter to the reader.
- Self-contained page (inline CSS, no external resources), responsive, theme-aware — per the Artifact tool's requirements.

Give the artifact a clear `<title>`, a one-sentence `description`, and a stable topic-appropriate `favicon`.

### Step 5: Report

Return the Artifact link with a one-line description of what the walkthrough covers and which sources it was built from.

## Constraints

- Brevity beats completeness of trivia: include every detail needed to understand the topic, and nothing else.
- Never fabricate flows or behavior — if something couldn't be verified in the source, either verify it or omit it (or explicitly mark it as unverified).
- User query overrides all defaults (depth, audience, format, scope).
