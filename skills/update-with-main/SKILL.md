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
  - "Bash(git merge-base *)"
  - "Bash(git rev-parse *)"
  - "Bash(git rev-list *)"
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

`DEFAULT` is the result with any `origin/` prefix stripped; fall back to `main` if unresolved. Then fetch both sides so the merge uses the remote's latest state, not a stale local ref:

```bash
git fetch origin <DEFAULT> <BRANCH>
```

If `<BRANCH>` does not exist on `origin` (never pushed), fetch only `<DEFAULT>`. If it exists neither locally nor on `origin`, report that and stop.

### 2. Pick the working tree

A merge needs a checkout of `<BRANCH>`. Find where it lives:

```bash
git worktree list --porcelain
```

- **Checked out in a worktree** (including the current one) — run every command below in that worktree with `git -C <path>`.
- **Not checked out anywhere** — check it out in the current checkout: invoke `/checkout-branch <BRANCH>` if that skill is available, otherwise `git checkout <BRANCH>`. Call this checkout `<WT>` from here on.

The working tree must be clean (`git -C <WT> status --porcelain` empty). If it is not, report the dirty files and stop — never stash or discard someone's changes to make room for a merge.

### 3. Sync with the branch's own remote

If `<BRANCH>` has an upstream, bring the local branch level with it first so the later push is not rejected:

```bash
git -C <WT> rev-list --left-right --count <BRANCH>...@{u}
```

- Behind only → `git -C <WT> merge --ff-only @{u}`.
- Ahead only or level → continue.
- Diverged (both counts non-zero) → report it and stop; reconciling local and remote history is the user's call.

### 4. Check whether a merge is needed

```bash
git -C <WT> merge-base --is-ancestor origin/<DEFAULT> <BRANCH>
```

Exit code `0` means the branch already contains the latest default branch — report "already up to date" and stop.

### 5. Merge

```bash
git -C <WT> merge --no-edit origin/<DEFAULT>
```

A clean merge creates the merge commit; skip to step 7. If Git reports conflicts, go to step 6.

### 6. Resolve conflicts

List the conflicted files:

```bash
git -C <WT> diff --name-only --diff-filter=U
```

**Use the harness's conflict-resolution skill.** Check the available skills list for one dedicated to resolving merge conflicts (e.g. `resolve-conflicts`). If one exists, invoke it via the Skill tool, passing the conflicted file list and stating that the conflicts come from merging `origin/<DEFAULT>` into `<BRANCH>`. Follow that skill's process in full, including any plan-approval step it requires — do not resolve the conflicts yourself first.

**Only if no such skill exists**, resolve conflicts directly:

- Read both sides of each hunk and preserve the intent of both changes; keep both when they do not contradict (imports, tests, config entries).
- Regenerate lock files and other generated files with the project's tooling rather than hand-merging them.
- When the right resolution is unclear, show the user the options and ask.

Either way, before committing confirm that nothing is left unresolved:

```bash
git -C <WT> diff --name-only --diff-filter=U   # must be empty
git -C <WT> diff --check                        # must report no conflict markers
```

Then stage the resolved files and finish the merge with `git -C <WT> commit --no-edit`.

If the conflicts cannot be resolved with confidence, leave the merge in progress, report the remaining files, and ask the user how to proceed. Never run `git merge --abort` without the user's approval, since it throws away resolution work.

### 7. Push

```bash
git -C <WT> push               # branch already has an upstream
git -C <WT> push -u origin <BRANCH>   # no upstream yet
```

Never force-push. If the push is rejected, report the error and stop.

### 8. Report

Return a short summary:

- Branch updated, the worktree path it was merged in, and the default branch merged (`origin/<DEFAULT>` with its SHA)
- Result: already up to date, clean merge, or merged with conflicts (list the files and the skill used to resolve them)
- New HEAD SHA and whether it was pushed
- Anything left for the user (dirty tree, diverged branch, unresolved conflicts, rejected push)
