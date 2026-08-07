---
name: checkout-branch
description: >-
  Check out a git branch on the local checkout, handling every edge case
  automatically: branches checked out in another worktree (removes the worktree
  and checks out the branch locally), remote-only branches (creates a tracking
  branch), ambiguous multi-remote branches, and detached-HEAD states. Use when
  the user types /checkout-branch <branch>, or asks to "check out <branch>",
  "switch to <branch>", or "move to <branch>".
allowed-tools:
  - "Bash(git status *)"
  - "Bash(git branch *)"
  - "Bash(git checkout *)"
  - "Bash(git switch *)"
  - "Bash(git fetch *)"
  - "Bash(git stash *)"
  - "Bash(git rev-parse *)"
  - "Bash(git worktree *)"
  - "Bash(git ls-remote *)"
  - "Bash(git for-each-ref *)"
---

# Checkout Branch

Check out the requested branch on the local (main) checkout, resolving any obstacle — worktrees, remote-only branches, uncommitted changes — automatically via Git.

## Input

The branch name is provided as the argument: `/checkout-branch <branch>`. If no branch is given, ask the user which branch to check out.

## Workflow

### 1. Gather state

Run in parallel:

```bash
git status --porcelain
git branch --show-current
git fetch --all --prune
```

Then determine where the branch exists:

```bash
git for-each-ref "refs/heads/<BRANCH>" "refs/remotes/*/<BRANCH>"
git worktree list --porcelain
```

### 2. Protect uncommitted work

If `git status --porcelain` shows changes and the checkout could touch those files, stash first and remember to restore:

```bash
git stash push -u -m "checkout-branch: auto-stash before switching to <BRANCH>"
```

Only stash when a plain checkout would fail or overwrite changes — try the checkout first; stash on failure, then retry.

### 3. Resolve the branch and check it out

Handle whichever case applies:

**Already on the branch** — report and stop (still pull no updates; just confirm).

**Branch is checked out in a worktree** — `git worktree list --porcelain` shows the branch attached to another worktree path. Git refuses to check out a branch active in another worktree, so release it first:

```bash
git worktree remove <worktree-path>
# If the worktree has uncommitted/untracked changes, do NOT force-remove.
# Report the dirty worktree to the user and stop unless they confirm; on
# confirmation use: git worktree remove --force <worktree-path>
git checkout <BRANCH>
```

If the worktree path no longer exists on disk, use `git worktree prune` instead of `remove`, then check out.

**Local branch exists (no worktree conflict)**:

```bash
git checkout <BRANCH>
```

**Branch exists only on one remote**:

```bash
git checkout --track <remote>/<BRANCH>
```

**Branch exists on multiple remotes** — prefer `origin`; otherwise ask the user which remote to track.

**Branch not found anywhere** — report that the branch does not exist locally or on any remote and stop. Do not create a new branch unless the user asks.

### 4. Restore stashed work

If step 2 stashed changes, restore them:

```bash
git stash pop
```

If the pop conflicts, leave the stash intact, report the conflict, and let the user resolve it.

### 5. Report

Return a short summary:

- Branch checked out and its current commit SHA
- Which case applied (local, remote-tracking created, worktree released, etc.)
- Whether changes were auto-stashed and restored
- Any action needing user follow-up (dirty worktree, stash conflict)
