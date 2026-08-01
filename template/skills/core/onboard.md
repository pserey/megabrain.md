# Onboard

Use this procedure when a user is setting up a brain for the first time:
"I'm new here", "set up my brain", "make this mine", "onboard me". You
interview the user about their life, infer the structure, and build the
first real version of the brain in one operation. Onboarding is bulk
extension with an interview in front: everything you build goes through
the same rules as `extend-brain`, one decision procedure with two entry
points.

This procedure edits the contract layer. Leave all changes uncommitted and
summarize them for the user to review — never commit manifest, `AGENTS.md`,
or skills changes without explicit approval in the moment.

Manifest values this procedure depends on: all of them. Read `megabrain.md`
in full before changing anything. Everything else this procedure needs
comes from conversation: it requires no capability beyond reading and
writing files, so never scrape a calendar, probe an integration, or inspect
anything outside the repository to fill in the interview.

The output of the interview is manifest declarations; directories come
after, in the same operation. Never create a notes directory the manifest
does not declare.

## The interview

Ask about the user's life, never about the brain. The user is not expected
to supply architecture: translating their answers into archetypes,
directories, and lifecycles is your job, not theirs. Keep the passes broad
and open-ended, and do the mapping yourself. Read
`skills/core/extend-brain.md` — its "Adding an entity type" selection
procedure, including the same-day test, is what you route everything you
hear through, applied to the concrete examples the user gives you rather
than asked of the user directly.

Four passes:

1. **What do you actually do** — job, study, side efforts, people you look
   after. This yields the domain vocabulary.
2. **Walk me through a typical week** — deliberately open-ended. From the
   narrative, infer what ends versus what continues (the ephemeral/durable
   split, and the status vocabularies for each), what recurs (dated-series
   candidates — run the same-day test yourself against the examples given),
   and what arrives from outside (captured external, and integration
   candidates). A commitment the user attends twice some days is a capture,
   not a dated series; this is the pass where that gets caught, by
   inference, at setup.
3. **What do you wish you could see at a glance** — derived views. Check,
   against what you are about to declare, that the canonical views (active
   work by domain, durable entities by domain, and the `due` views where
   `due` will exist) are computable from frontmatter alone. This is also
   the moment to recommend a frontend: the brain is plain Markdown on
   disk, so anything that renders Markdown works. Recommend Obsidian by
   default — it is the best fit today for at-a-glance dashboards over a
   plain-Markdown tree — and name the alternatives (any Markdown editor,
   plain files, a purpose-built app later) so the recommendation reads as
   a default, not a requirement. Declare the choice under `frontends` in
   the manifest; an instance may declare zero, one, or many.
4. **Where does your work already live** — integrations. For each, agree
   the intake mode (`sweep` or `on_demand`) and the write policy
   (`read_only`, `on_request`, or `autonomous` with the specific
   operations enumerated). Declare them in the manifest now; the adapter
   procedure can come later, through `extend-brain`, when the user
   actually wants the wiring.

## The cap

Refuse to build everything at once. A first brain with nine directories is
dead on arrival: the initial structure must be small enough to survive
week one. Defer everything else explicitly to `extend-brain`. This is a
rule, not a suggestion — the natural failure mode of an enthusiastic
interview is over-structuring, and you have permission to say "not yet."

Deferred does not mean forgotten. The interview will surface candidate
structures the cap excludes, and you have already done the inference work
on them. Keep them for the closing report.

## The proposal

Before writing anything, present in one message:

- the full manifest diff: domains, entity directories with archetypes
  (flavor, status vocabularies, terminal statuses, and `on_terminal`
  where required), fields, integrations, frontends;
- the directory list, with the seed note each will get;
- your inferences, stated back: "you mentioned two 1:1s some days, so
  meetings are captures, not a dated series." Naming what settled each
  call is what gives the user the chance to correct a wrong read before
  anything is written;
- the deferred-candidates list, so the user sees what you held back and
  why.

Wait for explicit approval. Do not write first and apologize.

## The build

On approval, in this order:

1. Write the manifest changes.
2. Create each declared directory with one seed note. A seed note carries
   the required frontmatter for its archetype — `domain`, `date_added`,
   and `status` where the archetype declares a vocabulary — and one or two
   lines of real content from the interview, never placeholder text.
3. Rewrite the `context/` notes for the user's real domains, replacing the
   template's starter context so each declared domain has a note that
   describes how that domain actually works.
4. If the instance still holds the starter task shipped with the template
   (`make-this-brain-yours.md` in the ephemeral-work-item directory),
   retire it through the completion protocol in
   `skills/core/complete-item.md`.
5. Report every path written and the metadata set.

## The closing report

End with the **deferred candidates**: the structures you considered and
held back, each with a one-line reason and the trigger to revisit it —
"when you start the course, extend with a `courses/` durable entity." The
user should feel necessities emerge from real use; when week-three
friction arrives, it lands on a suggestion that already fits how they
work instead of a blank menu.

Leave everything uncommitted for review. The manifest and the new
directories are the user's to commit.
