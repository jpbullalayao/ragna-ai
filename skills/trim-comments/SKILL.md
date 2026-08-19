---
name: trim-comments
description: >-
  Relentlessly remove or rewrite low-value comments in code: comments that
  merely restate the name of the variable, method, prop, class, or file they
  annotate, and comments that reference removed or superseded functionality
  from earlier iterations of the feature (change-history narration like
  "previously", "used to", "no longer", "changed from"), and comments that
  are needlessly verbose — condensing them to the shortest wording that
  preserves comprehension. Use when the user
  runs /trim-comments [<path>|<branch>], or asks to "trim comments",
  "clean up comments", "remove redundant comments", or "delete stale
  comments". Defaults to the current branch's diff against its base branch;
  a path argument scopes it to specific files or directories instead.
allowed-tools:
  - "Bash(git fetch *)"
  - "Bash(git diff *)"
  - "Bash(git merge-base *)"
  - "Bash(git symbolic-ref *)"
  - "Bash(gh pr view *)"
  - "Bash(gh repo view *)"
  - "Read"
  - "Edit"
---

# Trim Comments

Removes or rewrites comments that add no information beyond what the code already says, comments that leak the iteration history of a feature, and comments that say something worthwhile in more words than needed. **Mutates the working tree** — all edits are applied inline with the Edit tool.

Invocation:
- `/trim-comments` — operate on the current branch's diff against its base branch
- `/trim-comments <path>` — operate on a specific file or directory (any extension; recurse into directories)
- `/trim-comments <branch>` — operate on the diff against the given base branch

## Workflow

### Step 1: Resolve scope

If an argument was given and it exists on disk, treat it as a path scope: collect the target source files with the Glob tool (skip `node_modules`, lockfiles, build output, and generated files).

Otherwise resolve `<base-branch>` in this priority order:

1. **Explicit branch argument**, if given.
2. **Open PR base:** `gh pr view --json baseRefName -q .baseRefName 2>/dev/null`.
3. **Repo default branch:** `gh repo view --json defaultBranchRef -q .defaultBranchRef.name`, falling back to `git symbolic-ref --short refs/remotes/origin/HEAD` (strip `origin/`), falling back to `main` (note this in the output).

Then:

```bash
git fetch origin <base-branch> --quiet
git merge-base origin/<base-branch> HEAD
git diff --name-status <BASE>..HEAD
git diff <BASE>..HEAD
```

If the fetch fails, fall back to the local `<base-branch>`. If the diff is empty (and no path scope was given), stop and tell the user there is nothing to trim.

### Step 2: Scan for offending comments

Read each in-scope file (for diff scope, focus on comments added or touched by the diff, plus comments immediately adjacent to changed code). Flag every comment — line comments, block comments, JSDoc/docstrings — that matches either category:

**Category 1 — Name restatement.** The comment says nothing beyond what the identifier it annotates already says. Examples:

```ts
// The user's email
const userEmail = ...

/** Fetches the invoices */
const fetchInvoices = async () => ...

// onClick handler
onClick: ...
```

Fix: **delete** the comment. If a doc comment mixes restatement with genuinely non-obvious information (constraints, units, edge cases, side effects), keep only the informative part.

**Category 2 — Iteration remnants.** The comment references decisions, behavior, or code that existed in an earlier iteration of the feature but was changed or removed. Signals: "previously", "used to", "no longer", "changed from", "instead of the old", "was doing X, now does Y", "legacy", references to functions/params/branches that don't exist in the current code, or explanations framed as a contrast against something the reader can no longer see. Verify a referenced symbol is truly gone with the Grep tool before flagging.

Fix: **rewrite** the comment to describe the current implementation as if it had always worked this way — or **delete** it if the current code needs no explanation. Keep a reference to prior behavior only when it documents a deliberate, still-active concern (e.g. a backward-compatibility shim or migration note that callers depend on).

**Category 3 — Verbosity.** The comment carries real information but says it in more words than comprehension requires: filler phrases ("note that", "it's worth mentioning", "basically", "in order to"), restating the obvious half of a sentence alongside the non-obvious half, multi-line prose where one line suffices, or hedging/narration aimed at a reviewer rather than the next reader. Examples:

