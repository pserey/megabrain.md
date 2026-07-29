# Add item

Use this procedure for requests such as "add task: X", "remind me to Y",
or "track this" — creating one new note in an existing entity directory.

Manifest values this procedure depends on: `entities` (paths, archetypes,
status vocabularies), `domains`, `fields`, `timezone`,
`filename_date_format`. If any is missing, say so and stop.

1. Choose the target directory. Default to the declared
   `ephemeral_work_item` directory unless the user names another entity
   type. If the request needs an entity type or domain the manifest does
   not declare, stop and follow `extend-brain.md` instead — never create a
   note in an undeclared directory or with an undeclared domain.
2. Infer a short descriptive kebab-case filename and a natural-language
   title. Files in a dated-series or captured-external directory are named
   with the manifest's `filename_date_format` (`<date>.md` or
   `<date>-<slug>.md`).
3. Set frontmatter:
   - `domain` — a member of the declared domain vocabulary. Use the stated
     or safely inferred value.
   - `date_added` — today, resolved in the manifest's `timezone`.
   - `status` — the initial value of the directory's declared vocabulary,
     when the archetype declares one.
   - Optional reserved keys (`due`, `priority`, …) only when known. Omit
     unknown keys entirely — never write placeholders.
   - Resolve the type of any `declared`-type key from `fields` before
     writing a value.
4. Ask at most one follow-up, only when domain or due-date ambiguity would
   cause a materially wrong capture. Otherwise create the note immediately
   with a concise description beneath the frontmatter.
5. Report the created path and the metadata you set.
