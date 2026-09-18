---
name: check-for-regressions
description: >-
  Analyze the current branch's diff against its base branch — the open PR's
  base branch when one exists, otherwise the repository's GitHub default
  branch — and report potential feature or logical regressions with evidence
  and suggested fixes, without applying any changes. Use when the user runs
  /check-for-regressions, or asks to "check for regressions", "regression
  check", "did this break anything", "look for regressions in my branch", or
  wants a read-only pre-merge regression pass before opening or merging a PR.
---

# Check for Regressions

Analyzes the current branch diff for **feature and logical regressions** — changes that break behavior that worked before this branch. **Read-only and static-only**: inspect code, callers, tests, docs, and history with whatever tools the host agent has; never edit files, never auto-fix, and never run project tests, type checks, builds, or other verification commands.

## Workflow

### Step 1: Establish the diff baseline

Identify the current branch and resolve the base branch to compare against — call it `BASE_REF`:

1. **Explicit argument.** If the user passed a branch name, use it as `BASE_REF`.
2. **Open PR base.** If the current branch has an open pull request, use that PR's base branch.
3. **Repository default branch.** Otherwise use the repository's GitHub default branch.

If the baseline cannot be determined, stop and tell the user what is missing.

If the current branch **is** the resolved default branch and no explicit base was given, stop — there is nothing to compare.

Compute the merge base between `BASE_REF` and the current branch — call it `BASE`. Surface which baseline was used (PR base, explicit branch, or repo default) in the output.

### Step 2: Gather diff context

Collect enough context to reason about behavior change, not just line edits:

- Commit messages on the branch
- Changed file list with add/modify/delete/rename status
- Diff size summary
- Full diff content for review

If the diff is empty, stop and tell the user the branch has no changes vs `BASE_REF`.

**For large diffs** (> ~30 files or > ~1500 lines): do not rely on diff hunks alone. Read full contents of the most-changed files and trace cross-file impacts — callers of removed or renamed symbols, stale import paths, shared utilities used outside the diff. Use parallel exploration when the host supports it.

For each materially changed flow, inspect **both** the base version and the head version. Ground "before" behavior in the base-branch source, not only from removed diff lines.

### Step 3: Reconstruct intended behavior

Before hunting regressions, build a mental model of what this change is *supposed* to do:

- PR title/body and linked tickets, when available
- Commit subjects and bodies
- Existing tests, docs, and comments that describe expected behavior
- How surrounding code in the repo already solves similar problems

If the stated intent and the diff diverge, surface that in **Summary** — a branch that overshoots or undershoots its goal often hides regressions.

### Step 4: Analyze for regressions

Ask repeatedly: **what behavior existed before, and could this diff alter it for existing callers or users?**

The patterns below are common regression signals, not an exhaustive list. Flag any justified regression even when it does not match a bullet.

#### Contract and surface-area changes

- Removed or narrowed exports, props, event handlers, API fields, CLI flags, or config keys
- Signature changes — new required parameters, removed optional params, changed return shape or error type
- Renamed or moved modules — search for stale import paths and string references
- Removed enum/union/discriminant cases without updating exhaustive switches or downstream matchers
- Altered defaults, fallbacks, or feature-flag behavior

#### Logic and control-flow changes

- Narrowed conditionals without corresponding caller updates
- Removed `if`/`switch` branches, early returns, or error paths that callers relied on
- Changed ordering, timing, debouncing, caching, or async sequencing
- Swallowed errors, changed retry/backoff, or altered validation that previously rejected bad input
- Modified shared utilities, selectors, serializers, or formatters used outside the diff

#### Data, state, and persistence

- Schema or migration changes that drop/rename columns still referenced by app code
- Backfills or data transforms that lose rows or mis-map values
- Changed persistence semantics (what gets saved, when, and under which conditions)
- Broken invariants or state-machine transitions visible to existing users

#### User-visible and integration behavior

- Changed copy, labels, URLs, redirects, or response payloads that tests or clients assert on
- Removed side effects that downstream jobs, webhooks, or UI flows depended on
- Authz/authn checks tightened or removed in ways that change who can do what

#### Cross-file consistency

- Symbol removed in one file but still referenced elsewhere
- Duplicate logic updated in one place but not another that must stay in sync
- Test files not updated when production behavior they cover changed

**Confidence bar:** report a finding when you can cite evidence and a plausible failing scenario. When callers or runtime inputs are uncertain, frame it as a **Possible regression** with lower confidence rather than asserting. Do not list linter, formatting, or style nits.

**Intentional breaking changes:** if the diff clearly intends to remove or change behavior (major version bump, migration note, ticket requirement), say so and downgrade severity — but still report impact on callers that may not have been updated.

### Step 5: Output

Use this structure. Keep it concise; every finding must cite `file:line` when a specific location exists.

```markdown
## Baseline
<Current branch vs `BASE_REF`; note whether baseline came from open PR, explicit arg, or repo default branch>

## Summary
<1–3 sentences: what the branch changes, whether that matches its stated intent, and overall regression risk>

## Regressions

### High confidence
- `path/to/file.ts:42` — **Severity:** high · **Confidence:** high
  - **Before:** <prior behavior>
  - **After:** <new behavior>
  - **Scenario:** <input/state/caller where this breaks>
  - **Impact:** <who/what is affected>
  - **Potential fix:** <describe the fix; optional minimal snippet — do not apply>

(or: None spotted.)

### Possible regressions
- `path/to/file.ts:88` — **Severity:** medium · **Confidence:** low
  - **Before:** …
  - **After:** …
  - **Scenario:** …
  - **Impact:** …
  - **Potential fix:** …

(or: None spotted.)

## Analysis limitations
<What could not be verified statically — missing baseline access, large diff not fully traced, external systems not inspectable, etc. Omit if nothing material.>
```

**Empty sections:** when a subsection has no findings, output exactly `(or: None spotted.)` under that heading — no checklist of what was searched.

**Severity guide:**
- **high** — likely breaks existing users/callers without a compensating change in the diff
- **medium** — breaks a subset of cases or depends on assumptions that may not hold
- **low** — edge case or needs runtime confirmation

## Constraints

- **Read-only.** Never create, edit, or delete files in the working tree. Never commit, push, stash, checkout, or otherwise mutate repo state.
- **Static-only.** Never run tests, type checks, builds, linters, or other project verification commands — even when discoverable from package scripts.
- **Report, don't fix.** Describe potential fixes only; never apply them.
- **Be specific.** Every finding cites `file:line` where possible and states the failing scenario.
- **Don't restate the diff.** Assume the reader can read it; add judgment about behavioral risk.
- **Balance.** Some behavior changes are intentional. Flag impact and caller risk without treating every API change as a bug.
