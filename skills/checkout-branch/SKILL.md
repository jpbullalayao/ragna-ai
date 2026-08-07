---
name: checkout-branch
description: >-
  Check out a git branch on the local checkout, handling every edge case
  automatically: branches checked out in another worktree, remote-only
  branches, ambiguous multi-remote branches, and uncommitted local changes.
  Use when the user types /checkout-branch <branch>, or asks to
  "check out <branch>", "switch to <branch>", or "move to <branch>".
allowed-tools:
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

### 1. Fast path — just check out

```bash
git checkout <BRANCH>
```

If this succeeds (Git also auto-creates a tracking branch when exactly one remote has the branch), skip to step 3. If it fails, match the error to a case in step 2.

### 2. Remediate by failure case

**Branch is checked out in another worktree** — error mentions "already used by worktree" / "already checked out". Release it, then retry:

```bash
git worktree list --porcelain   # find the worktree path holding <BRANCH>
git worktree remove <worktree-path>
git checkout <BRANCH>
```

If the worktree has uncommitted or untracked changes, do NOT force-remove — report the dirty worktree and stop unless the user confirms `git worktree remove --force`. If the worktree path no longer exists on disk, run `git worktree prune` instead of `remove`.

**Local changes would be overwritten** — auto-stash and retry:

```bash
git stash push -u -m "checkout-branch: auto-stash before switching to <BRANCH>"
git checkout <BRANCH>
git stash pop
```

If the pop conflicts, leave the stash intact and report the conflict for the user to resolve.

**Branch not found** — the branch has no local ref and no remote-tracking ref yet. Fetch and retry once:

```bash
git fetch --all --prune
git checkout <BRANCH>
```

If it still fails because multiple remotes have the branch, check out with an explicit remote (prefer `origin`; otherwise ask the user):

```bash
git checkout --track <remote>/<BRANCH>
```

If the branch exists nowhere after fetching, report that and stop — do not create a new branch unless the user asks.

**Already on the branch** — Git says so; just confirm to the user and stop.

### 3. Report

Return a short summary:

- Branch checked out and its current commit SHA (from the checkout output)
- Which case applied, if any remediation was needed
- Whether changes were auto-stashed and restored
- Any action needing user follow-up (dirty worktree, stash conflict)
