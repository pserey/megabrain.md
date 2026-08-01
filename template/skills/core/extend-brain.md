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

1. Choose the archetype. Work through these questions in order — they are
   arranged most-discriminating first, so stop at the first one that
   settles it. Ask them about the thing the user keeps, not about the
   directory they imagine.

   1. Is it computed from other notes? → `derived_view`
   2. Did it originate outside the brain, to be filed and summarized? →
      `captured_external`
   3. Is it one immutable line per closed thing? → `append_only_log`
   4. Does it describe how a domain works, with no lifecycle? →
      `background_context`
   5. Is the date its identity? → `dated_series` (declare flavor `prose`
      or `record`, by whether the content lives in the body or the
      frontmatter)
   6. Is it expected to end and be disposed of? → `ephemeral_work_item`;
      otherwise → `durable_entity`

   Question 5 has a name: the **same-day test**. Can two of these
   legitimately exist on the same day and still be different things? If
   yes, the date is an attribute, not the identity, and it is not a dated
   series — whatever its content looks like. Meetings are the classic
   near-miss: notes per occurrence are dated captures
   (`<date>-<slug>.md`), not a dated series.

   Before declaring anything, state the chosen archetype back to the user
   **and the question that settled it**. Naming the discriminator out
   loud is what gives the user the chance to say "no, wait, I have two of
   those a day."

   The archetype set is closed. If the answer is genuinely that none of
   these fit, stop and report that — do not approximate. An approximate
   fit is the failure mode this procedure exists to prevent.
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
