---
name: update-with-main
description: >-
  Merge the latest remote default branch (main, master, etc.) into a given
  branch, hand any merge conflicts to the harness's conflict-resolution skill,
  and push the result. Use when the user types /update-with-main [<branch>], or
  asks to "update <branch> with main", "merge main into <branch>", "bring my
  branch up to date with main", or "sync my branch with the default branch".
allowed-tools:
  - "Bash(git -C *)"
  - "Bash(git checkout *)"
  - "Bash(git branch *)"
  - "Bash(git status *)"
  - "Bash(git fetch *)"
  - "Bash(git merge *)"
  - "Bash(git add *)"
  - "Bash(git commit *)"
  - "Bash(git push *)"
  - "Bash(git diff *)"
  - "Bash(git worktree *)"
  - "Bash(git symbolic-ref *)"
  - "Bash(gh repo view *)"
---

# Update With Main

Merge the latest `origin/<DEFAULT>` into the target branch with a merge commit (never a rebase), resolve conflicts through the harness's conflict-resolution skill, and push.

## Input

`/update-with-main <branch>`. If no branch is given, use the current branch. If the target is the default branch itself (or HEAD is detached and no branch was given), ask the user which branch to update.

## Workflow

### 1. Resolve the default branch and fetch

```bash
git symbolic-ref --short refs/remotes/origin/HEAD 2>/dev/null || gh repo view --json defaultBranchRef -q .defaultBranchRef.name
```

`DEFAULT` is the result with any `origin/` prefix stripped; fall back to `main` if unresolved. Then fetch so the merge uses the remote's latest state, not a stale local ref:

```bash
git fetch origin
```

### 2. Pick the working tree

A merge needs a checkout of `<BRANCH>`. Find where it lives:

```bash
git worktree list --porcelain
```

- **Checked out in a worktree** (including the current one) — run every command below in that worktree with `git -C <path>`.
- **Not checked out anywhere** — use the current checkout. Confirm it is clean (see below), then run `git checkout <BRANCH>`; Git creates a local tracking branch automatically when the branch exists only on `origin`. If the checkout fails because the branch exists nowhere, report that and stop.

Call the chosen checkout `<WT>` from here on. It must be clean (`git -C <WT> status --porcelain` empty) before any checkout or merge. If it is not, report the dirty files and stop — never stash or discard someone's changes to make room for a merge.

### 3. Sync with the branch's own remote

If `<BRANCH>` has an upstream, bring in any commits that exist only on the remote first, so the later push is not rejected:

```bash
git -C <WT> merge --ff --no-edit @{u}
```

- Behind → fast-forwards (`--ff` overrides a `merge.ff=false` config, so no needless merge commit is created).
- Level or ahead → `Already up to date.`; nothing changes.
- Diverged → creates a merge commit combining the local and remote commits. If it conflicts, resolve them as described in step 5, then continue to step 4.

### 4. Merge

```bash
git -C <WT> merge --no-edit origin/<DEFAULT>
```

- `Already up to date.` — the branch already contains the latest default branch. If step 3 created a merge commit, go to step 6 to push it; otherwise report that and stop.
- Clean merge — Git creates the merge commit; skip to step 6.
- Conflicts — go to step 5.

### 5. Resolve conflicts

**Use the harness's conflict-resolution skill.** Check the skills available in the current session for one dedicated to resolving merge conflicts. If one exists, invoke it, passing the conflicted files from the merge output and stating which merge produced them (`origin/<BRANCH>` or `origin/<DEFAULT>` into `<BRANCH>`). Follow that skill's process in full, including any plan-approval step it requires — do not resolve the conflicts yourself first.

**Only if no such skill exists**, resolve the conflicts directly.

Either way, stage the resolved files, confirm no conflict markers were left behind, then finish the merge:

```bash
git -C <WT> diff --cached --check   # must report no conflict markers
git -C <WT> commit --no-edit        # Git refuses while any file is still unmerged
```

If the conflicts cannot be resolved with confidence, leave the merge in progress, report the remaining files, and ask the user how to proceed. Never run `git merge --abort` without the user's approval, since it throws away resolution work.

### 6. Push

```bash
git -C <WT> push -u origin <BRANCH>
```

Never force-push. If the push is rejected, report the error and stop.

### 7. Report

Return a short summary:

- Branch updated, the worktree path it was merged in, and the default branch merged (`origin/<DEFAULT>` with its SHA)
- Whether remote commits on `<BRANCH>` were brought in first (fast-forward or merge commit)
- Result: already up to date, clean merge, or merged with conflicts (list the files and the skill used to resolve them)
- New HEAD SHA and whether it was pushed
- Anything left for the user (dirty tree, unresolved conflicts, rejected push)
