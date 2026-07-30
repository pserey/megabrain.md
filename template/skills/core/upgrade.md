# Upgrade

Use this procedure when the user asks to upgrade this brain, move to a newer
version of the specification, or install a release they have named. You are the
operator: there is no supported manual upgrade path, so do not tell the user to
run an upgrade themselves.

This procedure edits the contract layer. Leave every change uncommitted and
summarize it for the user to review — never commit manifest, `AGENTS.md`,
skills, or lock changes without explicit approval in the moment.

Manifest values this procedure depends on: `spec_version`. Everything else it
needs comes from `.megabrain/lock.json`, which is the authoritative anchor for
the upgrade. If both the lock file and `spec_version` are missing or
unreadable, say so and stop — you cannot determine what to migrate from.

Never edit `.megabrain/lock.json` by hand. It is written only by the installer
and by step 8 below.

## 1. Establish where the instance is now

Read `.megabrain/lock.json`. Take `spec_version` as the current version,
`release` as what was installed, and `source` as the distribution to fetch
from.

If the lock file does not exist, the instance predates it. Take the current
version from `spec_version` in `megabrain.md`, and take the source from the
user — ask which spec repository this brain came from rather than guessing.

## 2. Fetch the target release

Unless the user named a version, the target is the latest release of `source`.
Download the release tarball into a temporary directory outside the instance
and extract it. Do not copy anything into the instance yet.

The tarball carries `template/` (the files a fresh install would get),
`MANAGED` (the release's managed-file list), `VERSION`, and `migrations/` —
every pack up to that release, so the whole chain is in this one download.

If the download fails, report exactly what could not be fetched and stop. Do
not proceed from a partial or remembered release.

## 3. Compute the chain

The chain is every directory in the release's `migrations/` whose version is
greater than the current version and less than or equal to the target, in
ascending version order. One pack per intervening release, applied strictly in
order.

- If the chain is empty, report that the instance is already at the target
  version and stop. Nothing below runs.
- If the chain spans more than two minor versions back, tell the user it is
  outside the tested window and is therefore experimental, and ask whether to
  continue before going on.

Report the chain you computed before executing it.

## 4. Gate on a clean working tree

Run `git status --porcelain`. If it returns anything, stop and tell the user
which files are dirty. The upgrade rewrites managed files and relies on git
history as the only backup, so it must not run over uncommitted work.

## 5. Check conformance before migrating

Run the conformance checker against the instance's **current** version:

```
python3 <release>/template/scripts/megabrain.py doctor --root . --spec-version <current>
```

Run it from the extracted release rather than from `scripts/` in the instance,
because the instance may not ship a checker yet at its current version. The
checker is version-aware, so it validates only what the current version
requires.

If this run reports MUST violations, stop. Report them and tell the user the
instance must conform before it can be migrated — a migration applied to a
non-conforming instance produces an unpredictable result.

## 6. Create the rollback tag

```
git tag pre-upgrade-<target-version>
```

This tag is the entire backup mechanism. Every managed file the upgrade
overwrites, and every instance file a migration step rewrites, is recoverable
from it. If the tag already exists, a previous upgrade to this version was
interrupted — tell the user and ask whether to reuse or replace it.

## 7. Apply each pack in order

For each pack in the chain, read its `migrations/<version>/MIGRATING.md` in
full before doing anything, then execute its `steps` in the declared order:

- **`programmatic`** — run the declared `script`. The scripts are idempotent,
  so a re-run after a partial failure is safe.
- **`agentic`** — follow the step's prose yourself. Preserve everything the
  user wrote: dispatch rows they added, declarations they changed, prose they
  authored. A structural change to `AGENTS.md` or `megabrain.md` means editing
  around the user's content, never replacing the file.

If any step fails, stop at that step. Do not continue to later steps or later
packs. Report which pack and which step failed, and what the failure was.

Report every file each pack touched, as you go.

## 8. Replace the managed files and rewrite the lock

Only once every pack in the chain has applied cleanly.

1. Read the release's `MANAGED` file. That list, not the instance's directory
   layout, defines what is managed by the target release.
2. Before overwriting anything, compare each managed file against the hashes in
   the lock file. Run this from the release too — the instance may still not
   ship the tooling at this point in the chain:
   ```
   python3 <release>/template/scripts/megabrain.py lock verify --root .
   ```
   Any file it reports as drifted has been modified locally. **Warn the user by
   name for each one** before continuing. These files belong to the standard,
   so they are overwritten; the modified version survives in git history and
   under the rollback tag, and no separate backup is taken.

   Drift is not visible to the clean-tree gate of step 4: a user who *committed*
   a change to a managed file has a clean tree and a modified file. This
   comparison is the only thing that catches that, which is why it runs before
   any copying.
3. Copy every path in `MANAGED` from `<release>/template/` into the instance,
   overwriting whatever is there. Create parent directories as needed. A
   managed file that the release drops should be deleted from the instance.
4. Never overwrite `AGENTS.md` or `megabrain.md`. They are managed in structure
   and owned by the instance in content; they change only through the agentic
   steps of step 7.
5. Rewrite the lock, now that the target release's tooling is in place:
   ```
   python3 scripts/megabrain.py lock write \
       --release <release-identifier> \
       --source <source> \
       --spec-version <target-version> \
       --managed-list <release>/MANAGED
   ```
   This is the only write to the lock file the upgrade makes on its own; the
   intermediate lock a migration step may have written is replaced here, not
   amended.

## 9. Check conformance after migrating

Run the instance's own checker, now that the target release installed it:

```
scripts/doctor.sh
```

If it passes, the upgrade succeeded.

If it reports MUST violations, the upgrade has failed. Halt and report. Then
localize the failure rather than guessing: every migration step declares a
`verify` naming a check the checker can run on its own.

```
scripts/doctor.sh --only <check-id>
```

Walk the chain's steps in order, running each step's `verify`, and report the
first one that fails — that is the step that did not do what it claimed. Tell
the user how to undo the whole attempt:

```
git reset --hard pre-upgrade-<target-version> && git clean -fd
```

Both halves are needed. The reset restores every tracked file, but a managed
file the release *added* is untracked, and a reset leaves it behind — the
`clean` is what removes it. This is safe precisely because step 4 required a
clean tree: anything untracked at this point came from the upgrade.

Do not attempt the rollback yourself without the user's approval, and do not
try to repair a failed migration by improvising edits.

## 10. Report

Tell the user:

- the chain applied, from version to version, pack by pack;
- every managed file replaced, and which of them had drifted;
- every instance file a migration step rewrote;
- the rollback tag, and the command that would undo the upgrade;
- the result of the final conformance check.

Leave everything uncommitted. The upgrade rewrote the contract layer, and that
is the user's to review and commit.
