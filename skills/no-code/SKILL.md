---
name: no-code
description: >-
  Answer the user's query with an explanation only — do not write, edit, or
  apply any code changes. Use when the user invokes /no-code <query>, or asks
  for an answer without code changes.
disable-model-invocation: true
---

# No Code

Answer the query after `/no-code` without writing or applying any code.

## Rules

1. Provide your answer as prose. Do not create, edit, or delete any files, and
   do not apply any code changes.
2. Reading files, searching the codebase, and running read-only commands to
   inform your answer is fine.
3. If the answer would naturally involve a fix or implementation, describe the
   approach instead of implementing it.

If no query follows `/no-code`, respond:

```text
Usage: /no-code <query>
```
