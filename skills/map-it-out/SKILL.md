---
name: map-it-out
description: >-
  Map out, end to end, how a piece of functionality actually works today —
  its entry points, execution flow, data flow, state changes, side effects,
  branches, and failure paths — grounded in the real code with file:line
  citations and a flow diagram. Read-only. Use when the user invokes
  /map-it-out <query>, asks to "map out", "trace", or "show me the flow of"
  something, or when an agent must understand a feature deeply and
  accurately before changing, debugging, or explaining it.
---

# Map It Out

Builds an accurate, verified map of how the functionality in `<query>` works right now, so the reader (a human or another agent) can reason about it without re-reading the code.

Invocation: `/map-it-out <query>` — the text after the command is what to map (a feature, flow, endpoint, job, bug path, or question such as "what happens when a user resets their password"). If no query is given, ask for one before doing anything else.

This skill is **read-only**. Do not create, edit, or delete files, and do not run commands with side effects (migrations, deploys, writes to shared services). Running existing tests or read-only commands to confirm behavior is fine.

## Step 1: Frame the query

Before searching, write down for yourself:

- **Subject** — the functionality being mapped, in one sentence.
- **Trigger(s)** — what starts it: an HTTP route, UI event, CLI command, cron/scheduled job, queue consumer, webhook, function call from another module.
- **Outcome** — what "done" looks like: a response, a persisted record, a rendered UI, a message sent.
- **Scope edges** — where the map stops (e.g. "up to the database write", "excluding the auth middleware"). Default: from the outermost trigger in this repo to the last observable effect in this repo.
- **Level** — a feature-level query ("how does checkout work") maps one flow: its entry points, the functions it passes through, its data stores, and the external systems it calls. A project-level query ("how does this service work") maps the major components and how they connect, and leaves out the internals of each.
- **Focus** — if the query names a specific concern (a change being considered, a bug, a decision point such as "where the price is calculated"), note it. The map must still cover the whole flow, but the focus areas get extra depth and are highlighted in the output.

If the query is ambiguous enough that two different maps are plausible (e.g. "how does sync work" in a repo with three sync systems), ask the user which one before going further. Otherwise state your interpretation and proceed.

## Step 2: Find every entry point

Search broadly before reading deeply. Missing an entry point is the most common way a map ends up wrong.

- Grep for the domain terms in the query **and** their variants: camelCase, snake_case, kebab-case, plurals, abbreviations, and the names used in routes, tables, events, and UI copy.
- Look at the places triggers are registered: route tables, controllers, CLI command registries, job/cron schedulers, queue and event subscribers, webhook handlers, UI event handlers, exported public APIs.
- Check whether more than one path reaches the same core logic (e.g. an API route and a background job both calling the same service). Each path belongs on the map.
- Read the project's docs, READMEs, and ADRs for orientation only — confirm every claim from them against the code.

## Step 3: Trace the flow

Follow the actual execution from each entry point to the outcome. Read implementations, not just signatures or names.

For each hop, capture:

- **Where** — `file_path:line` of the function or block.
- **What it does** — one line, in terms of behavior, not restating the function name.
- **Inputs and outputs** — the shape of data coming in and going out, and where it is transformed, validated, or defaulted.
- **State** — what it reads from and writes to: database tables, caches, in-memory stores, files, session, global/module state, client state.
- **Side effects** — external API calls, emitted events, enqueued jobs, emails, logs or metrics that something depends on.
- **Branches** — conditions that change the path: feature flags, config and env vars, permissions/roles, user or account type, input validation, early returns.
- **Failure paths** — what is thrown or returned on error, where it is caught, retries, fallbacks, and what the caller ultimately sees.

Resolve indirection instead of guessing across it. When the next hop is hidden behind any of the following, find the concrete target:

- dependency injection, service locators, factories, or registries
- interfaces or abstract classes with multiple implementations (identify which one runs, and when)
- middleware, decorators, interceptors, hooks, plugins, or lifecycle callbacks that run implicitly
- event emitters, pub/sub, queues, or message buses (find every subscriber, not just one)
- dynamic dispatch by string, map lookup, or reflection
- generated code, ORM hooks, database triggers, or framework conventions (file-based routing, magic method names)
- async boundaries: promises not awaited, background tasks, retries, scheduled follow-ups

