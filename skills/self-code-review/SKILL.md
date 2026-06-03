---
name: self-code-review
description: Review the current branch's diff against its base branch — the open PR's base branch when one exists, otherwise the repo's default branch. Flags newly introduced bugs (logic errors, null/undefined derefs, inverted conditionals, unhandled async, off-by-one), functionality regressions, unnecessary uncommon hooks (useRef/useEffect/useMemo/useCallback), functionality that duplicates existing shared utils/helpers/components (named duplicates and inline reimplementations), code that drifts from established conventions/architecture/syntax in the codebase, and stale leftover code from iteration. Use when the user runs /self-code-review or asks for a review of their current branch, a pre-PR check, or "review my changes".
allowed-tools:
  - "Bash(git fetch *)"
  - "Bash(git log *)"
  - "Bash(git diff *)"
  - "Bash(git status *)"
  - "Bash(git rev-parse *)"
  - "Bash(git merge-base *)"
  - "Bash(git symbolic-ref *)"
  - "Bash(git show *)"
  - "Bash(git branch *)"
  - "Bash(gh pr view *)"
  - "Bash(gh repo view *)"
---

# Code Review

Reviews the current branch against its base branch — the open PR's base branch when the branch has one, otherwise the repo's default branch. **Read-only** — never mutates the working tree (no checkout, pull, commit, push, or stash).

## Workflow

### Step 1: Establish the diff baseline

First, identify the current branch and whether it has an open PR. Run these in parallel:

```bash
git rev-parse --abbrev-ref HEAD
gh pr view --json number,baseRefName,url,state 2>/dev/null
```

- If the current branch is `main` or `master`, stop and tell the user there is nothing to review (they need to be on a feature branch).

Now resolve the base ref to diff against — call it `BASE_REF` — in this priority order:

1. **Open PR base.** If `gh pr view` returned an open PR, set `BASE_REF` to its `baseRefName` (e.g. `develop`). Surface the PR number and url in the output so the reviewer knows the baseline came from the PR config.
2. **Repo default branch.** Otherwise (no PR, or `gh` is missing/unauthenticated/errored), resolve the repo's actual default branch — do **not** assume `main`:
   - `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`
   - If that fails, fall back to `git symbolic-ref --short refs/remotes/origin/HEAD` and strip the leading `origin/`.
   - If both fail, use `main` as a last resort.
   - Note in the output which resolution path was used (resolved default vs. last-resort `main`).

Then fetch the base ref and compute the merge base (substitute the resolved `BASE_REF`):

```bash
git fetch origin <BASE_REF> --quiet
git merge-base origin/<BASE_REF> HEAD
```

- If `git fetch` fails (no remote, offline, etc.), fall back to local `<BASE_REF>` and note the limitation in the output.

Capture the resulting merge-base SHA — call it `BASE` for the rest of the workflow.

### Step 2: Resolve Linear ticket context

The Summary should explain the *problem* this PR is meant to solve, not just the *what* of the diff. Pull that context from Linear when available.

1. Extract candidate ticket IDs from:
   - The current branch name (e.g. `kor-1449-ulr-into-ibnr` → `KOR-1449`).
   - Commit subjects from `git log <BASE>..HEAD --oneline` (e.g. `feat(bdx): ... (KOR-1449)`, `fix(ui): ... (KOR-1385/1449)`).
   - Use the regex `[A-Za-z][A-Za-z0-9]+-\d+`, upper-case the matches, and dedupe.

2. If one or more IDs are found, invoke the **`linear`** skill and call `mcp__linear-server__get_issue` for each unique ID. Capture `title`, `description`, `state`, `priority`, and `url`.
   - Cap at **3 ticket fetches** per review. If more IDs are referenced, fetch the first three (branch-name match first, then commits in order) and note the rest in **Other Notes**.
   - Tolerate failures: if MCP isn't connected, the ticket is archived, or permissions block the read, log "Could not fetch Linear ticket KOR-XXXX — falling back to commit/diff inference" and continue. Never block the review on a Linear failure.

3. If no IDs are found at all, skip the fetch and surface that in the **Problem** section of the output (see Step 5).

### Step 3: Gather diff context

Run these in parallel (substitute the captured `BASE`):

