---
name: checkout-branch
description: >-
  Check out a git branch on the local checkout, handling every edge case
  automatically: branches checked out in another worktree, remote-only
  branches, and uncommitted local changes.
  Use when the user types /checkout-branch <branch>, or asks to
  "check out <branch>", "switch to <branch>", or "move to <branch>".
allowed-tools:
  - "Bash(git -C *)"
  - "Bash(git checkout *)"
  - "Bash(git fetch *)"
  - "Bash(git stash *)"
  - "Bash(git worktree *)"
  - "Bash(git for-each-ref *)"
---

# Checkout Branch

Check out the requested branch on the local (main) checkout, resolving any obstacle — worktrees, remote-only branches, uncommitted changes — automatically via Git.

## Input

The branch name is provided as the argument: `/checkout-branch <branch>`. If no branch is given, ask the user which branch to check out.

## Workflow

Optimize for the common case: attempt the checkout immediately and remediate only if it fails. No upfront state-gathering or fetching.

### 0. Resolve the main checkout

The session may be running inside a git worktree (e.g. `.claude/worktrees/<name>`), but the branch must always land on the main local checkout. Resolve its path first:

```bash
MAIN=$(git worktree list | awk 'NR==1 { print $1 }')
```

Run every checkout and remediation command below against it with `git -C "$MAIN"` (or `cd "$MAIN"` first), so the skill behaves identically whether the session runs from the main checkout or from a worktree.

### 1. Fast path — just check out

```bash
git -C "$MAIN" checkout <BRANCH>
```

If this succeeds (Git also auto-creates a tracking branch when exactly one remote has the branch), skip to step 3. If it fails, match the error to a case in step 2.

### 2. Remediate by failure case

**Branch is checked out in another worktree** — error mentions "already used by worktree" / "already checked out". Release it, then retry:

```bash
git -C "$MAIN" worktree list --porcelain   # find the worktree path holding <BRANCH>
git -C "$MAIN" worktree remove <worktree-path>
git -C "$MAIN" checkout <BRANCH>
```

If the worktree holding the branch is the session's own current worktree, do NOT remove it — instead switch that worktree off the branch (`git checkout main`, or `git checkout --detach` if `main` is taken), but only if its tree is clean; otherwise report the dirty tree and stop. Then check out the branch on `$MAIN`.

If the worktree has uncommitted or untracked changes, do NOT force-remove — report the dirty worktree and stop unless the user confirms `git worktree remove --force`. If the worktree path no longer exists on disk, run `git worktree prune` instead of `remove`.

**Local changes would be overwritten** — auto-stash and retry:

```bash
git -C "$MAIN" stash push -u -m "checkout-branch: auto-stash before switching to <BRANCH>"
git -C "$MAIN" checkout <BRANCH>
git -C "$MAIN" stash pop
```

If the pop conflicts, leave the stash intact and report the conflict for the user to resolve.

**Branch not found** — the branch has no local ref and no remote-tracking ref yet. Fetch and retry once:

```bash
git -C "$MAIN" fetch --all --prune
git -C "$MAIN" checkout <BRANCH>
```

If the branch exists nowhere after fetching, report that and stop — do not create a new branch unless the user asks. Surface any other checkout error as-is.

**Already on the branch** — Git says so; just confirm to the user and stop.

### 3. Report

Return a short summary:

- Branch checked out, which checkout it landed on (the `$MAIN` path), and its current commit SHA (from the checkout output)
- Which case applied, if any remediation was needed
- Whether changes were auto-stashed and restored
- Any action needing user follow-up (dirty worktree, stash conflict)