Depth rules:

- Go as deep as the query needs. Stop at third-party libraries and generic utilities **unless** the behavior the query cares about depends on them — then describe the relevant library behavior. Confirm it from the library's source or current docs rather than memory, and say which you used (or that you could not confirm it).
- Do not stop at the first match that looks right. Keep going until the outcome from Step 1 is reached on every path.

For a large surface, you may delegate breadth searches (e.g. "find every subscriber to event X") to subagents, but read the critical path yourself. Do not trust a summary for the hops the map depends on most.

## Step 4: Verify the map

Treat the draft map as a hypothesis and try to break it.

- **Re-check each hop** — does the cited line actually do what the map says? Re-open any hop you described from memory or from a name alone.
- **Draft the diagram now and use it to find gaps** — if there is a node or edge you cannot explain from the code you read, go back to Step 3 and trace it before continuing.
- **Look for what you missed** — other callers of the core functions, other implementations of the interfaces, other subscribers to the events, other code that writes the same state.
- **Check for dead or shadowed code** — code that looks relevant but is unreachable, behind a flag that is off by default, deprecated, or overridden elsewhere. Say so on the map rather than silently dropping or including it.
- **Cross-check against tests** — tests show intended behavior and edge cases. Where tests and code disagree, the code is what runs; note the discrepancy.
- **Code wins over docs and comments** — when docs, comments, or names contradict the code, map the code's behavior and note the contradiction.
- **Confirm at runtime when it is cheap and safe** — e.g. run an existing relevant test. Never run anything with side effects to confirm a map.

Label every claim on the map as one of:

- **Verified** — read directly in the code (cite `file_path:line`).
- **Inferred** — reasoned from surrounding code, conventions, or config not fully traced; say what it is inferred from.
- **Unknown** — could not be determined from the repo (e.g. runtime config, external service behavior); say what would resolve it.

## Step 5: Present the map

Output the map in the conversation so it stays in context for whoever invoked the skill. Do not write it to a file unless the user asks.

Use this structure, dropping any section that would be empty:

1. **Summary** — 2–4 sentences: what the functionality does, what triggers it, and what it produces.
2. **Flow diagram** — Mermaid, in the form that fits the shape of what you mapped: `flowchart` for branching logic or how components connect, `sequenceDiagram` for request/response flows between several actors or systems, `stateDiagram` for lifecycles. Use a clean ASCII diagram instead if Mermaid won't render where the map is going.
   - Label nodes with the real functions, files, or components, and edges with what actually passes between them (a call, event, query, or payload).
   - Mark branches, async hops, and external systems.
   - Highlight the focus areas from Step 1, if any (e.g. with a `classDef` style).
   - Keep it readable: collapse trivial hops, and split it into several diagrams if one would exceed ~20 nodes.
3. **Step-by-step trace** — numbered hops in execution order, each with `file_path:line`, what it does, and the data passed on. One list per entry point when paths differ meaningfully.
4. **Data and state** — key types/schemas involved, and every piece of state read or written, by whom.
5. **Branches and configuration** — flags, env vars, config values, and conditions that change behavior, with their defaults.
6. **Side effects and external dependencies** — external calls, events, jobs, and what depends on them.
7. **Failure modes** — how each meaningful error is handled and what the caller or user ends up seeing.
8. **Gotchas** — non-obvious behavior, implicit coupling, ordering dependencies, invariants the code relies on, and docs/code contradictions.
9. **Open questions** — every **Inferred** or **Unknown** item that matters, and what would resolve it.

Write for a reader who has never seen this code: plain language, concrete names, no claims without a citation.

## Constraints

- **Read-only.** Mapping never changes the codebase or any shared system.
- **Ground everything.** Every file, function, and behavior on the map must come from the actual repo. Never invent a path, name, or line number.
- **Accuracy over completeness.** A smaller map that is correct beats a larger one with guesses. When something is uncertain, label it instead of smoothing it over.
- **Describe current behavior, not intended behavior.** Do not propose fixes or redesigns unless the user asks; note suspected bugs briefly under Gotchas.
- **Match the query's scope.** Map what was asked, to the depth it needs — not the whole system.
