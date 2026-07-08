---
name: update-skills
description: >-
  Update globally installed agent skills from jpbullalayao/ragna-ai. Use when
  the user types /update-skills, asks to "update skills", "update my skills",
  "refresh skills", "sync skills", or wants to pull the latest skill definitions
  from the ragna-ai repo.
allowed-tools:
  - "Bash(cd ~)"
  - "Bash(npx skills *)"
---

# Update Skills

Run the following commands to update my local skills:

```
cd ~
npx skills add jpbullalayao/ragna-ai
```

## When to invoke

Trigger on any of:

- `/update-skills`
- "update skills" / "update my skills"
- "refresh skills" / "sync skills"
- "pull latest skills" / "install latest skills"

## Workflow

Run these commands sequentially from the home directory:

```bash
cd ~
npx skills add jpbullalayao/ragna-ai
```

This installs or updates all skills from the ragna-ai repo into the global skills location.

## Constraints

- This updates **global** skills only — do not modify the ragna-ai repo workspace.
- Do **not** commit, push, or create a branch.
- Do **not** run any git operations as part of this workflow.

## Report

Return a short summary of the CLI output: which skills were added or updated, or any errors from the command.
