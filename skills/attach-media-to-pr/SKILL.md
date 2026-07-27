---
name: attach-media-to-pr
description: Host local image/media files on GitHub and embed them inline in a pull request or issue body (or comment) so they render for anyone with repo access — including private repos. Use when the user asks to "attach a screenshot to the PR", "add this image to the pull request", "embed media in the PR body", or when another skill (e.g. submit-pull-request) has captured media that needs to be attached to a PR. Takes file paths plus a PR/issue number; handles hosting, URL construction, and the body edit.
---

# Attach Media to PR

Host local media files in the repository via the GitHub Contents API and embed them inline in a PR or issue. No worktrees, no branch checkouts, no local git state — every operation is a `gh api` call, so it is safe from any directory, a dirty tree, a worktree agent, or CI.

## Why this design

GitHub renders markdown images through its anonymous Camo proxy, which cannot read private repos — so `raw.githubusercontent.com` embeds 404. There is also no public API for the web UI's drag-and-drop upload (`user-attachments`). The reliable path is repo-hosted media referenced by a SHA-pinned `github.com/.../blob/...?raw=true` URL: github.com serves it directly and the viewer's own session authenticates, so it renders inline for any collaborator.

## Inputs

- **Files**: one or more local image/media paths (png, jpg, gif, mp4 under ~100MB).
- **Target**: a PR number (default) or issue number, and the repo (default: current directory's repo).
- **Placement**: which section of the body to embed under (e.g. "After"), or a new comment. Default: append to the end of the body.
- **Label**: alt/label text per image (e.g. "After"). Default: the filename stem.

## Workflow

1. **Resolve repo and owner.** `gh repo view --json nameWithOwner -q .nameWithOwner`.

2. **Ensure the `pr-assets` branch exists.** Check with `gh api repos/{owner}/{repo}/branches/pr-assets` — on 404, create it from the default branch head:
   - `default_sha=$(gh api repos/{owner}/{repo}/git/ref/heads/{default-branch} -q .object.sha)`
   - `gh api -X POST repos/{owner}/{repo}/git/refs -f ref=refs/heads/pr-assets -f sha=$default_sha`
   The branch is never merged and holds only PR media; never add code to it.

3. **Upload each file with the Contents API.** Base64-encode the file first (pre-compute into a variable or temp file — no inline `$()` in the final command), then:
   - `gh api -X PUT repos/{owner}/{repo}/contents/pr-media/<number>/<filename> -f branch=pr-assets -f message="Add PR <number> media" -f content=@<base64-file>`
   - If the path already exists (422), fetch its blob `sha` via `gh api .../contents/pr-media/<number>/<filename>?ref=pr-assets -q .sha` and retry the PUT with `-f sha=<blob-sha>` to overwrite.
   - Capture the **commit SHA** from each response (`.commit.sha`); the last upload's commit SHA covers all files.

4. **Build SHA-pinned embed URLs.** For each file:
   `![<label>](https://github.com/<owner>/<repo>/blob/<commit-sha>/pr-media/<number>/<filename>?raw=true)`
   Always pin to the commit SHA, never the branch name, so later uploads can never break existing embeds.

5. **Embed.**
   - **Body section** (default): fetch the current body (`gh pr view <number> --json body -q .body`), insert the image line under the requested section heading (after any HTML comment hint, preserving it), write the result to a temp file with the Write tool, and `gh pr edit <number> --body-file <file>`. Never overwrite unrelated body content; this is an insert, not a rewrite. For issues use `gh issue edit`.
   - **New comment**: `gh pr comment <number> --body-file <file>`.

6. **Report** the embed URL(s) and remind the user to eyeball the PR, since inline rendering on private repos authenticates via the viewer's browser session and cannot be verified from the CLI.

## Failure handling

Best-effort, never destructive: on any failure (no `gh` auth, no push/write permission, API error), stop, leave the PR body untouched, and report the local file paths so the user can drag them in manually. If the repo is public, `raw.githubusercontent.com` URLs also work, but the SHA-pinned blob URL works everywhere — always prefer it.

## What this skill does NOT do

- **Capture.** Screenshots/recordings are produced by the caller (e.g. a project's browser-verification skill). This skill starts from files on disk.
- **Official `user-attachments` uploads.** Those require the web UI; if the user explicitly wants them, they must drag the reported files in manually (or drive a logged-in browser).
