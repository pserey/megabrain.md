# Briefing

Use this procedure when asked what to do today, how to allocate capacity,
or for a summary of active work and priorities.

Manifest values this procedure depends on: `entities` (paths, archetypes,
status vocabularies, terminal statuses), `timezone`, `fields.priority`,
`integrations`. If any is missing, say so and stop rather than guessing.

1. Read the current system date, time, and timezone, and resolve dates in
   the manifest's `timezone`.
2. Read `megabrain.md` and identify every directory of archetype
   `ephemeral_work_item`. Read all notes there whose `status` is not one of
   the declared terminal statuses. Read the background-context notes and,
   for broader requests, the non-terminal durable entities.
3. For each integration declared with intake mode `sweep`, follow its
   adapter procedure to pull live signal. Clearly distinguish live results
   from repository content, and state the scope of any non-default query.
   If no integrations are declared, say that the briefing is built from
   repository content alone. If a query fails or returns nothing, report
   that and continue from repository context — never substitute remembered
   values.
4. Identify overdue, due-today, and upcoming work across every domain using
   `due` where present.
5. Rank work using due-date urgency, declared `priority`, dependencies, and
   available time. Resolve the type of `priority` from `fields` in the
   manifest before sorting: if it is an ordered type, sort by it; if it is
   an unordered enumeration, group by it instead of ranking. Do not
   silently treat one domain as more important than another.
6. Present a realistic plan that fits the remaining day, separating quick
   wins from big pushes.
7. Call out conflicts, missing information, and decisions that need the
   user.

This is a read-only procedure. Do not modify priorities, statuses, due
dates, or any note unless the user explicitly asks.

If you cannot complete the briefing — a directory is missing, the manifest
is unreadable — say exactly what could not be read and present only what
the repository actually contains.
