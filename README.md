# megabrain.md

> *"Megabrain, ativar."*

A megabrain is a git repository of plain Markdown files that you keep as a second brain, and that AI agents read and write as a first-class client. This repository is the home of the [specification](docs/SPEC.md) and of the template every instance is installed from.

## Install

Hand this to your agent, or run it yourself:

```bash
curl -fsSL https://megabrain.serey.uk/install.sh | bash
```

That creates `./megabrain`: a plain private git repository with no fork relationship to this one, stamped with a lock file recording exactly what was installed. Pass `--dir ~/brain` to put it elsewhere, or `--version 0.2.0` to pin a release.

The installer asks nothing. Tailoring the brain — your timezone, your domains, the things you want to track — is your agent's job, and the template ships a starter task that walks it through.

## The agent is the operator

You can read and edit every file by hand; it is Markdown under git and nothing stops you. But a megabrain is *designed to be driven by an agent*, and two things follow from that.

**Installing means handing the installer to your agent.** Point it at the new repository and it reads `AGENTS.md`, which routes what you ask for to a procedure in `skills/`. Asking "what should I do today" runs the briefing procedure; "I finished the migration doc" runs the completion protocol. The procedures live in the repository, so they travel with the data and work across harnesses.

**There is no manual upgrade path.** When a new release lands, you ask your agent to upgrade the brain and it follows [`skills/core/upgrade.md`](template/skills/core/upgrade.md): it checks conformance, tags a rollback point, applies each migration pack in order, replaces the managed files, and checks conformance again. This is deliberate — the upgrade is specified as an agent-executed procedure ([D-12]), not as a script you run, because some migration steps are judgment calls about your own content that no script can make.

Instances created before 0.2.0 do not ship that procedure yet, so they need a one-time bootstrap: [**migrations/0.2.0/BOOTSTRAP.md**](migrations/0.2.0/BOOTSTRAP.md) has a block to copy straight into your agent.

## How it works

- **Files are the source of truth.** No database, no app, no build step. Any frontend — Obsidian, a text editor, an agent — reads the same files.
- **The manifest declares the instance.** Domains, entity directories and their archetypes, status vocabularies, integrations, and field types all live in `megabrain.md` frontmatter, so an agent learns your brain in one read.
- **Procedures travel with the data.** How an agent briefs you, captures reading, completes work, or extends the brain is written down in `skills/core/`.
- **Extension is a procedure.** To track something new, ask your agent to "start tracking X"; it routes to `extend-brain`, which updates the manifest and creates directories in the conforming order.
- **Conformance is checkable.** Every instance ships `scripts/doctor.sh`, which validates it against the `spec_version` it declares and reports violations by requirement identifier.

## Layout of this repository

| Path | What it is |
|---|---|
| [`docs/SPEC.md`](docs/SPEC.md) | The normative specification |
| `template/` | What an install produces — the tarball payload |
| `migrations/` | One pack per conformance-changing release |
| `install.sh` | The installer |
| `MANAGED` | The managed-file set of this release |
| `VERSION` | The spec version this tree builds |
| `tools/build-release.sh` | Builds the release tarball |

## Managed and instance-owned

The upgrade mechanism rests on one boundary. **Managed** files — the core procedures and the tooling, listed in `MANAGED` — belong to the standard and are replaced wholesale on upgrade. Everything else is yours and is never touched, except where a migration step explicitly rewrites content.

`AGENTS.md` and `megabrain.md` sit deliberately in between: the standard owns their structure, you own their content. They are never overwritten. When their structure has to change, the migration pack says so in prose and your agent edits around what you wrote.

Editing a managed file is allowed and will be overwritten by the next upgrade. The lock file's hashes make that visible — your agent warns you by name before replacing anything you changed, and the change survives in git history and under the rollback tag.

## Contributing to the standard

Changes to [`docs/SPEC.md`](docs/SPEC.md) that alter any conformance requirement need a migration pack under `migrations/<version>/` and a release. [`docs/AUTHORING-MIGRATIONS.md`](docs/AUTHORING-MIGRATIONS.md) is the maintainer's walkthrough for writing one from the diff since the last tag.

`tools/build-release.sh` builds the tarball the workflow publishes; `bash install.sh --tarball dist/megabrain-template.tar.gz --dir /tmp/test` installs it locally without touching a release.
