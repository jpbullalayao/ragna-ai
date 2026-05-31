---
name: write-docs
description: >-
  Writes concise, token-efficient markdown documentation about a user-specified
  query, function, module, or project. Docs are readable by both humans and
  agents, auto-placed by project architecture, and the user's query can override
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
---

# Write Docs

Writes a `.md` doc explaining the user's query so any agent or human reading it cold gets full context.

Invocation: `/write-docs <query>` — the text after `/write-docs` is the subject and may include overrides.

## Query precedence

The user's query is authoritative. If it conflicts with the defaults below (e.g. asks for exhaustive detail, a specific output path, or a different format), follow the query and skip the conflicting default.

## Content defaults

- Concise but complete — every detail must be relevant; no fluff.
- Cover: what it is, why it exists, key behavior, inputs/outputs, dependencies/relationships, and gotchas.
- Cite real file paths from the codebase.
- Research the codebase before writing; never invent.

## Placement

Find the natural docs home from project architecture:

1. Existing `docs/` or similar documentation directory
2. Sibling `README.md` or `.md` files near the subject
3. The relevant package or module directory

If none is clearly appropriate, default to the repo root or current folder. Filename: kebab-case `*.md` derived from the subject.

## Workflow

### Step 1: Parse query

Extract the subject and any overrides (output path, verbosity, format, scope).

### Step 2: Gather context

Use native CLI and Read only. Run in parallel where possible:

```bash
ls -la
find . -name "<relevant pattern>" -not -path "*/node_modules/*"
grep -r "<topic keywords>" --include="*.ts" --include="*.tsx" --include="*.js" --include="*.py" -l .
```

Read key files (entry points, relevant modules, configs). Cap reads to 3–5 files.

### Step 3: Choose target path

Apply the placement rules above. If the query specifies a path, use it.

### Step 4: Write the doc

Create the markdown file at the chosen path using the content defaults (or query overrides).

### Step 5: Report

Return the created file path and a one-line summary of what was documented.

## Constraints

- No fluff, no time-sensitive phrasing.
- Ground every claim in code or the user's input.
- Query overrides win over defaults.
- Context gathering uses only native CLI (`ls`, `find`, `grep`, `cat`) and `Read`.
