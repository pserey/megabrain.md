---
spec_version: "0.3.0"
timezone: UTC
filename_date_format: YYYY-MM-DD
filename_exceptions:
  - AGENTS.md  # harness convention requires this casing
  - README.md  # repository convention requires this casing
domains:
  - work
  - personal
entities:
  tasks:
    path: tasks
    archetype: ephemeral_work_item
    status_vocabulary: [todo, in_progress, blocked, done, cancelled]
    terminal_statuses: [done, cancelled]
    on_terminal: delete
  projects:
    path: projects
    archetype: durable_entity
    status_vocabulary: [active, paused, complete, abandoned]
    terminal_statuses: [complete, abandoned]
    on_terminal: archive
  context:
    path: context
    archetype: background_context
  history:
    path: history.md
    archetype: append_only_log
  journal:
    path: journal
    archetype: dated_series
    flavor: prose
  reading:
    path: reading
    archetype: captured_external
    status_vocabulary: [unread, read]
    terminal_statuses: [read]
    on_terminal: retain
  archived_projects:
    path: archive/projects
    archetype: durable_entity
    status_vocabulary: [complete, abandoned]
    terminal_statuses: [complete, abandoned]
    on_terminal: retain
completion:
  log: history.md
  archive_root: archive
fields:
  priority:
    type: enum
    ordered: true
    vocabulary: [high, medium, low]
  progress:
    type: integer
    range: [0, 100]
integrations: []
skills:
  root: skills
  layers:
    core: skills/core
    adapters: skills/adapters
    packs: skills/packs
frontends: []
---

# Megabrain manifest

This file declares the instance. Everything an agent needs to orient
itself — domains, entity directories and their archetypes, status
vocabularies, field types, integrations, skills layout, frontends — is in
the YAML frontmatter above. This body is prose for humans and carries no
declarations.

## What this brain is for

This is a fresh megabrain created from the reference template. It holds
one person's cross-domain life: active work, long-running efforts,
background context, reading, and a dated journal. Git history is the
version history and the sync mechanism; the working tree is the source of
truth.

## Making it yours

- Edit `domains` above to name your life areas, then rewrite the notes in
  `context/` to describe how each domain works. Domains are metadata, never
  directories — adding one never moves a file.
- Set `timezone` to your IANA timezone. All dates in the brain resolve
  against it.
- Add entity directories (a `courses/`, a `grants/`, a measurements
  series) by asking your agent to start tracking something — the
  `extend-brain` procedure declares the directory here and creates it in
  one operation.
- Add integrations by writing an adapter in `skills/adapters/` and
  declaring it under `integrations` with its system identifier, intake
  mode, and write policy. Integrations are queried live, never mirrored.

## How the domains are meant to be used

- `work` — obligations from jobs, clients, or collaborations.
- `personal` — everything else you choose to track.

These two are a starting point, not a recommendation. The specification
deliberately defines no allowed set of domains; replace them with whatever
your life actually contains.
