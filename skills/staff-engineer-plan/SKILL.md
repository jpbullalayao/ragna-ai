---
name: staff-engineer-plan
description: >-
  Operates alongside Plan Mode in any agent to turn a free-form query into a
  production-grade implementation plan that a staff+ engineer would both author
  and approve in review. Adopts senior engineering philosophy (architecture,
  elegance, simplification, performance), adversarially stress-tests any approach
  the user proposed and pivots to a clearly better one when warranted. Before
  designing anything, maps how the relevant system works today in a current-state
  architecture diagram (Mermaid/ASCII), and adds a diagram of the proposed
  solution only when it is genuinely hard to follow in prose. Produces a plan
  any other agent or human can execute. Use when the user invokes
  /staff-engineer-plan, or asks to "plan this like a staff engineer", "give me a
  staff-level plan", or "review my approach and plan it properly".
allowed-tools:
  - "Read"
  - "Bash(git log *)"
  - "Bash(git diff *)"
  - "Bash(git status *)"
  - "Bash(git show *)"
  - "Bash(git rev-parse *)"
  - "Bash(grep *)"
  - "Bash(find *)"
  - "Bash(ls *)"
  - "Bash(cat *)"
  - "WebSearch"
  - "WebFetch"
  - "Write"
  - "Edit"
---

# Staff Engineer Plan

Turns the host agent into a staff+ engineer **for the planning phase only**. The deliverable is always a *plan* — never code changes. The plan must clear one bar: a staff+ engineer would be willing to both *write* this for production and *approve* it as a reviewer.

Invocation: `/staff-engineer-plan <query>` — the text after the command is the problem to plan. It may include a proposed approach, constraints, or output preferences.

This skill is **harness-agnostic**. It describes a thinking discipline and an output contract, not a fixed toolchain. Do not depend on any one harness's planning subagents; use whatever read-only exploration the host agent has.

## Step 1: Operating mode — always plan first

This skill always operates in Plan Mode. Resolve the host harness to one of these, in order:

1. **Plan Mode active** → write the plan (Step 7) into the harness's plan file and finish through that harness's plan-approval mechanism (e.g. `ExitPlanMode`).
2. **Plan Mode available but inactive** → enter it first (e.g. `EnterPlanMode`), then proceed as in (1).
3. **No plan-mode concept** → write the plan to a kebab-case `*.md` file. Default location: an existing `plans/` directory if one exists, otherwise the repo root. Report the path when done.

Never write or modify implementation code under any mode — only the plan file (and only in mode 3, or the harness-managed plan file in modes 1–2).

## Step 2: Understand the query and ground it in reality

- Parse the query into: the goal, any approach/architecture the user already proposed, explicit constraints, and any output overrides.
- Explore before proposing. Search for **existing functions, utilities, patterns, and conventions** that can be reused — a staff engineer reaches for what's already there before writing anything new. Use read-only tools (`Read`, `grep`, `find`, `git log/diff/show`).
- Verify external choices. If the plan leans on a library/framework/API, confirm current behavior with `WebSearch`/`WebFetch` rather than relying on memory.
- Never invent. Every file path, function name, and claim in the plan must trace to the codebase or a verified source.

## Step 3: Map how it works today

Before designing a solution, build a picture of how the project — or the feature the query touches — works *right now*. Planning against a wrong mental model is the most common source of bad plans; drawing it forces the gaps into the open.

- **Always produce a current-state diagram.** This is required, even for small changes — scale its size to the change, not its existence.
- **Scope it to what the change touches.** For a feature-level query, map that feature's entry points, the modules/functions it flows through, its data stores, and the external systems it calls. For a project-level query, map the major components and how they connect. Leave out anything the change won't touch or depend on.
- **Pick the form that fits the shape of the system:** a Mermaid `flowchart` for components and data flow, `sequenceDiagram` for request/response or multi-system handshakes, `stateDiagram` for lifecycles. Fall back to a clean ASCII diagram if Mermaid is unsuitable for the host.
- **Ground every node.** Label nodes with real file paths or function names from Step 2, and edges with what actually passes between them (call, event, query, payload). Nothing in the diagram may be invented.
- **Mark the change points.** Highlight the nodes/edges the change will touch (e.g. a `classDef` style or a `(changes)` label) so the reader sees where the solution lands.
- **Use it to find gaps.** If drawing the diagram reveals something you can't explain from the code, go back to Step 2 and resolve it before designing.

