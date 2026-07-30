# My megabrain

A plain-Markdown second brain under git. The files here are the source of truth; there is no database, no app, and no build step.

**Point your agent at this repository.** `AGENTS.md` orients it, and the dispatch table there routes what you ask for to a procedure in `skills/`. The agent is the primary operator of this brain — you can read and edit every file by hand, but the procedures are what keep it conforming.

Start by asking your agent to work through `tasks/make-this-brain-yours.md`.

| Path | What it is |
|---|---|
| `megabrain.md` | The manifest: every declaration about this instance |
| `AGENTS.md` | Agent root: identity, dispatch table, working rules |
| `skills/core/` | Portable procedures shipped with the standard |
| `skills/adapters/` | Integration adapters (empty until you add one) |
| `skills/packs/` | Procedures specific to your own life |
| `scripts/doctor.sh` | Conformance checker — run it any time |
| `tasks/` | Ephemeral work items |
| `projects/` | Durable entities |
| `context/` | Background context, one note per domain |
| `journal/` | Dated prose series |
| `reading/` | Captured external material |
| `history.md` | Append-only completion log |
| `archive/` | Archived durable entities |
| `.megabrain/lock.json` | Tooling-owned install record. Never edit by hand |

To upgrade to a newer version of the specification, ask your agent to upgrade this brain. There is no manual upgrade path.
