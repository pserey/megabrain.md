# AGENTS.md

## Identity

This repository is a megabrain: a plain-Markdown second brain under git.
The files here are the source of truth for personal context, cross-domain
priorities, and active work. You are a first-class client of this brain:
you read it to answer questions and write it to record what the user asks
you to track.

## The manifest

`megabrain.md` at the repository root is the manifest. Its YAML frontmatter
declares this instance's domains, entity directories and their archetypes,
status vocabularies, field types, integrations, and skills layout. Read it
before acting on anything structural. Never infer structure from directory
listings or prose when the manifest can tell you.

## Dispatch

Match on intent, not exact wording. When a request matches a row, read the
procedure file **in full, in this turn**, before making any tool call or
file write it covers.

| User is asking about... | Read this file first |
|---|---|
| What to do today, daily briefing, planning the day, priorities, "what's on my plate" | `skills/core/briefing.md` |
| Adding a task or note, "add task: X", "remind me to", "track this" | `skills/core/add-item.md` |
| Finishing, completing, cancelling, or being done with an item | `skills/core/complete-item.md` |
| Summarizing or filing an article, paper, or link; a message that is mostly a URL | `skills/core/capture.md` |
| Starting to track something new, adding a domain or entity type, setting up an integration | `skills/core/extend-brain.md` |

## The re-read rule

Always re-read the procedure file in the current turn, even if you read it
earlier in this conversation or in a previous session. Procedures change
between sessions; a remembered procedure is not a substitute for the file.
If no dispatch row matches, fall back to the working rules below — do not
improvise a procedure.

## Working rules

- Read the relevant notes before answering: the entity directories and
  context notes declared in the manifest.
- `domain` is metadata, never a directory. Adding a domain never moves a
  file.
- One entity per file. Filenames are descriptive lowercase kebab-case with
  a `.md` extension; frontmatter keys and controlled values are snake_case
  ASCII English; prose may be any language.
- Every entity note carries `domain` and `date_added`; notes in
  status-bearing archetypes carry `status`. Dates are ISO 8601
  (`YYYY-MM-DD`) in the manifest's timezone. Omit optional keys when
  unknown — never write placeholders or guesses.
- Fail loudly. If you cannot retrieve something you were asked to use — an
  integration is down, a file is missing, a value is unknown — say so
  explicitly. Never substitute an estimate, a remembered value, or an
  inference presented as fact.
- Never create notes from an external system without the user's explicit
  approval of those specific items.
- Preserve user-written content. Do not rewrite prose you did not author,
  and do not modify priorities, statuses, or due dates as a side effect of
  a read-only request such as a briefing or lookup.
- Report the path of every note you create or modify, and the metadata you
  set.
- Write full lines — one line per paragraph or bullet. Do not hard-wrap
  Markdown.

## Version control

- You may commit changes to the **content layer** freely: notes, journals,
  logs, archives.
- You must not commit changes to the **contract layer** — `megabrain.md`,
  `AGENTS.md`, anything in `skills/` — without the user's explicit approval
  in the moment. Leave such changes in the working tree and summarize what
  changed so the user can review and commit.
- When committing, add a trailer identifying the harness actually running
  this session, not a hardcoded name.
