---
allowed-tools:
    - Bash(git branch *)
    - Bash(git status *)
    - Bash(git checkout *)
    - Bash(git switch *)
    - Bash(git pull *)
    - Bash(git fetch *)
    - Bash(git push origin --delete *)
    - Bash(git ls-remote *)
    - Bash(git symbolic-ref *)
    - Bash(gh repo view *)
description: Sync the default branch and delete the merged working branch after a PR merge. Use when the user types `/post-merge-cleanup`, asks to "clean up after merging", "pull main and delete this branch", "post-merge cleanup", "delete my feature branch after merge", or otherwise wants to switch to main, pull latest, and remove the branch they were working on.
metadata:
    github-path: skills/post-merge-cleanup
    github-ref: refs/heads/main
    github-repo: https://github.com/jpbullalayao/ragna-ai
    github-tree-sha: 32c0134b74aff885879aee757481ab26b6e1ed17
name: post-merge-cleanup
---
# Post-Merge Cleanup

After a PR merges, sync the default branch and delete the working branch locally and on the remote.

## Workflow

### 1. Gather state

Run in parallel:

```bash
git branch --show-current
git status --porcelain
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || gh repo view --json defaultBranchRef -q .defaultBranchRef.name
```

- `BRANCH` — current branch name.
- `DEFAULT` — default branch (strip `origin/` prefix if present; fall back to `main` if unresolved).

### 2. Guard rails

Stop or ask before mutating:

- **Detached HEAD** (empty `BRANCH`) — stop; tell the user.
- **Already on default branch** — run `git pull --ff-only` only, report done; nothing to delete.
- **Dirty working tree** (`git status --porcelain` non-empty) — stop and ask whether to commit or stash first.

### 3. Sync default branch

```bash
git checkout <DEFAULT>
git pull --ff-only
```

### 4. Delete local branch

```bash
git branch -d <BRANCH>
```

If this fails with "not fully merged" (common after squash/rebase merges), ask the user to confirm force-delete, then:

```bash
git branch -D <BRANCH>
```

### 5. Delete remote branch

Check if the remote branch still exists:

```bash
git ls-remote --exit-code --heads origin <BRANCH>
```

- **Exists** — ask the user to confirm, then `git push origin --delete <BRANCH>`.
- **Already gone** (GitHub auto-deleted on merge) — skip silently.

### 6. Prune stale refs

```bash
git fetch --prune
```

### 7. Report

Return a short summary:

- Default branch synced (`<DEFAULT>`).
- Local branch deleted (`-d` or forced `-D`).
- Remote branch deleted or already absent.
- Stale remote-tracking refs pruned.

## Edge cases

- **`git pull --ff-only` fails** — stop and surface the error; do not force-pull or rebase without explicit user instruction.
- **`gh` not authenticated** — only affects default-branch resolution fallback; if `git symbolic-ref` also fails, default to `main` and note the assumption.
- **Branch name passed explicitly** — if the user names a branch (e.g. "delete `feature/foo`"), use that instead of the current branch, but still require confirmation before `-D` or remote delete.