```ts
// Note that we need to debounce here in order to avoid
// firing a request on every single keystroke the user types
→ // Debounced to avoid a request per keystroke

/** This function is responsible for retrying the upload. Retries up to 3 times with exponential backoff. */
→ /** Retries up to 3 times with exponential backoff. */
```

Fix: **rewrite** to the shortest wording that preserves the non-obvious information. Only shorten when no meaning is lost — if trimming would sacrifice comprehension of a constraint or gotcha, keep the length. After each rewrite, **re-read the remaining sentence** — deleting words can break grammar or leave a fragment (e.g. cutting "May involve a network round-trip" down to "Involve a network round-trip"); fix agreement and completeness before moving on.

**Category 4 — Rationale overreach.** The comment states a behavior plus a justification or consequence clause ("X — because Y", "X: otherwise Z would happen"). Keep only the behavior clause unless the justification is a genuinely non-recoverable gotcha; extended rationale belongs in a decision doc, ADR, or PR description, not inline. Examples:

```ts
// When PostHog is down we deny rather than grant: an outage should never let someone into another user's draft.
→ // When PostHog is down we deny rather than grant.

// No answer from PostHog — deny for this call, but don't memoize the denial: a transient failure shouldn't keep denying the user from cache for a whole TTL once PostHog recovers.
→ // No answer from PostHog — deny for this call.
```

Related fixes in the same spirit:

- **State a policy once.** If the same rule (e.g. "deny on error") is commented at multiple sites in a module, keep one canonical statement and reduce the other sites to a short clause or nothing.
- **Don't annotate self-evident defensive checks.** A strict comparison like `return value === true;` needs no comment explaining why strictness is safer — delete such comments entirely.
- **Drop caller-instruction docs on private helpers whose callers already comply.** A doc block on a non-exported function instructing how it must be called (e.g. "callers must resolve X before entering the lock") can be deleted when every existing caller complies and the structure/types enforce it.
- **Doc summaries must not restate adjacent declarations.** Delete phrases in a type/function doc that repeat what the signature or fields immediately below already say (e.g. "with its draft-access rule already resolved" directly above a `hasOrgDraftAccess: boolean` field).

**Never touch:** comments stating non-obvious constraints, rationale, or gotchas the code can't express; license headers; directive comments (`eslint-disable`, `@ts-expect-error`, `prettier-ignore`, `TODO`/`FIXME` with real content); doc comments whose content goes beyond the name.

### Step 3: Present findings and apply

List every finding before editing:

```
### Comment Trim Findings
- `path/to/file.ts:12` — [RESTATES] "// the user's email" → delete
- `path/to/file.ts:48` — [REMNANT] "// no longer uses polling, now websockets" → rewrite: "// Pushes updates over the websocket connection"
- `path/to/file.ts:73` — [VERBOSE] "// Note that we need to debounce here in order to avoid firing a request on every keystroke" → rewrite: "// Debounced to avoid a request per keystroke"
- `path/to/file.ts:91` — [RATIONALE] "// Deny rather than grant: an outage should never let someone in" → rewrite: "// Deny rather than grant."
(or: Nothing to trim.)
```

Then apply every fix with the Edit tool. When deleting a comment, remove the whole line (or the comment portion of a mixed line) without leaving stray blank lines.

### Step 4: Summary

```
## Trim Comments Summary

**Scope:** <branch vs base | path>
**Files touched:** N
**Deleted:** X comment(s) · **Rewritten:** Y comment(s)
```

## Constraints

- **Comments describe the present, not the past.** After this skill runs, no comment should read as a changelog entry.
- **When in doubt, keep it — except rationale elaboration.** Only remove a comment when it is unambiguously redundant or stale. Rationale/consequence elaboration is not "doubt": its default is trim, keeping only the behavior clause. Genuine non-obvious gotchas still stay.
- **Shorter, never lossier.** Prefer the most concise wording, but never trade away comprehension — a longer comment that's needed to understand a constraint stays long.
- **Rewrites are behavior-neutral.** Never change code — only comments, docstrings, and doc blocks.
- **Stay in scope.** Only edit files in the resolved diff or path scope.
- **Never run destructive git commands.** No `checkout`, `reset`, `stash`, `commit`, or `push`.
