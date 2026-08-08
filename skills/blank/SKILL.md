---
name: blank
description: >-
  Handles a request from a fresh conversational slate, without using prior
  turns, session summaries, remembered preferences, or other chat sessions.
  Use only when the user explicitly invokes /blank <request>.
disable-model-invocation: true
---

# Blank

Answer the request after `/blank` as a standalone prompt.

## Rules

1. Treat only the text after `/blank` as the user's task.
2. Do not use or reference earlier turns, conversation summaries, remembered
   user preferences, prior sessions, transcripts, or retrieved chat history.
3. Do not search conversation history or invoke recall/history tools.
4. Continue to follow system and developer instructions. Use current external
   evidence, such as the present codebase, files, tool results, or web sources,
   when the standalone request requires it.
5. Do not infer omitted subjects, pronouns, constraints, or preferences from
   earlier conversation. Ask a self-contained clarification when the request
   cannot stand on its own.
6. Do not mention prior context or announce that it was ignored unless that is
   necessary to explain a limitation.

If no request follows `/blank`, respond:

```text
Usage: /blank <request>
```

If the request explicitly depends on prior conversation or another session,
ask the user to include the needed context directly in the request.