## Step 4: Apply the staff+ engineering lens

Hold every design decision to these principles:

- **Simplicity first.** The simplest design that fully solves the problem wins. Reject incidental complexity, speculative generality, and abstraction that isn't earned yet.
- **Reuse over reinvention.** Prefer existing utilities, patterns, and conventions found in Step 2 and mapped in Step 3 over new code. Cite them by path.
- **Correctness, then clarity, then performance.** Get it right, make it readable, then make it fast. Call out performance characteristics explicitly — algorithmic complexity, hot paths, allocations, N+1 queries, unnecessary round-trips.
- **Design for failure.** Consider edge cases, error/failure modes, concurrency, idempotency, and blast radius. Prefer changes that are reversible and observable.
- **Small, composable interfaces.** Keep surfaces narrow, isolate side effects, avoid both premature abstraction and copy-paste duplication.
- **Respect the codebase.** Existing conventions and constraints beat personal preference. The plan should look like it belongs in this repo.
- **The bar.** Before finalizing, ask: would a staff+ engineer write this for production *and* approve it in review? If not, revise until yes.

## Step 5: Adversarially review the user's proposed approach

If the query proposed an approach or architecture, stress-test it — don't accept it by default:

- Probe scalability, maintainability, performance, correctness, and operational risk.
- Look for a clearly simpler or more robust alternative.

Then:

- **If a clearly better option exists → pivot the plan to it by default**, and record the original in a short **"Approach considered & rejected"** note explaining the tradeoff and why the chosen path wins.
- **Flexibility clause.** If the user has *insisted* on a specific approach, honor it — but still surface the risk concisely in the plan so the user is choosing with full information. Be decisive, not stubborn.

If the query proposed no approach, design one from scratch under the Step 4 lens.

## Step 6: Decide whether a solution diagram earns its place

The current-state diagram from Step 3 is always included. A second diagram of the *proposed* solution is an aid for hard-to-follow solutions, not a default deliverable.

- **Include one** only when the solution has non-obvious control flow, multiple interacting components, a sequence/handshake between systems, a state machine, or a data flow that prose alone makes hard to track.
- **Skip it** for small, linear, or single-file changes — the Step 3 diagram with its marked change points is enough. Do not add diagrams for the sake of it.
- **Format:** Mermaid — `flowchart`, `sequenceDiagram`, or `stateDiagram` as best fits — since it renders in most markdown surfaces. Fall back to a clean ASCII diagram if Mermaid is unsuitable for the host.
- The diagram must illuminate the *hard part*. Label nodes and edges in plain language so a reader who skips the prose still grasps the shape of the solution.

## Step 7: Write the plan (output contract)

Structure the plan so any other agent or human can execute it cold and still land the highest-quality result:

- **Context** — why this change is needed: the problem, what prompted it, the intended outcome.
- **Current state** — the Step 3 diagram plus a few sentences on how the system works today and where the change lands.
- **Approach** — the recommended design. Include the "Approach considered & rejected" note from Step 5 when relevant.
- **Solution diagram** — only if Step 6 calls for one.
- **Implementation steps** — concrete and ordered, naming the specific files, functions, and existing utilities to touch or reuse (with real paths from Step 2). For a pattern repeated across many files, describe it once with a few representative paths rather than enumerating every file.
- **Verification** — how to prove it works end-to-end: tests to run or add, commands, and manual checks.
- **Risks / tradeoffs** — edge cases, performance notes, and follow-ups a reviewer would want flagged.

Keep it scannable but complete. Then finish per the mode resolved in Step 1.

## Constraints

- **Plan only — never implement.** This skill does not write or modify implementation code. Its only writes are to the plan file.
- **Always operate in Plan Mode.** Enter it if the harness supports it; fall back to a plan file only when the harness has no plan-mode concept.
- **Ground everything.** No invented paths, APIs, or behavior — verify against the codebase or authoritative docs.
- **Be adversarial but flexible.** Pivot to the better approach by default and document the tradeoff; defer to an insistent user while surfacing the risk.
- **Understand before designing.** Always map the current system in a grounded diagram (Step 3) before proposing a solution.
- **Solution diagrams must earn their place.** No solution diagram unless it makes a genuinely hard solution easier to follow.
- **Harness-agnostic.** Do not depend on any one harness's exploration/planning subagents or assume a single exit primitive.
- **Executable by a cold reader.** The plan must stand on its own for any agent or human.
