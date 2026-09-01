---
name: update-pr-context
description: >-
  Review every commit and the full diff of the current branch's PR (or a
  user-provided branch/PR number), compare them against the PR's existing
  title and description, and rewrite any content that has gone stale —
  claims about behavior that no longer match the code, missing changes,
  removed changes still described, outdated test plan steps, or a title that
  no longer summarizes the work. Use when the user types
  /update-pr-context [<branch>|<PR#>], or asks to "update the PR
  description", "refresh the PR body", "sync the PR with the latest
  commits", or "is my PR description still accurate".
allowed-tools:
  - "Bash(gh *)"
  - "Bash(git *)"
---

# Update PR Context

Reads all commits and the complete diff of a pull request, checks the PR's
title and description against what the code actually does now, and edits
only the parts that are stale. Accurate content is left word-for-word.

## Workflow

### Step 1: Resolve the target PR

- No argument → current branch: `gh pr view --json number,title,body,url,state,headRefName,baseRefName`
- Argument is a branch name → `gh pr view <branch> --json ...`
- Argument is a number → `gh pr view <number> --json ...`

If no PR is found, tell the user and stop. If the PR is `MERGED`, tell the
user and stop. If `CLOSED`, warn and ask whether to continue.

Store: `PR_NUMBER`, `TITLE`, `BODY`, `HEAD_BRANCH`, `BASE_BRANCH`, `PR_URL`.

### Step 2: Gather the commits and full diff

```bash
git fetch origin BASE_BRANCH HEAD_BRANCH
git log origin/BASE_BRANCH..origin/HEAD_BRANCH --format='%h %s%n%b'   # every commit, subject + body
git diff origin/BASE_BRANCH...origin/HEAD_BRANCH --stat               # file-level overview
git diff origin/BASE_BRANCH...origin/HEAD_BRANCH                      # full diff
```

Use the remote refs so the review reflects what reviewers see on GitHub, not
unpushed local work. If the local branch is ahead of the remote, tell the
user the description will reflect the pushed state only.

Read the whole diff, not just the stat. For large diffs, read it file by
file, but do not skip files — a stale claim often hides in a file the commit
messages never mention.

Also check whether the PR body was previously refreshed: the last commit
mentioned in the body, if any, tells you what the description was written
against. Later commits are the most likely source of drift.

### Step 3: Build the ground truth

From the commits and diff, write down for yourself (not for the user yet):

- What problem the change solves, as evidenced by the code
- The mechanism used to solve it
- Every user-visible or system-visible behavior change
- Anything that was added, removed, or renamed (files, flags, endpoints,
  env vars, dependencies, migrations)
- What is verifiable, and how (commands, UI flows)

### Step 4: Compare against the title and body

Go through the existing description section by section (whatever sections
it has — do not impose a template it did not use). For each sentence or
bullet, classify it:

- **Accurate** — still true of the diff. Keep verbatim.
- **Stale** — describes behavior, files, names, or approach that the diff no
  longer matches (e.g. a helper renamed, a flag removed, an approach
  replaced by a later commit). Rewrite.
- **Missing** — a meaningful change in the diff that the description does
  not mention at all. Add it in the section where it belongs.
- **Obsolete** — describes something that was reverted or dropped from the
  branch. Remove it.

Then check the title: does it still name the primary change? If later
commits shifted the scope (a fix became a refactor, one feature became two),
rewrite the title. Keep the repo's title convention (Conventional Commits
prefix if the existing title or recent commits use one) and stay under 70
characters.

Test plan / verification sections deserve extra care: a step that references
a removed UI element, a renamed command, or a behavior that changed is stale
even if the rest of the body is fine. Add steps for new behavior that has no
coverage in the plan. Preserve the checked/unchecked state of existing
checkboxes that remain valid.

If **nothing** is stale, missing, or obsolete, tell the user "PR #N title and
description are up to date with the N commits on the branch" and stop. Do
not rewrite for style.

### Step 5: Report the changes before applying

Output a concise summary:

```
## PR Context Review — PR #<number> (<N> commits, <M> files)

### Title
- Keep: `<current title>`            (or)
- Change: `<current>` → `<new>` — <one-line reason>

### Description
1. <Section> — <stale/missing/obsolete>: <one-line what and why>
2. ...
```

One line per change. Do not paste the full new body here.

Proceed directly to applying the edits — do not wait for approval unless the
user asked to review first.

### Step 6: Apply the edits

Write the full updated body to a temp file and update the PR:

```bash
gh pr edit PR_NUMBER --title "<new title>" --body-file <tmpfile>
```

Omit `--title` if the title is unchanged. Rules for the new body:

- Preserve the existing structure, headings, order, and voice.
- Preserve untouched sentences exactly — no incidental rewording.
- Preserve HTML comments, placeholders, media embeds, links, and ticket
  references. Never remove an image or recording the author pasted in.
- Preserve the checked state of test plan checkboxes that remain valid.
- Do not add sections the body did not have unless a missing change has no
  sensible home; then add the smallest section that fits.
- Do not append changelogs, "updated by" notes, or commit lists.

### Step 7: Output summary

```
Updated PR #<number>: <title changed|title unchanged>, <K> description edit(s)
  • <one line per edit>
<PR URL>
```

## Constraints

- **`gh` auth is required.** Run `gh auth status` first; if unauthenticated,
  tell the user to run `gh auth login` and stop.
- **Always report the changes (Step 5) before editing the PR.**
- **Edit only stale, missing, or obsolete content.** Accurate text stays
  verbatim, even if you would have phrased it differently.
- **Never invent behavior.** Every claim in the updated description must be
  traceable to the diff or a commit message.
- **Never change code, commit, or push.** This skill edits the PR title and
  body only.
- **Never hardcode PR numbers, repos, or branch names** — derive everything
  from `gh`/`git` output.
