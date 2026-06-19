---
name: npm-increment
description: >-
  Analyze changes since the last package version, recommend a semver bump
  (patch/minor/major), and run npm version after user confirmation. Supports
  explicit target versions (e.g. /npm-increment 2.0.0) and re-prompts when the
  user declines the recommendation. Use when the user types /npm-increment,
  asks to "bump the version", "increment package version", "what semver bump",
  "set version to X", or "release a new version".
allowed-tools:
  - "Bash(git log *)"
  - "Bash(git diff *)"
  - "Bash(git status *)"
  - "Bash(git rev-parse *)"
  - "Bash(git tag *)"
  - "Bash(git describe *)"
  - "Bash(git show *)"
  - "Bash(npm version *)"
  - "Read"
  - "AskUserQuestion"
---

# npm-increment

Reads the root `package.json` version, reviews changes since that release, recommends a semver bump, and runs `npm version` after user confirmation. Supports explicit target versions and a re-prompt flow when the user declines the recommendation.

Invocation: `/npm-increment` or `/npm-increment <version>` (e.g. `/npm-increment 2.0.0`).

## When to invoke

Trigger on any of:
- `/npm-increment` or `/npm-increment <version>`
- "bump the version" / "increment package version"
- "what semver bump" / "release a new version"
- "set version to X" / "bump to X"

## Workflow

### Step 0: Parse invocation (optional override)

Extract an explicit target version when the user already knows what they want:

- `/npm-increment 2.0.0`
- `/npm-increment v2.0.0` (strip leading `v`)
- Natural language: "bump to 2.0.0", "set version to 1.5.0-rc.1"

If provided, record as `TARGET_VERSION` and **skip Steps 2–3** (diff analysis and semver classification). Still read `CURRENT_VERSION` from `package.json` for comparison.

Validate `TARGET_VERSION` is a valid semver string (e.g. `1.2.3`, `2.0.0-rc.1`). If invalid, stop with a clear error.

### Step 1: Read current version

Read the root `package.json` `version` field.

- If missing or not a valid semver string, stop with a clear message.
- Record as `CURRENT_VERSION` (e.g. `1.2.3`).

### Step 2: Resolve diff baseline (since last package version)

**Skip this step** when `TARGET_VERSION` was provided at invocation.

Find the git ref that marks when `CURRENT_VERSION` was released:

1. **Primary:** tag `v{CURRENT_VERSION}` (npm's default tag format)
2. **Alternate:** tag `{CURRENT_VERSION}` (no `v` prefix)
3. **Fallback:** most recent semver tag via `git tag -l 'v*' --sort=-v:refname | head -1`
4. **Last resort:** `git log -1 --format=%H -S '"version":' -- package.json`

If primary/alternate tag is missing, **warn explicitly** that `package.json` and git tags are out of sync, state which fallback ref was used, and include that caveat in the recommendation output.

Run in parallel once `BASE_REF` is known:

```bash
git log <BASE_REF>..HEAD --oneline
git diff --stat <BASE_REF>..HEAD
git diff <BASE_REF>..HEAD
```

If the range is empty and no `TARGET_VERSION` was provided, stop: "Nothing to release since `CURRENT_VERSION`." If the user supplied an explicit `TARGET_VERSION`, continue even with an empty diff (they may be re-tagging or correcting version drift).

### Step 3: Determine semver bump

**Skip this step** when `TARGET_VERSION` was provided at invocation.

Apply [Semantic Versioning](https://semver.org/) using **highest applicable bump wins**:

| Bump | Signals (any one is sufficient) |
|------|----------------------------------|
| **major** | `BREAKING CHANGE:` in commit body; Conventional Commit `!` after type (e.g. `feat!:`); removed/renamed public exports or APIs; changed function signatures without backward compatibility; dependency major upgrades that alter consumer-facing behavior |
| **minor** | `feat:` commits; new backward-compatible features, endpoints, props, or config options |
| **patch** | `fix:` commits; bug fixes, security patches, internal refactors, `chore:`, `docs:`, `style:`, `test:` with no user-facing feature additions |

**Analysis order:**

1. Scan `git log <BASE_REF>..HEAD` for Conventional Commit prefixes and `BREAKING CHANGE` footers
2. Skim `git diff` for API surface changes (exports, public types, route handlers, CLI flags)
3. Pick the **maximum** bump level found; default to **patch** if changes are only internal/non-breaking

Compute `NEXT_VERSION` — e.g. `1.2.3` + minor → `1.3.0`.

**Pre-release note:** if `CURRENT_VERSION` contains a prerelease suffix (e.g. `1.2.0-beta.1`), flag in output that `npm version patch` may strip the prerelease suffix without incrementing. Recommend an explicit version string if that behavior is wrong for the user's intent.

### Step 4: Present recommendation (mandatory before mutating)

Do **not** run `npm version` until the user explicitly confirms (yes / confirm / proceed).

#### Recommended bump (default flow)

```markdown
## Version recommendation

| | |
|---|---|
| **Current version** | `1.2.3` |
| **Recommended bump** | **minor** → `1.4.0` |
| **Diff range** | `v1.2.3..HEAD` (N commits, M files) |

**Why minor:** <1–3 concise sentences citing commit subjects and/or diff highlights. Mention if any major signals were checked and not found.>

Proceed with `npm version minor`? (creates commit + `v1.4.0` tag)

You can also reply with a different bump (`patch` / `minor` / `major`) or an explicit version (e.g. `2.0.0`).
```

#### Explicit version (override at invocation)

When `TARGET_VERSION` was provided, use a shorter template:

```markdown
## Version confirmation

| | |
|---|---|
| **Current version** | `1.2.3` |
| **Target version** | `2.0.0` |

Proceed with `npm version 2.0.0`? (creates commit + `v2.0.0` tag)
```

#### When the user declines ("no" / "not yet" / disagrees)

Do **not** stop immediately. Re-prompt with structured options (use `AskUserQuestion` when available):

1. **Accept a different bump** — user says `patch`, `minor`, or `major`; recompute next version and confirm again
2. **Specify a custom version** — user provides e.g. `1.5.0-rc.1`; validate semver, set `TARGET_VERSION`, confirm again
3. **Cancel** — user says `cancel` / `stop` / clearly wants no changes; exit with no mutations

Loop confirmation until the user accepts or cancels. Never run `npm version` on a declined recommendation without a new explicit choice.

### Step 5: Apply bump on confirmation

**Pre-flight guards** (stop if any fail):

```bash
git status --porcelain
git rev-parse --is-inside-work-tree
```

Working tree must be clean — `npm version` fails on a dirty tree. Repo must be inside a git work tree for default commit+tag behavior.

From repo root, run **one** of:

```bash
npm version <patch|minor|major>
npm version <TARGET_VERSION>
```

- Do **not** pass `--no-git-tag-version` (default: update `package.json`, create commit + `vX.Y.Z` tag).
- Do **not** pass `--force` unless the user explicitly requests it after seeing the dirty-tree error.
- Honor the user's final choice over the agent's recommendation.
- If `TARGET_VERSION` equals `CURRENT_VERSION`, warn before proceeding — `npm version` will fail unless `--allow-same-version` is passed; only use that flag if the user explicitly confirms after the warning.

After success, report:

- New version from `package.json`
- Git tag created (e.g. `v1.4.0`)
- Remind user to `git push --follow-tags` if they want the tag on remote (npm does not push by default)

## Edge cases

| Scenario | Behavior |
|----------|----------|
| No root `package.json` | Stop — root-only v1 |
| Not a git repository | Stop before `npm version` — cannot create tag/commit |
| Dirty working tree | Stop before `npm version`; tell user to commit/stash first |
| No tag for current version | Warn + use fallback ref; note uncertainty in recommendation |
| Empty diff since release | Stop — unless explicit `TARGET_VERSION` was provided |
| `pnpm` / `yarn` repo | Still use `npm version`; warn if lockfile may not match package manager |
| Pre-release versions | Surface npm prerelease stripping behavior |
| `npm version` fails (hooks) | Surface stderr; do not retry with `--force` without user consent |
| User overrides bump | Run their choice, not the recommendation |
| User provides explicit version at invocation | Skip diff analysis; confirm then `npm version <TARGET_VERSION>` |
| User says "no" to recommendation | Re-prompt: different bump, custom version, or cancel |
| `TARGET_VERSION` equals `CURRENT_VERSION` | Warn; only proceed with `--allow-same-version` if user confirms |
| Invalid custom version string | Reject with error; ask for a valid semver |

## Examples

### Recommended bump

Current version `1.2.3`, tag `v1.2.3` exists. Commits since:

- `feat(api): add pagination to list endpoint`
- `fix(ui): correct empty state copy`

Recommendation: **minor** → `1.3.0` (new feature, no breaking changes).

### Explicit version at invocation

User runs `/npm-increment 2.0.0`. Current version `1.3.0`.

Skip diff analysis. Present confirmation table showing `1.3.0` → `2.0.0`. On confirm, run `npm version 2.0.0`.

### Decline and override

Agent recommends **minor** → `1.4.0`. User says "no, make it a patch."

Recompute: **patch** → `1.3.1`. Present updated confirmation. On confirm, run `npm version patch`.
