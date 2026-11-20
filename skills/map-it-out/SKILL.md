---
name: map-it-out
description: >-
  Map out, end to end, how a piece of functionality actually works today —
  its entry points, execution flow, data flow, state changes, side effects,
  branches, and failure paths — grounded in the real code with file:line
  citations. The map is for the agent's own understanding and is not shown to
  the user. Use when the user invokes /map-it-out <query>, asks to "map out"
  or "trace" how something works, or when an agent must understand a feature
  deeply and accurately before changing, debugging, or explaining it.
---

# Map It Out

Builds an accurate, verified map of how the functionality in `<query>` works right now, so you can reason about it correctly in the work that follows. The map is for your own understanding: never display it to the user or write it to a file.

Invocation: `/map-it-out <query>` — the text after the command is what to map (a feature, flow, endpoint, job, bug path, or question such as "what happens when a user resets their password"). If no query is given, ask for one before doing anything else.

## Step 1: Frame the query

Before searching, write down for yourself:

- **Subject** — the functionality being mapped, in one sentence.
- **Trigger(s)** — what starts it: an HTTP route, UI event, CLI command, cron/scheduled job, queue consumer, webhook, function call from another module.
- **Outcome** — what "done" looks like: a response, a persisted record, a rendered UI, a message sent.
- **Scope edges** — where the map stops (e.g. "up to the database write", "excluding the auth middleware"). Default: from the outermost trigger in this repo to the last observable effect in this repo.
- **Level** — a feature-level query ("how does checkout work") maps one flow: its entry points, the functions it passes through, its data stores, and the external systems it calls. A project-level query ("how does this service work") maps the major components and how they connect, and leaves out the internals of each.
- **Focus** — if the query names a specific concern (a change being considered, a bug, a decision point such as "where the price is calculated"), note it. The map must still cover the whole flow, but the focus areas get extra depth.

If the query is ambiguous enough that two different maps are plausible (e.g. "how does sync work" in a repo with three sync systems), ask the user which one before going further. Otherwise proceed with your interpretation.

## Step 2: Find every entry point

Search broadly before reading deeply. Missing an entry point is the most common way a map ends up wrong.

- Grep for the domain terms in the query **and** their variants: camelCase, snake_case, kebab-case, plurals, abbreviations, and the names used in routes, tables, events, and UI copy.
- Look at the places triggers are registered: route tables, controllers, CLI command registries, job/cron schedulers, queue and event subscribers, webhook handlers, UI event handlers, exported public APIs.
- Check whether more than one path reaches the same core logic (e.g. an API route and a background job both calling the same service). Each path belongs on the map.
- Read the project's docs, READMEs, and ADRs for orientation only — confirm every claim from them against the code.

## Step 3: Trace the flow

Follow the actual execution from each entry point to the outcome. Read implementations, not just signatures or names.

Break the flow into steps: each function or block of code it passes through, in the order they run. For each step, capture:

- **Where** — `file_path:line` of the function or block.
- **What it does** — in terms of behavior, not restating the function name.
- **Inputs and outputs** — the shape of data coming in and going out, and where it is transformed, validated, or defaulted.
- **State** — what it reads from and writes to: database tables, caches, in-memory stores, files, session, global/module state, client state.
- **Side effects** — external API calls, emitted events, enqueued jobs, emails, logs or metrics that something depends on.
- **Branches** — conditions that change the path: feature flags, config and env vars, permissions/roles, user or account type, input validation, early returns.
- **Failure paths** — what is thrown or returned on error, where it is caught, retries, fallbacks, and what the caller ultimately sees.

When the code that runs next is hidden behind any of the following, find the code that actually runs instead of guessing:

- dependency injection, service locators, factories, or registries
- interfaces or abstract classes with multiple implementations (identify which one runs, and when)
- middleware, decorators, interceptors, hooks, plugins, or lifecycle callbacks that run implicitly
- event emitters, pub/sub, queues, or message buses (find every subscriber, not just one)
- dynamic dispatch by string, map lookup, or reflection
- generated code, ORM hooks, database triggers, or framework conventions (file-based routing, magic method names)
- async boundaries: promises not awaited, background tasks, retries, scheduled follow-ups

Depth rules:

- Go as deep as the query needs. Stop at third-party libraries and generic utilities **unless** the behavior the query cares about depends on them. In that case, confirm the library's behavior from its source or current docs rather than memory.
- Do not stop at the first match that looks right. Keep going until the outcome from Step 1 is reached on every path.

For a large surface, you may delegate breadth searches (e.g. "find every subscriber to event X") to subagents, but read the critical path yourself. Do not trust a summary for the steps the map depends on most.

## Step 4: Verify the map

Treat the draft map as a hypothesis and try to break it.

- **Re-check each step** — does the cited line actually do what the map says? Re-open any step you described from memory or from a name alone.
- **Sketch the flow as a diagram for yourself and use it to find gaps** — if there is a connection you cannot explain from the code you read, go back to Step 3 and trace it before continuing.
- **Look for what you missed** — other callers of the core functions, other implementations of the interfaces, other subscribers to the events, other code that writes the same state.
- **Check for dead or shadowed code** — code that looks relevant but is unreachable, behind a flag that is off by default, deprecated, or overridden elsewhere. Note it on the map rather than silently dropping or including it.
- **Code wins over docs and comments** — when docs, comments, or names contradict the code, map the code's behavior and note the contradiction.

Label every claim on the map as one of:

- **Verified** — read directly in the code, at a known `file_path:line`.
- **Inferred** — reasoned from surrounding code, conventions, or config not fully traced; know what it is inferred from.
- **Unknown** — could not be determined from the repo (e.g. runtime config, external service behavior); know what would resolve it.

## Step 5: Confirm the map is complete

The map is complete when you can answer each of the following from code you have read, with a `file_path:line` behind each claim. If any can't be answered, go back to Step 3.

1. What the functionality does, what triggers it, and what it produces.
2. Every step in the order the code runs, for each entry point, and the data passed between steps.
3. The key types and schemas involved, and every piece of state read or written, and by which step.
4. The flags, env vars, config values, and conditions that change behavior, and their defaults.
5. The external calls, events, and jobs, and what depends on them.
6. How each meaningful error is handled, and what the caller or user ends up seeing.
7. Non-obvious behavior: implicit coupling, ordering dependencies, invariants the code relies on, docs/code contradictions, and suspected bugs.
8. Which claims are Inferred or Unknown, and what would resolve them.

Do not output the map. Tell the user in one or two sentences that the mapping is done, naming any Unknown that matters to the task at hand. Then continue with the task the map was for, or wait for the user's next request.

## Constraints

- **Keep the map internal.** It exists so you understand the functionality; it is never displayed to the user or written to a file.
- **Ground everything.** Every file, function, and behavior on the map must come from the actual repo. Never invent a path, name, or line number.
- **Accuracy over completeness.** A smaller map that is correct beats a larger one with guesses. When something is uncertain, label it instead of smoothing it over.
- **Describe current behavior, not intended behavior.** Map what the code does today, including suspected bugs, without redesigning it.
- **Match the query's scope.** Map what was asked, to the depth it needs — not the whole system.
