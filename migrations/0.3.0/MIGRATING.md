---
from: "0.2.0"
to: "0.3.0"
steps:
  - id: reclassify-dated-series
    kind: agentic
    runtime: bash
    summary: Reclassify any dated-series directory whose entries are not uniquely identified by their date [A-11]
    verify: filenames
  - id: add-onboard-dispatch-row
    kind: agentic
    runtime: bash
    summary: Add the onboard row to the AGENTS.md dispatch table, preserving every existing row
    verify: agents-skeleton
  - id: bump-spec-version
    kind: programmatic
    runtime: bash
    script: steps/01-bump-spec-version.sh
    summary: Declare spec_version 0.3.0 in the manifest
    verify: lock-present
---

# Migrating 0.2.x to 0.3.0

0.3.0 adds [A-11] — a dated series is one whose entries are uniquely
identified by the date they cover — and §5.8 *Choosing an archetype*, the
decision procedure that was missing when the archetype set was a menu of
names. It also ships an `onboard` core procedure, reachable from the dispatch
table. The pack covers both 0.2.0 and 0.2.1 instances: 0.2.1 was a patch
release that did not touch the specification, so there is nothing between the
two to migrate.

For most instances this pack changes only the dispatch table and the declared
version. The reclassification step below is a no-op for every correctly
declared dated series.

## Step 1 — `reclassify-dated-series`

[A-11] is a new MUST, and it is a judgment call: whether a directory's entries
are identified by their date cannot be decided by a script. The canonical
misdeclaration is a `meetings/` directory declared `dated_series` — two
meetings on one day are two entities that happen to share a date, so the date
is an attribute there, not the identity.

Scan every entity declared `dated_series` in the manifest. Flag a directory
when either holds:

- any filename in it does not match `<date>.md` exactly — a second entry for
  one date could not take the date as its name, so something else was
  invented; or
- the user reports that more than one entry per date is normal there.

For each flagged directory, walk the archetype-selection questions with the
user — read `skills/core/extend-brain.md` and use its "Adding an entity type"
step 1, including the same-day test. The common landing spot is
`captured_external`: notes per occurrence, named `<date>-<slug>.md`. To
reclassify:

1. Rewrite the manifest declaration: the new archetype, and where it requires
   one, a status vocabulary with terminal statuses and `on_terminal`. A
   meeting's real lifecycle maps onto the captured-external minimum — "not
   yet consumed" versus "consumed" (raw notes versus follow-ups extracted).
2. Rename each file to `<date>-<slug>.md`, using the declared
   `filename_date_format`.
3. Add the frontmatter the new archetype requires — `status` above all — to
   every note in the directory.

Preserve note bodies untouched ([R-12]): renames and frontmatter additions
only, never rewrites of prose the user authored.

If the user is unavailable to decide, leave the declaration alone, report the
flagged directory by name, and do not guess. A flagged directory left alone
may fail the final conformance check — that is the check doing its job, and
the bisection walk will land on this step.

A directory that is genuinely one-entry-per-date — a journal, a measurement
series — is untouched by this step, whatever its content looks like.

## Step 2 — `add-onboard-dispatch-row`

Add one row to the dispatch table in `AGENTS.md`, immediately before the
`extend-brain` row:

```
| Setting up this brain for the first time, "set up my brain", "I'm new here", "make this mine", "onboard me" | `skills/core/onboard.md` |
```

This is an agentic step because `AGENTS.md` is managed in structure and owned
by the instance in content ([D-2]). The user may have added their own dispatch
rows, reworded the intents, or reordered the table. Preserve all of it: insert
the row, change nothing else, and do not reformat the file.

If the dispatch table cannot be located — the file has no table, or its
structure is unrecognizable — stop and report it rather than appending a row
somewhere plausible. An `AGENTS.md` that has diverged from the skeleton is a
conformance problem to raise with the user, not something to repair silently.

A mature instance will likely never run the procedure this row points at —
onboarding is needed once, and this instance already happened. Add the row
anyway: the dispatch set is structure, and an unused row costs nothing. The
row points at `skills/core/onboard.md`, which does not exist yet at this point
in the chain; it is installed with the other managed files after the last
pack, so a `verify` run of `agents-skeleton` is meaningful only after the
upgrade has reached that stage — which is exactly when bisection runs it.

## Step 3 — `bump-spec-version`

Rewrite `spec_version` in the manifest frontmatter to `0.3.0`, leaving every
other declaration untouched. The script accepts a manifest declaring `0.2.0`
or `0.2.1`, is a no-op on one already at `0.3.0`, and refuses to act on
anything else — a manifest at an unexpected version means this pack is being
applied out of order.
