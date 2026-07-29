# Complete item

Use this procedure when the user finishes, completes, or cancels a tracked
item.

Manifest values this procedure depends on: `entities` (status vocabularies,
terminal statuses, `on_terminal`), `completion.log`,
`completion.archive_root`, `timezone`. If any is missing, say so and stop.

1. Identify the note and its directory's archetype and terminal statuses
   from the manifest. If several notes could match, ask which one.
2. Set the note's `status` to the appropriate terminal status.
3. If the note's archetype is `captured_external`, stop here: captures are
   never logged to the completion log. The log records work that closed,
   not material that was read.
4. Otherwise, append one dated line to the completion log declared in
   `completion.log`, stating what was completed and its domain. Entries are
   one line, dated with an ISO calendar date, and are never rewritten or
   reordered — corrections are appended, not edited.
5. Then, and only after the log line is written, apply the directory's
   declared `on_terminal`:
   - `delete` — delete the note. Git history preserves it.
   - `archive` — move it under `completion.archive_root`, preserving its
     relative directory, without rewriting its content or frontmatter.
   - `retain` — leave it in place.
6. Report the log line, the final disposition of the note, and every path
   touched.

Logging always precedes deletion or archiving. If you cannot write the log
for any reason, do not delete or archive the note — report the failure
instead. A completed entity that was never logged is data loss.