```bash
git log <BASE>..HEAD --oneline
git diff --stat <BASE>..HEAD
git diff --name-status <BASE>..HEAD
git diff <BASE>..HEAD
```

If the diff is empty, stop and tell the user the branch has no changes vs the base branch (`<BASE_REF>`).

**For large diffs** (> ~30 files or > ~1500 lines): don't rely on diff hunks alone. Read the full contents of the most-changed files so you can spot code that was *removed but is still referenced elsewhere*, and dispatch an Explore subagent to search for cross-file impacts (callers of removed/renamed symbols, similar utilities elsewhere in the repo).

### Step 4: Apply the six review guidelines

#### a) Newly introduced bugs
Does the *new or changed* code contain a defect — a way it produces wrong results, crashes, or misbehaves at runtime? This is distinct from **(b) Functionality regressions**: regressions are about *breaking pre-existing* behavior, while this guideline is about defects *inside the code this branch adds*. When a finding fits both, put it under whichever frames the failure most clearly and don't list it twice.

**Reason about correctness from first principles — a bug can come from anything, not just the patterns listed below.** For each meaningful change, ask: what does this code intend to do, and is there any input, state, ordering, or environment in which it does the wrong thing? Trace the actual logic, edge cases, and data flow of the change rather than pattern-matching against a fixed checklist. The list below is a non-exhaustive set of *common* failure modes to jog your thinking — never treat it as the full scope of what counts as a bug, and do flag defects that don't resemble any of these:

- Null/undefined dereferences and unchecked optional access (`obj.a.b` where `a` may be absent; non-null assertions that aren't guaranteed).
- Inverted or wrong boolean/comparison logic (`!`/`&&`/`||` mistakes, `===` vs `==`, `<` vs `<=`, swapped operands).
- Off-by-one and boundary errors (loop bounds, slice/substring indices, empty-collection edge cases).
- Missing `await`, floating promises, or unhandled rejections (async function called without awaiting; `forEach` with an async callback).
- Incorrect error handling — swallowed errors, `catch` that hides failures, too-broad or mis-scoped `try`, returning on the error path without surfacing it.
- Direct mutation of state, props, or shared/frozen objects where an immutable update is expected.
- Race conditions and ordering assumptions (state read before it's set, concurrent writes, effects firing out of order).
- Resource leaks — unclosed handles/connections/streams, missing cleanup/unsubscribe, intervals/timeouts never cleared.
- Incorrect type coercion, parsing, or serialization (`parseInt` without radix, `JSON.parse` on possibly-invalid input, number/string confusion).
- Using a value before it's assigned, or a code path that returns `undefined` where a value is required.
- Anything else that makes the code incorrect: wrong algorithm or formula, mishandled units/timezones/encodings, incorrect SQL/query logic, broken invariants or state machines, security holes (injection, missing authz, leaked secrets), domain-specific logic errors, etc.

Flag concrete, defensible defects only: cite `file:line` and state the scenario in which it fails. When the surrounding codepath is uncertain (you can't see all callers or inputs), frame the finding as a question rather than an assertion. Don't restate nits the linter/type-checker already catches.

#### b) Functionality regressions
Did this branch accidentally remove or break something that worked before? Reason about what behavior existed prior to the diff and whether any change could alter it for existing callers or users — the list below is a non-exhaustive set of common regression patterns, not the full scope. Flag any regression you can justify, even if it doesn't match a listed pattern.

- Removed exports, props, event handlers, or branches in `if`/`switch`.
- Narrowed conditionals (e.g. `if (a || b)` → `if (a)`) without justification.
- Signature changes (added required params, changed return shape) — grep callers to confirm they were updated.
- Renamed/moved files — grep for old import paths.
- Removed cases from a discriminated union or enum without updating exhaustive switches.
- Behavior changes in shared utilities that callers depend on.
- Anything else that changes existing behavior: altered defaults, narrowed types, changed ordering/timing, removed validation, modified copy/output that something asserts on, etc.

#### c) Unnecessary uncommon hooks
Scan additions for `useRef`, `useEffect`, `useMemo`, `useCallback`, `useImperativeHandle`, `useLayoutEffect`.

For each new occurrence, judge whether it's load-bearing:

- **Likely unnecessary**: `useEffect` that syncs derived state (compute it during render); `useMemo`/`useCallback` whose dep array changes every render anyway; `useRef` storing values that could be props or local variables; `useEffect` for fetching data in a Server Component or that should be an event handler.
- **Legitimate**: DOM measurement / focus, integrating non-React libraries, subscribing to external stores, debounce/throttle timers, stable identity required by a downstream `memo` boundary.

When flagging, suggest the simpler alternative (derived state, event handler, server component, ref-as-prop, etc.). Don't flag hooks that are clearly load-bearing — balance code quality against churn.

#### d) Duplicated functionality / reuse opportunities
Catch functionality the diff adds that already exists in the project's shared layer. This covers **two** cases:

**1. Named duplicates** — a *new* utility function, hook, or component whose name/shape matches something already in the repo:

- Grep the repo for similar names (`<name>`, partial matches, common synonyms).
- For components, look in shared UI packages (`packages/ui`, `packages/design-system`, `apps/*/components`, `apps/*/lib`, etc.).
- For utilities, look in `packages/utils`, `packages/core`, `apps/*/lib`, `lib/`, `utils/`.

**2. Inline reimplementation** — logic written *inline* in the diff that duplicates the behavior of an existing shared util/helper/hook even though it isn't a named helper. Search by *behavior*, not just name. The examples below are common cases, not a closed list — flag any inline logic that re-creates something the shared layer already provides:

- Inline date/number/currency formatting that duplicates a shared formatter.
- Hand-rolled debounce/throttle, deep-clone, group-by, sleep, retry, or similar primitives that already exist as shared utilities.
- Ad-hoc `fetch`/HTTP wrappers, auth-header construction, or error handling that bypasses an existing shared client.
- Re-derived constants, config, enums, or validation logic that's already centralized elsewhere.
- Reimplemented data transforms / selectors that a shared hook or util already provides.

Use Glob + Grep, or dispatch an Explore subagent if the surface area is large. When you find a duplicate (named or inline), cite the existing shared path and suggest importing/calling it instead of the new code.

#### e) Stale code from iteration
Anything left behind that shouldn't ship. The bullets below are the usual suspects, not an exhaustive list — flag any leftover scaffolding, dead code, or debugging residue from building this change, whatever form it takes:

- `console.log`, `console.debug`, `debugger`, `alert`.
- Commented-out code blocks.
- Unused imports (in the diff context).
- New exports nothing imports.
- Leftover `TODO`, `FIXME`, `WIP`, `XXX` markers tied to this change.
- Mock data, fake delays, or hardcoded test values in production paths.
- Feature flag / experiment scaffolding that's no longer toggled.
- Half-finished function bodies, dead branches behind `if (false)`, etc.

Skip nits Biome / Ultracite / ESLint already catch — focus on substance.

#### f) Convention & architectural drift
Does the new code follow the patterns already established elsewhere in the codebase, or does it invent its own?

First, **infer the established convention** by looking at the diff's neighbors — sibling files in the same directory, other files in the same package, and existing files that play the same role (other components, other API routes, other hooks, other tests). Then flag where the diff diverges. The categories below are common axes of drift, not a closed set — flag any meaningful divergence from an established pattern, even one not listed here:

- **Naming** — file names, function/variable casing, component naming that breaks from how peers are named.
- **Placement / module structure** — new code living somewhere different from where its peers live (e.g. a util dropped into a component file when the repo has a `lib/`/`utils/` home for it).
- **Syntax / idiom** — diverging from the repo's prevailing style: `function` declarations where the codebase uses arrow functions, default exports where it uses named exports, `.then()` chains where it uses `async/await`, class components where it uses function components, etc.
- **Patterns** — error handling, data fetching, state management, or styling done differently from the surrounding code (e.g. raw `fetch` where peers use a shared client/hook; inline styles where peers use the design system; manual `try/catch` where peers use a shared error boundary/wrapper).
- **Imports** — import style or path-alias usage inconsistent with the rest of the project (e.g. deep relative imports where peers use `@/...` aliases).

Only flag **meaningful** drift that affects consistency or maintainability — cite the established pattern with a concrete `file:line` example so the reviewer can compare, and frame it as a question when the convention is ambiguous or there's a plausible reason for the divergence. Do **not** flag formatting/style the linter or formatter already enforces.

### Step 5: Output

Use this exact structure. Keep it concise — every finding must cite `file:line` so the reviewer can jump directly. Use "None spotted" rather than omitting a section, so the reviewer can see each guideline was considered.

```markdown
## Problem
<2–4 sentences pulled from the Linear ticket(s) fetched in Step 2: the user-facing problem, who reported it / what triggered it, and the acceptance criteria or "done" condition stated in the ticket. Cite each ticket as a markdown link in `[KOR-1449](url)` form.

If no Linear ID was found in the branch or commits, write: "No Linear ticket linked from branch or commits — Problem inferred from commit messages: <one-line inference>."

If a ticket was referenced but the fetch failed, write: "Linear ticket KOR-XXXX referenced but could not be fetched (<reason>) — Problem inferred from commit messages: <one-line inference>.">

## Summary
<1–3 sentences: what the PR actually changes, and whether that matches the Problem above. If the implementation goes beyond the ticket (or stops short of it), say so here — that's the load-bearing observation. Don't restate the diff line-by-line.>

## Review Order
<Include this section when the diff is large (>10 files or >500 lines) OR touches any DB-migration-related files (`packages/db/drizzle/*.sql`, `packages/db/src/schema/**`, `packages/db/drizzle/meta/*`, or `packages/db/src/scripts/backfill-*`). Otherwise skip.

Before grouping, collect the **complete file list** from the `git diff --name-status <BASE>..HEAD` output gathered in Step 3 — this is the authoritative set every group must draw from.

When DB-migration files are present, list them as the FIRST grouping — schema context is load-bearing for everything downstream. Look for: new columns/types, NOT-NULL adds without defaults, dropped or renamed columns still referenced by app code, index/constraint changes, backfill correctness.

Then list remaining file groupings in dependency order (schema → core/lib → API/server → UI), each with a one-line "what to look for" hint.

**Completeness check**: after forming all groups, verify every file from the complete list appears in exactly one group. Any file with no obvious grouping goes into an "Other" group — never drop a file silently.>

## Findings

### Bugs Introduced
- `path/to/file.ts:42` — <the defect in the new code and the scenario it fails in> | Suggest: <fix>
- (or: None spotted.)

### Functionality Regressions
- `path/to/file.ts:42` — <what changed> | Suggest: <fix>
- (or: None spotted.)

### Hook Usage
- `path/to/component.tsx:15` — `useRef` here is unnecessary because <reason>. Suggest: <alternative>.
- (or: None spotted.)

### Duplication / Reuse Opportunities
- `path/to/new-helper.ts` duplicates `existing/path/helper.ts`. Suggest: import from there.
- `path/to/file.ts:30` — inline date formatting reimplements `packages/utils/format-date.ts`. Suggest: call the shared util.
- (or: None spotted.)

### Convention & Architecture Drift
- `path/to/file.ts:12` — uses a default export while peers in this dir use named exports (e.g. `path/to/peer.ts:1`). Suggest: match the convention.
- (or: None spotted.)

### Stale Code
- `path/to/file.ts:88` — leftover `console.log`. Remove.
- (or: None spotted.)

## Other Notes
<Optional. Brief. Things outside the buckets above that genuinely matter: missing tests for a new branch, a11y regression, type-safety gap, security concern. Skip if there's nothing.>
```

## Constraints

- **Read-only.** Never run `git checkout`, `git pull`, `git stash`, `git commit`, `git push`, or anything else that mutates the tree.
- **Be specific.** Every finding must cite a path and (where possible) a line number.
- **Don't restate the diff.** Assume the reviewer can read it. Add value via judgment.
- **Don't flag what the linter catches.** Focus on architecture, regressions, and reuse.
- **Balance.** Some hooks are necessary, some duplication is intentional, some "stale" code is actually intentional scaffolding for a follow-up, and some convention divergence is justified. When in doubt, frame the finding as a question.
- **Convention drift must cite the established pattern.** Don't assert a convention exists — point to a concrete `file:line` peer that demonstrates it, so the reviewer can judge whether the divergence is warranted.
- **Linear context is advisory, not authoritative.** If the ticket and the diff disagree, surface the disagreement as a finding rather than trusting either source blindly. Tickets get stale; PRs sometimes do more (or less) than the ticket says.
