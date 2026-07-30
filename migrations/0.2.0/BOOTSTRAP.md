# Upgrading a 0.1.0 instance — copy this to your agent

**Read this on the web, not from a checkout.** It explains how to fetch the release, so you cannot already have it.

A 0.1.0 instance predates the upgrade mechanism: it has no `skills/core/upgrade.md` and no dispatch row pointing at one, so there is nothing for your agent to route to. This is the one-time bootstrap that closes that gap. Every version after 0.2.0 ships the procedure, so from then on "upgrade this brain" is enough.

## Before you start

- Your brain must be a git repository with **no uncommitted changes**. The upgrade rewrites files and relies on git history as its only backup, so it refuses to run over a dirty tree.
- Your brain must already **conform to 0.1.0**. The agent checks this first and stops if it does not. Undeclared note directories and notes missing `domain` or `date_added` are the usual culprits.
- You need `git`, `curl`, `tar`, and `python3`. Your agent needs to be able to run shell commands.

## Copy this

Open your agent **in your megabrain repository** and paste this:

```
Upgrade this megabrain to the latest specification version.

This instance is at 0.1.0 and does not ship the upgrade procedure yet, so
bootstrap it from the release:

  mkdir -p /tmp/mb-upgrade
  curl -fsSL https://github.com/pserey/megabrain.md/releases/latest/download/megabrain-template.tar.gz | tar -xz -C /tmp/mb-upgrade

Then read /tmp/mb-upgrade/template/skills/core/upgrade.md in full and follow
it against this repository, exactly as written.

Context it will ask for:
  - the extracted release is at /tmp/mb-upgrade
  - the distribution source is https://github.com/pserey/megabrain.md
  - there is no .megabrain/lock.json yet; take the current version from
    spec_version in megabrain.md

Report what you changed. Leave everything uncommitted for me to review.
```

To pin a specific version instead of the latest, replace `releases/latest/download` with `releases/download/v0.2.0`.

## What the agent will do

It follows a ten-step procedure. In order: read your current version, fetch and extract the release, compute the migration chain, check your tree is clean, run the conformance checker against **0.1.0**, tag a rollback point, apply each migration pack in version order, replace the managed files, rewrite the lock file, and run the checker again against the new version.

Three of those are worth knowing about as they happen.

**It will warn you about files you have edited.** If you changed one of the five core procedures, the agent names it before overwriting. Those files belong to the standard and are replaced — your version survives in git history and under the rollback tag. Nothing is silently lost, but nothing is merged either.

**It edits `AGENTS.md` by hand, not by replacement.** Adding the upgrade dispatch row is an agentic step precisely because that file is yours: your own dispatch rows, wording, and ordering are preserved. The diff should be a single added line. If it is bigger than that, something went wrong — say so before committing.

**It leaves everything uncommitted.** The upgrade touches the contract layer — the manifest, `AGENTS.md`, the procedures — and that is yours to review and commit. Read the diff before you do.

## If it fails

The agent halts and reports rather than improvising a repair. It will also tell you which migration step failed, by running each step's declared verification check until one fails.

To undo the whole attempt:

```bash
git reset --hard pre-upgrade-0.2.0 && git clean -fd
```

Both halves are needed: the reset restores tracked files, and the clean removes newly installed ones that were never tracked.

## If your agent cannot run shell commands

Then it cannot do the upgrade — the procedure needs `git tag`, `git status`, and file copying. Run the two bootstrap commands yourself, then point the agent at `/tmp/mb-upgrade/template/skills/core/upgrade.md` and run the shell steps on its behalf as it reaches them.

## Afterwards

Check that it worked:

```bash
scripts/doctor.sh
```

You should see `PASS conforms to 0.2.0`. From now on, upgrading is just asking your agent to upgrade the brain — the dispatch row exists, and it will find the procedure itself.
