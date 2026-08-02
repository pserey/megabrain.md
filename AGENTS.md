# AGENTS.md

Working rules for agents operating in this repository — the megabrain.md
standard itself, not an instance. Instances carry their own `AGENTS.md`;
this file never ships (the release tarball contains only `template/`,
`migrations/`, `MANAGED`, and `VERSION`).

## Never version temporary files

Do not commit temporary working artifacts: plans (`PLAN.md` and friends),
release notes (`RELEASE-NOTES-*.md`), build output (`dist/`), scratch or
fixture files, and anything else whose purpose is to be reviewed once and
discarded. The repository holds the standard; working documents live in
the working tree, untracked, and die there.

When a task produces such a file, leave it untracked and say so. Before
committing, check `git status` for strays and exclude them. If one has
already been committed, say so rather than compounding it — the fix is a
history rewrite, and that is the user's call, never yours to do unasked.
