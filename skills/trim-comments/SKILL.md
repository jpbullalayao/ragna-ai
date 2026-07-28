---
name: trim-comments
description: >-
  Relentlessly remove or rewrite low-value comments in code: comments that
  merely restate the name of the variable, method, prop, class, or file they
  annotate, and comments that reference removed or superseded functionality
  from earlier iterations of the feature (change-history narration like
  "previously", "used to", "no longer", "changed from"). Use when the user
  runs /trim-comments [<path>|<branch>], or asks to "trim comments",
  "clean up comments", "remove redundant comments", or "delete stale
  comments". Defaults to the current branch's diff against its base branch;
  a path argument scopes it to specific files or directories instead.
allowed-tools:
  - "Bash(git fetch *)"
  - "Bash(git log *)"
  - "Bash(git diff *)"
  - "Bash(git status *)"
  - "Bash(git rev-parse *)"
  - "Bash(git merge-base *)"
  - "Bash(git symbolic-ref *)"
  - "Bash(gh pr view *)"
  - "Bash(gh repo view *)"
  - "Bash(grep *)"
  - "Bash(find *)"
  - "Read"
  - "Edit"
---

# Trim Comments

Removes or rewrites comments that add no information beyond what the code already says, and comments that leak the iteration history of a feature. **Mutates the working tree** — all edits are applied inline with the Edit tool.

Invocation:
- `/trim-comments` — operate on the current branch's diff against its base branch
- `/trim-comments <path>` — operate on a specific file or directory (any extension; recurse into directories)
- `/trim-comments <branch>` — operate on the diff against the given base branch

## Workflow

### Step 1: Resolve scope

If an argument was given and it exists on disk, treat it as a path scope: collect the target source files (skip `node_modules`, lockfiles, build output, and generated files).

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

**Category 2 — Iteration remnants.** The comment references decisions, behavior, or code that existed in an earlier iteration of the feature but was changed or removed. Signals: "previously", "used to", "no longer", "changed from", "instead of the old", "was doing X, now does Y", "legacy", references to functions/params/branches that don't exist in the current code, or explanations framed as a contrast against something the reader can no longer see. Verify a referenced symbol is truly gone with `grep` before flagging.

Fix: **rewrite** the comment to describe the current implementation as if it had always worked this way — or **delete** it if the current code needs no explanation. Keep a reference to prior behavior only when it documents a deliberate, still-active concern (e.g. a backward-compatibility shim or migration note that callers depend on).

**Never touch:** comments stating non-obvious constraints, rationale, or gotchas the code can't express; license headers; directive comments (`eslint-disable`, `@ts-expect-error`, `prettier-ignore`, `TODO`/`FIXME` with real content); doc comments whose content goes beyond the name.

### Step 3: Present findings and apply

List every finding before editing:

```
### Comment Trim Findings
- `path/to/file.ts:12` — [RESTATES] "// the user's email" → delete
- `path/to/file.ts:48` — [REMNANT] "// no longer uses polling, now websockets" → rewrite: "// Pushes updates over the websocket connection"
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
- **When in doubt, keep it.** Only remove a comment when it is unambiguously redundant or stale; a comment that might carry rationale stays.
- **Rewrites are behavior-neutral.** Never change code — only comments, docstrings, and doc blocks.
- **Stay in scope.** Only edit files in the resolved diff or path scope.
- **Never run destructive git commands.** No `checkout`, `reset`, `stash`, `commit`, or `push`.
