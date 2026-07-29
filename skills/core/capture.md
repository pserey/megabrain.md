# Capture

Use this procedure for requests to summarize, annotate, or file external
material — an article, paper, or link — including any message that is
mostly a URL.

Manifest values this procedure depends on: `entities` (the
`captured_external` directory and its status vocabulary), `domains`,
`timezone`, `filename_date_format`. If any is missing, say so and stop.

1. Fetch the content. If it truly cannot be retrieved, say so and stop —
   do not summarize from the URL or title alone.
2. Read the background-context notes and active entities to find topical
   overlap. Identify the most likely `domain` and, where content genuinely
   supports it, `related` notes. Never assert a relation you cannot
   support from content — an omitted `related` is fine.
3. Create one note in the declared `captured_external` directory, named
   `<date>-<slug>.md` using the manifest's `filename_date_format`, with
   frontmatter:
   - `domain` — a member of the declared domain vocabulary.
   - `status` — the vocabulary's "not yet consumed" value, unless the user
     has clearly already read it and wants it filed.
   - `source_url` — the origin URL.
   - `date_added` — today, in the manifest's `timezone`.
   - `related`, `tags` — only when genuinely non-empty.
4. Below the frontmatter write a concise summary of what the piece actually
   argues or reports, and one or two sentences on why it matters here. If
   nothing in the brain relates yet, say that plainly instead of forcing a
   connection.
5. Report the created path and the metadata you set.

A capture never creates a work item or durable entity as a side effect —
that requires an explicit request. Captures are never logged to the
completion log.

Human-in-the-loop intake: this procedure runs only on material the user
gave you. Never pull items from an external system and file them without
explicit approval of those specific items.
