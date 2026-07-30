# Authoring a migration pack

**Audience:** whoever maintains this standard. This document is not shipped to instances and is not a procedure any agent dispatches to — it lives in `docs/` precisely so it stays out of `template/`. It describes how to turn "the spec changed since the last tag" into a migration pack that upgrades a real instance.

The reference pack is [`migrations/0.2.0/`](../migrations/0.2.0/). When something here is unclear, read that one.

## 1. Decide whether you need a pack

[D-7]: every release that **changes any conformance requirement** ships a pack. A release that only reworks prose, fixes a typo in a rationale block, or improves a core procedure's wording does not — managed files are replaced wholesale, so improvements to them ride along for free.

The test is not "did files change", it is "would an existing instance stop conforming, or fail to gain what the new version promises, if nothing ran".

## 2. Read the diff since the last tag

```bash
git describe --tags --abbrev=0
```

```bash
git diff "$(git describe --tags --abbrev=0)"..HEAD -- docs/SPEC.md MANAGED template/AGENTS.md template/megabrain.md
```

Those four paths are the whole input. Everything else under `template/` is either a managed file (overwritten, needs no step) or starter content (never touched in an existing instance).

Read `docs/SPEC.md`'s diff for new and changed **MUST** requirements specifically. A new SHOULD needs no step; a new MUST almost always does.

## 3. Triage each change into steps

| What changed since the last tag | Step needed? |
|---|---|
| Content of a file already in `MANAGED` | **No.** The wholesale overwrite handles it ([D-16]) |
| A file added to `MANAGED` | **No step**, but it must be listed in `MANAGED` — the upgrade copies every path there |
| A file removed from `MANAGED` | **No step**, but remove the line; the upgrade deletes managed files the release drops |
| `AGENTS.md` skeleton, or a new dispatch row | **Agentic.** It is instance-owned in content ([D-2]) |
| A new required declaration in `megabrain.md` | **Programmatic** if the value can be derived or defaulted; **agentic** if it needs judgment about the user's life |
| A frontmatter key renamed, added, or newly required on notes | **Programmatic** |
| A status vocabulary value renamed | **Programmatic** |
| Instance content moving between directories | **Programmatic**, or agentic if which file goes where is a judgment call |
| Anything in `.megabrain/` | **No.** The upgrade rewrites the lock itself ([D-17]) — never write a step that edits the lock, except the one case in §7 below |

Most diffs produce **zero or one** step. If your triage produces five, you are probably scripting things the overwrite already does.

## 4. Scaffold the pack

```bash
mkdir -p migrations/<new-version>/steps
```

`MIGRATING.md` carries YAML frontmatter declaring `from`, `to`, and an ordered `steps` list. Every step declares `id`, `kind`, `runtime`, `summary`, and `verify`; a `programmatic` step also declares `script` ([D-8]).

```yaml
---
from: "0.2.0"
to: "0.3.0"
steps:
  - id: rename-blocked-status
    kind: programmatic
    runtime: bash
    script: steps/01-rename-blocked-status.sh
    summary: Rename the blocked status to waiting across every task note
    verify: note-schema
---
```

`runtime` is `bash` on every step, including agentic ones — it is the only value this version of the spec defines ([D-9]), and it is declared from day one so a future runtime is a new value rather than a format change.

Below the frontmatter, write prose for the agent that will execute this. Explain *why* each step exists, not just what it does; the agent reads this in full before acting, and an agentic step is only as good as its prose.

## 5. Write the scripts

Constraints, all of them load-bearing:

- **POSIX `sh`**, not bashisms. `#!/bin/sh` and `set -eu`.
- **Idempotent** ([D-9]). Running it twice must leave the same result as running it once. The upgrade may re-run a pack after a partial failure. Every script in `migrations/0.2.0/steps/` opens with an "already done, nothing to do" branch — copy that shape.
- **Run from the instance root.** Assert it: `[ -f megabrain.md ] || exit 1`.
- **Refuse to act on an unexpected state.** If the manifest is at a version this pack does not expect, fail loudly rather than half-applying. See `02-bump-spec-version.sh`.
- **Verify your own rewrite before committing it.** Write to a temp file, grep it for the expected result, and only then overwrite. A `sed` that silently matches nothing is the most common way a migration lies about succeeding.

