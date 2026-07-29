# Extend brain

Use this procedure for any request to start tracking something the brain
does not yet track: a new domain, a new kind of entity, a new integration,
or a new recurring operation.

This procedure edits the contract layer. Leave all changes uncommitted and
summarize them for the user to review — never commit manifest, `AGENTS.md`,
or skills changes without explicit approval in the moment.

Manifest values this procedure depends on: all of them. Read `megabrain.md`
in full before changing anything.

## Adding a domain

1. Add the domain to `domains` in the manifest **before** any note carries
   it.
2. Create or update the domain's background-context note if the instance
   keeps one per domain.
3. Never move, rename, or restructure any file to add a domain — domain is
   metadata, not directories.

## Adding an entity type

Follow this order exactly:

1. Choose the archetype: `ephemeral_work_item`, `durable_entity`,
   `background_context`, `append_only_log`, `dated_series` (declare flavor
   `prose` or `record`), `captured_external`, or `derived_view`. The
   archetype set is closed — if none fits, say so and stop.
2. Where the archetype requires one, choose the status vocabulary and
   identify its terminal statuses, plus the `on_terminal` disposition.
3. Declare the directory in the manifest: path, archetype, vocabulary.
4. Only then create the directory and its first note. Creating the
   directory and declaring it are one operation — never create a notes
   directory the manifest does not declare.

## Adding an integration

1. Read the integration contract: integrations are queried live, never
   mirrored, and intake requires explicit user approval of specific items.
2. Write the adapter procedure in the adapters layer declared under
   `skills.layers.adapters`. The adapter is portable: it reads every
   instance-specific value (project keys, account names, field identifiers,
   queries) from the manifest, and names each value it depends on so a
   missing one fails visibly. Record the reasoning behind any non-obvious
   query scoping in the adapter itself.
3. Declare the integration in the manifest: system identifier (used for
   `system:id` external identifiers), intake mode (`sweep` or `on_demand`),
   write policy (`read_only`, `on_request`, or `autonomous` with the
   specific authorized operations enumerated), the path to the adapter, and
   all configuration the adapter requires.
4. Add a dispatch row to `AGENTS.md` routing the integration's intents to
   the adapter, with several phrasings.

## Adding a procedure

1. Cover exactly one operation. State when it applies and what to do when
   it cannot complete.
2. Place it in the correct layer: `core` (portable, no instance
   configuration, no assumed domains or integrations), `adapters` (one per
   external system, configured from the manifest), or `packs`
   (instance-specific, unrestricted). If it contains a value that would
   differ in another instance, it is not core.
3. Name every manifest value the procedure depends on.
4. Add a dispatch row to `AGENTS.md`, with several phrasings per row.
