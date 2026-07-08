---
name: pull-latest-default-branch
description: >-
  Fast-forward the local default branch (main, master, etc.) to match the remote
  without switching branches. Use when the user types /pull-latest-default-branch,
  asks to "pull latest main", "update local main", "sync default branch",
  "fetch latest master", or wants their local default branch current while staying
  on their current branch.
allowed-tools:
  - "Bash(git branch *)"
  - "Bash(git status *)"
  - "Bash(git pull *)"
  - "Bash(git fetch *)"
  - "Bash(git symbolic-ref *)"
  - "Bash(git rev-parse *)"
  - "Bash(git ls-remote *)"
  - "Bash(gh repo view *)"
---

# Pull Latest Default Branch

Fast-forward the local default branch to match `origin` without checking out that branch.

## When to invoke

Trigger on any of:

- `/pull-latest-default-branch`
- "pull latest main" / "pull latest master"
- "update local main" / "sync default branch"
- "fetch latest master" / "update my default branch"

If the user names a specific branch (e.g. "update local `develop`"), use that name instead of auto-detected default.

## Workflow

### 1. Gather state

Run in parallel:

```bash
git branch --show-current
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || gh repo view --json defaultBranchRef -q .defaultBranchRef.name
```

- `BRANCH` — current branch name (empty when detached HEAD).
- `DEFAULT` — default branch (strip `origin/` prefix if present; fall back to `main` if unresolved).

Then capture the local default ref before updating (if it exists):

```bash
git rev-parse --verify <DEFAULT> 2>/dev/null
git rev-parse --verify origin/<DEFAULT> 2>/dev/null
```

### 2. Update default branch (in-place, no checkout)

**If already on `DEFAULT`:**

```bash
git pull --ff-only
```

**If on any other branch (including detached HEAD):**

```bash
git fetch origin <DEFAULT>:<DEFAULT>
```

This fast-forwards the local default ref without switching branches. It also creates the local branch if it does not exist yet. Non-fast-forward updates are refused, so local-only commits on the default branch are not silently overwritten.

### 3. Prune stale refs

```bash
git fetch --prune
```

### 4. Report

Return a short summary:

- Default branch resolved (`<DEFAULT>`)
- Update method: `pull --ff-only` (on default) or `fetch origin DEFAULT:DEFAULT` (in place)
- Old and new commit SHAs when available
- Stale remote-tracking refs pruned

## Edge cases

- **Detached HEAD** — proceed; in-place fetch does not require a checked-out branch.
- **Dirty working tree** — proceed for in-place fetch (no checkout). If on `DEFAULT`, `git pull --ff-only` may still work; if it fails due to local changes, stop and tell the user to stash or commit.
- **`git fetch origin DEFAULT:DEFAULT` fails (non-ff)** — stop; explain local default has diverged; do not force without explicit user instruction.
- **`git pull --ff-only` fails** — stop and surface the error; do not force-pull or rebase without explicit user instruction.
- **`gh` unavailable / unauthenticated** — only affects default-branch resolution; if `git symbolic-ref` also fails, default to `main` and note the assumption.
- **Explicit branch name** — if the user names a branch, use that instead of auto-detected default.

## What this skill does not do

- Does not `git checkout` or `git switch` away from the current branch
- Does not delete local or remote branches
- Does not force-pull, rebase, or reset without explicit user instruction
- Does not update git config