Test both branches by hand:

```bash
sh migrations/<version>/steps/01-whatever.sh && sh migrations/<version>/steps/01-whatever.sh
```

## 6. Choose each step's `verify`

[D-11]: `verify` names a check the conformance checker can perform. It is not run after the step — it is the **bisection tool**, run only when the final doctor fails, to find which step lied.

```bash
template/scripts/doctor.sh --list-checks
```

Pick the check that would fail if and only if this step did not do its job. If none exists, add one to `template/scripts/megabrain.py`:

```python
@check("capture-policy-declared", 2, since="0.3.0")
def _capture_policy(inst: Instance, out):
    if isinstance(inst.manifest, dict) and not inst.manifest.get("capture_policy"):
        out.append(Finding("MUST", "M-2", "capture-policy-declared",
                           "the manifest does not declare 'capture_policy'"))
```

The `since=` argument is what makes the registry version-aware ([D-18]). Set it to the version you are releasing. That is what lets the pre-chain doctor validate a 0.2.0 instance without demanding 0.3.0's requirements, and it is not optional — a check without a correct `since` makes every older instance report as non-conforming the moment it downloads the new release.

## 7. If the pack must write a lock file

Only relevant when the previous version had no lock, or had a different managed set. If you do write one, **bake in the previous release's reference hashes** rather than hashing what is on disk:

```bash
for f in $(git show <prev-tag>:MANAGED | grep -v '^#' | grep .); do
  printf '%s:%s\n' "$f" "$(git show "<prev-tag>:template/$f" | shasum -a 256 | cut -d' ' -f1)"
done
```

Hashing the files as found records a user's local edits as if they were the release, and the drift warning of [D-16] then never fires for anything modified before the lock existed — which is the exact case the lock is there to catch. `migrations/0.2.0/steps/01-create-lock.sh` gets this right; it is worth reading before you write one.

## 8. Bump the version markers

Three places, and `tools/build-release.sh` refuses to build if the first two disagree:

```bash
echo "<new-version>" > VERSION
```

- `VERSION`
- `spec_version` in `template/megabrain.md`
- the header and changelog in `docs/SPEC.md`

And update `MANAGED` if the managed set changed.

## 9. Test against a real instance

Never tag a pack you have not run against an instance of the previous release.

```bash
tools/build-release.sh
```

```bash
bash install.sh --dir /tmp/guinea --version <previous-version>
```

Then make it a *realistic* instance before upgrading, because a pristine one will not catch the bugs that matter:

- add a dispatch row of your own and a procedure in `skills/packs/`;
- edit a managed file and **commit it** — committed drift is invisible to the clean-tree gate, and is the case that finds real bugs;
- add a few notes with the frontmatter your change touches.

Now execute `template/skills/core/upgrade.md` against it, following the procedure literally rather than doing what you know it means. Deviating is how you ship a procedure that only works when its author drives it.

Check all of this:

- [ ] doctor passes against the **previous** version before the chain
- [ ] each programmatic script is idempotent when run twice
- [ ] the agentic steps touched only the lines they had to (`git diff` should be small and boring)
- [ ] the drift warning names your edited managed file before it is overwritten
- [ ] doctor passes against the **new** version after the chain
- [ ] `git reset --hard pre-upgrade-<version> && git clean -fd` restores a conforming previous-version instance

Then seed a failure — make one step exit 0 without doing its work — and confirm the final doctor catches it and that walking the steps' `verify` checks localizes it.

## 10. Test the chain, not just the hop

[D-20]: a pack is tested against upgrades from the **two preceding minor versions**. Repeat §9 starting from each, letting the chain apply every intervening pack in order. Packs must compose: a step that assumes it runs immediately after the previous release, rather than after an arbitrary chain, will pass its own test and fail in the field.

## 11. Release

`tools/build-release.sh` gates on `VERSION` matching the template manifest and on every `MANAGED` path existing. The workflow additionally gates on the tag matching `VERSION`, on `migrations/<version>/MIGRATING.md` existing, and on the tarball actually installing and passing conformance — so a pack that was never written is caught before anything is published.

```bash
git tag v<new-version> && git push origin v<new-version>
```
