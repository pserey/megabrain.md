# megabrain

A megabrain is a git repository of plain Markdown files that you keep as a
second brain, and that AI agents read and write as first-class clients. This
repository is the reference instance: a minimal, conforming template you
fork to start your own.

## Start your own

1. Create a repository from this template (or fork it).
2. Open `megabrain.md` — the manifest. Set your `timezone` and edit the
   `domains` list to match your life. Everything structural about your
   brain is declared in that one file.
3. Point any agent harness at the repository. `AGENTS.md` orients it; the
   dispatch table routes requests to procedures in `skills/`.
4. Delete the starter task in `tasks/` once you've made the brain yours.

## How it works

- **Files are the source of truth.** No database, no app, no build step.
  Any frontend (Obsidian, a text editor, an agent) reads the same files.
- **The manifest declares the instance.** Domains, entity directories and
  their archetypes, status vocabularies, integrations, and field types all
  live in `megabrain.md` frontmatter — an agent learns your brain in one
  read.
- **Procedures travel with the data.** How an agent briefs you, captures
  reading, completes work, or extends the brain is written down in
  `skills/core/`, portable across instances and harnesses.
- **Extension is a procedure.** To track something new, ask your agent to
  "start tracking X" — it routes to `skills/core/extend-brain.md`, which
  updates the manifest and creates directories in the conforming order.

## Layout

| Path | What it is |
|---|---|
| `megabrain.md` | The manifest: all instance declarations |
| `AGENTS.md` | Agent root: identity, dispatch table, working rules |
| `skills/core/` | Portable procedures shipped with the standard |
| `skills/adapters/` | Integration adapters (empty until you add one) |
| `skills/packs/` | Procedures specific to your own life |
| `tasks/` | Ephemeral work items |
| `projects/` | Durable entities |
| `context/` | Background context, one note per domain |
| `journal/` | Dated prose series |
| `reading/` | Captured external material |
| `history.md` | Append-only completion log |
| `archive/` | Archived durable entities |

The normative rules this template conforms to are in the megabrain
specification. Conformance is carried by the manifest, `AGENTS.md`, and the
procedures — agents never need to read the spec itself at runtime.
