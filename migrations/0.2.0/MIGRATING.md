---
from: "0.1.0"
to: "0.2.0"
steps:
  - id: create-lock
    kind: programmatic
    runtime: bash
    script: steps/01-create-lock.sh
    summary: Create .megabrain/lock.json by hashing the managed files of the 0.1.0 install
    verify: lock-present
  - id: add-upgrade-dispatch-row
    kind: agentic
    runtime: bash
    summary: Add the upgrade row to the AGENTS.md dispatch table, preserving every existing row
    verify: agents-skeleton
  - id: bump-spec-version
    kind: programmatic
    runtime: bash
    script: steps/02-bump-spec-version.sh
    summary: Declare spec_version 0.2.0 in the manifest
    verify: lock-present
---

# Migrating 0.1.0 to 0.2.0

0.2.0 adds §15 *Distribution and upgrades*. For an existing instance the change
is small: it gains a lock file, a conformance checker, and an upgrade
procedure, and it declares the new version. Nothing about the schema, the
archetypes, or the completion protocol changed, so no note content is
rewritten by this pack.

The checker and the upgrade procedure themselves are not installed by a step
here. They are managed files, and the upgrade procedure replaces all managed
files wholesale after the last pack in the chain has applied ([D-16]).

## Step 1 — `create-lock`

A 0.1.0 instance has no lock file, so there is nothing to anchor the upgrade
to and nothing to compare managed files against. This step writes the lock
that *would* have been stamped had 0.1.0 shipped one, hashing the five core
procedures that were managed at 0.1.0:

```
skills/core/add-item.md
skills/core/briefing.md
skills/core/capture.md
skills/core/complete-item.md
skills/core/extend-brain.md
```

Writing this intermediate lock is what makes the drift warning of [D-16]
possible one step later: without it, a user who had edited a core procedure
would have it silently overwritten. The lock is rewritten with the 0.2.0
managed set at the end of the upgrade ([D-17]), so its `spec_version` is
`0.1.0` only for the duration of the chain.

The script takes the release identifier and source from `MEGABRAIN_RELEASE`
and `MEGABRAIN_SOURCE` when set. It does nothing if a lock file already
exists, so re-running it after a partial failure is safe.

## Step 2 — `add-upgrade-dispatch-row`

Add one row to the dispatch table in `AGENTS.md`, after the `extend-brain`
row:

```
| Upgrading this brain, moving to a newer spec version, installing a release | `skills/core/upgrade.md` |
```

This is an agentic step because `AGENTS.md` is managed in structure and owned
by the instance in content ([D-2]). The user may have added their own dispatch
rows, reworded the intents, or reordered the table. Preserve all of it: insert
the row, change nothing else, and do not reformat the file.

If the dispatch table cannot be located — the file has no table, or its
structure is unrecognizable — stop and report it rather than appending a row
somewhere plausible. An `AGENTS.md` that has diverged from the skeleton is a
conformance problem to raise with the user, not something to repair silently.

The row points at `skills/core/upgrade.md`, which does not exist yet at this
point in the chain. It is installed with the other managed files after the
last pack, so a `verify` run of `agents-skeleton` is meaningful only after the
upgrade has reached that stage — which is exactly when bisection runs it.

## Step 3 — `bump-spec-version`

Rewrite `spec_version` in the manifest frontmatter from `0.1.0` to `0.2.0`,
leaving every other declaration untouched. The instance now claims 0.2.0, so
the final conformance check validates it against the checks this version adds:
`lock-present` and `managed-hashes`.

The script is a no-op if the manifest already declares `0.2.0`, and refuses to
act if it declares anything other than `0.1.0` or `0.2.0` — a manifest at an
unexpected version means this pack is being applied out of order.
