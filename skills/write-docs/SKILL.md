---
name: write-docs
description: >-
  Writes concise, token-efficient markdown documentation about any subject in
  the user's query — a topic, function, module, project, or online material
  including provided URLs. Docs are readable by both humans and agents,
  auto-placed by project architecture, and the user's query can override
  defaults. Use when the user invokes /write-docs, or asks to "document this",
  "write docs for", or "write documentation about".
allowed-tools:
  - "Bash(grep *)"
  - "Bash(find *)"
  - "Bash(ls *)"
  - "Bash(cat *)"
  - "Read"
  - "Write"
  - "Edit"
  - "WebSearch"
  - "WebFetch"
---

# Write Docs

Writes a `.md` doc explaining the user's query so any agent or human reading it cold gets full context. The subject may be local project material, online material, or both.

Invocation: `/write-docs <query>` — the text after `/write-docs` is the subject and may include overrides.

## Query precedence

The user's query is authoritative. If it conflicts with the defaults below (e.g. asks for exhaustive detail, a specific output path, or a different format), follow the query and skip the conflicting default.

## Source modes

Determine what the query is asking to document:

- **Local** — project code or files in the working tree (a function, module, config, etc.).
- **Online** — a topic to research on the web, or one or more URLs provided in the query.
- **Mixed** — the query references both local and online material; draw from both.

## Content defaults

- Concise but complete — every detail must be relevant; no fluff.
- Cover: what it is, why it exists, key behavior, inputs/outputs, dependencies/relationships, and gotchas.
- Cite real sources — file paths for local subjects, URLs for online subjects.
- State each detail once — don't repeat the same fact, definition, or explanation across sections; cross-reference instead. A brief overview line is fine, but don't re-explain it later.
- Research before writing; never invent.

## Placement

Find the natural docs home from project architecture:

1. Existing `docs/` or similar documentation directory
2. Sibling `README.md` or `.md` files near the subject
3. The relevant package or module directory

If none is clearly appropriate — including purely online subjects with no related local folder — default to the repo root or current folder. Filename: kebab-case `*.md` derived from the subject.

## Workflow

### Step 1: Parse query

Extract the subject, source mode (local, online, or mixed), and any overrides (output path, verbosity, format, scope, URLs).

### Step 2: Gather context

Choose the approach based on source mode. Cap all research to a few authoritative sources.

**Online (URLs provided):** Fetch each URL with `WebFetch`.

**Online (topic, no URLs):** Use `WebSearch`, then `WebFetch` the most relevant results.

**Local:** Use native CLI and `Read`. Run in parallel where possible:

```bash
ls -la
find . -name "<relevant pattern>" -not -path "*/node_modules/*"
grep -r "<topic keywords>" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" -l .
```

Read key files (entry points, relevant modules, configs). Cap reads to 3–5 files.

**Mixed:** Combine the online and local steps above.

### Step 3: Choose target path

Apply the placement rules above. If the query specifies a path, use it.

### Step 4: Write the doc

Create the markdown file at the chosen path using the content defaults (or query overrides).

### Step 5: Report

Return the created file path and a one-line summary of what was documented.

## Constraints

- No fluff, no time-sensitive phrasing.
- Ground every claim in the codebase, fetched web content, or the user's input.
- No redundant restatement — each detail appears in exactly one place.
- Query overrides win over defaults.
