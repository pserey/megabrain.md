# The megabrain specification

**Version:** 0.1.0 · **Status:** Released 2026-07-28 · **Format:** Normative

A megabrain is a git repository of plain Markdown files that a person keeps as their second brain, and that AI agents read and write as a first-class client. This document specifies what makes a repository *a megabrain* rather than a folder of notes: the invariants, the schema, the agent runtime contract, and the points at which two instances may legitimately differ.

The specification exists so that a procedure written against one person's brain runs unmodified against another's, and so that an agent dropped into an unfamiliar instance can orient itself in one read.

## 1. Conformance language

The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** are to be interpreted as described in RFC 2119.

Every normative requirement carries a stable identifier (`C-1`, `S-4`, …) so that tooling, validators, and future revisions can cite it. Non-normative material — examples, illustrations, rationale — is marked as such and carries no identifier. Anything in an appendix is non-normative.

Requirement identifiers are stable across revisions. A requirement that is removed leaves its identifier retired rather than reused.

## 2. Terminology

**Instance** — one person's megabrain repository. **Note** — a single Markdown file with YAML frontmatter. **Entity** — the thing a note represents (a task, a course, a paper, a measurement). **Archetype** — the structural kind a note belongs to, from the closed set in §5. **Domain** — a life area, recorded as metadata. **Procedure** — a Markdown file describing how an agent performs one recurring operation. **Integration** — an external system queried live by an agent. **Manifest** — the file in which an instance declares itself. **Contract layer** — the files that define behavior rather than record content: the manifest, the agent root, and procedures.

## 3. The layer model

The specification is organized in four layers of decreasing normativity.

| Layer | What it holds | Who owns it |
|---|---|---|
| 1 — Core | Invariants that make a repository a megabrain | This document |
| 2 — Schema | Fixed keys, open vocabularies, archetypes | This document |
| 3 — Extension points | Sanctioned axes of divergence | This document defines the axes; the instance fills them |
| 4 — Instance | One person's domains, entities, content, integrations | The instance, declared in its manifest |

The test for placing any concept: *does an agent working in another instance need this in order to function?* If yes, it is core. If it only needs to **know** the value, it is a declared extension point. If neither, it is instance content and this document MUST NOT mention it.

## 4. Core invariants

These are the requirements that break interoperability when violated.

**[C-1] Plain Markdown and YAML, under git.** An instance MUST be a git repository. All entity content MUST be UTF-8 Markdown files with YAML frontmatter. An instance MUST NOT require a database, an application, a build step, or an import step to be read or written. Git history is both the version history and the sync mechanism.

**[C-2] Files are the source of truth.** A conforming reader MUST be able to reconstruct the full state of the brain from the working tree alone. Any cache, index, or rendered view MUST be derivable from the notes (see §5.7).

**[C-3] An agent root that routes to procedures.** An instance MUST contain a root instruction file named `AGENTS.md` that carries a dispatch table mapping user intent to procedure files (§8). Harness-specific instruction files MAY exist and MUST delegate all shared behavior to `AGENTS.md` rather than restating it (§8.1).

**[C-4] Procedures live in the repository.** Procedures MUST be files inside the instance, not configuration held in a particular agent harness or vendor account. Procedures travel with the data. This is what makes an instance agent-agnostic rather than tied to one product.

**[C-5] `domain` is metadata, never a directory.** Directory placement expresses **entity type**; the `domain` key expresses **life area**. The two axes MUST remain orthogonal: adding a domain MUST NOT require moving, renaming, or restructuring any file.

**[C-6] Ephemeral and durable content are separated.** An instance MUST distinguish notes that are expected to be deleted or archived on completion from notes that persist and accumulate. The separation MUST be structural (different directories, declared as different archetypes), not conventional.

**[C-7] Controlled vocabulary in English; free text in any language.** All frontmatter keys, all controlled values, all filenames, and all directory names MUST be ASCII English in the casing rules of §6.2. Prose in note bodies MAY be written in any language, and MAY mix languages within one instance.

**[C-8] Integrations are queried live, never mirrored.** An instance MUST NOT maintain a synchronized copy of an external system's records. Notes record what the external system does not know — cross-domain priority calls, personal reasoning, decisions — plus the minimum pointer needed to find the record again (§7, §9).

**[C-9] Human-in-the-loop intake.** An agent MUST NOT create notes from an external system without the user's explicit approval of those specific items. Automated ingestion turns the brain into a mirror of someone else's queue and violates [C-8].

**[C-10] Completion protocol.** Reaching a terminal status MUST produce a dated entry in an append-only log before the note is deleted or archived (§10). Deletion is safe precisely because [C-1] guarantees recoverable history.

**[C-11] Self-description.** An instance MUST declare itself in a manifest (§7). An agent MUST be able to learn the instance's domains, entity types, status vocabularies, integrations, and frontend from that one file, without inferring them from directory listings or prose.

**[C-12] Fail loudly.** When an agent cannot retrieve information it was asked to use — an integration is unavailable, a file is missing, a value is unknown — it MUST say so explicitly and MUST NOT substitute an estimate, a remembered value from a previous session, or an inference presented as fact.

The following are explicitly **not** core, and an instance conforms without them: tasks as an entity type, any particular directory name, any frontmatter key other than `domain` and `status`, Obsidian or any other frontend, and any specific integration.

## 5. Archetypes

Archetypes are a closed set. Every directory of notes in an instance MUST be declared as exactly one archetype in the manifest **[A-0]**. This single rule is what makes an unfamiliar instance legible: an agent that has never seen `advisees/` or `grants/` still knows how to treat it once it knows the archetype.

An instance MAY have zero, one, or many directories of a given archetype, MAY name them anything, and MAY omit any archetype entirely.

### 5.1 Ephemeral work item

Discrete units of work expected to end. High churn.

**[A-1]** Notes MUST be one entity per file. The directory MUST declare a status vocabulary including at least one terminal status. On reaching a terminal status the note MUST follow §10.

**[A-10]** An instance SHOULD declare at least one ephemeral-work-item directory. The first canonical view ([V-2.1]) and most core procedures are defined over this archetype; an instance declaring none forgoes them, and MUST accept that those procedures do not apply to it rather than expecting them to degrade gracefully.

*Typical name:* `tasks/`.

> **Rationale (non-normative).** [A-10] is a SHOULD rather than a MUST because the archetype, not the directory, is what an agent needs — a brain used purely for reading, context, and durable entities is coherent and conforming. But this archetype is what makes a brain answer "what should I do today", which is the capability most instances are built for, so omitting it should be a deliberate choice with known consequences rather than an oversight.

### 5.2 Durable entity

Long-running things that accumulate history and are not expected to be deleted: efforts, relationships, artifacts, obligations.

**[A-2]** Notes MUST be one entity per file and MUST declare a status vocabulary. A durable entity reaching a terminal status SHOULD be retained in place or archived, and SHOULD NOT be deleted.

*Typical names:* `projects/`, `courses/`, `advisees/`, `papers/`, `grants/`.

### 5.3 Background context

Slow-changing background per domain: how a domain works, standing constraints, capacity, recurring cadences, current situation. This is what an agent reads to interpret everything else.

**[A-3]** Context notes MUST be stable references rather than a work log — an agent MUST NOT record activity here that belongs in an append-only log (§5.4) or journal (§5.5). Context notes do not require a status.

*Typical name:* `context/`, one note per domain.

### 5.4 Append-only log

The durable record of what was completed, one line per closed item.

**[A-4]** Entries MUST be appended, MUST be dated with an ISO calendar date, MUST be one line, and MUST NOT be rewritten or reordered once written. Correcting an entry means appending a correction. A log file requires no frontmatter.

*Typical name:* `history.md`.

### 5.5 Dated series

One file per date, accumulating over time. Two flavors, declared per directory in the manifest:

- **`prose`** — freeform writing covering a day: reflection, running notes, things not yet shaped into an entity.
- **`record`** — a structured observation of the same shape each time: measurements, readings, per-meeting or per-assessment records. Meant to be read by machine rather than as prose.

**[A-5]** A dated-series directory MUST declare its flavor. Files MUST be named for the date they cover (§6.3), one date per file. A `prose` entry is not a work item and MUST NOT be treated as one — an agent MUST NOT infer work items from it without explicit instruction.

**[A-6]** A `record` entry MUST carry its observation as frontmatter keys rather than prose, and MUST NOT be edited to reflect a later observation — a new observation is a new file. A missing value MUST be omitted rather than estimated or interpolated.

*Typical names:* `journal/` (prose); `health/measurements/`, `meetings/`, `grades/` (record).

> **Note (non-normative).** A dated journal and a structured record could be modeled as two archetypes. They are one shape — a dated series — differing only in whether the content lives in the body or in the frontmatter, and splitting them would add an archetype without adding any rule an agent needs.

### 5.6 Captured external

Material originating outside the brain that the user wants filed and summarized: articles, papers, links, documents.

**[A-7]** Captured notes MUST record where the material came from and MUST declare a status vocabulary distinguishing at minimum "not yet consumed" from "consumed". A capture MUST NOT create a work item or durable entity as a side effect; that requires an explicit request.

*Typical name:* `reading/`.

### 5.7 Derived view

A file whose content is computed from other notes: a dashboard, a chart, a roll-up, a home page.

**[A-8]** A derived view MUST declare its sources. A derived view MUST NOT be the only place any fact exists — every value in it MUST be reconstructible from the notes it derives from. When source and view disagree, the source wins. An agent updating a source SHOULD update the views declared to derive from it, and MUST NOT edit a view in a way that cannot be reproduced from its sources.

**[A-9]** A derived view SHOULD be produced by a query or generator that reads its sources at render time, rather than by an agent writing values into it. Where a view is agent-maintained, it MUST record in the view itself when it was last reconciled with its sources.

*Typical names:* a home note, a dashboard note, a query/base file.

> **Rationale (non-normative).** This archetype exists because denormalized dashboards appear naturally in real instances — a chart file duplicating a series of measurements, a summary table mirroring a context note — and they silently become a second, drifting source of truth. Naming the pattern and forcing a declared direction of derivation is what keeps [C-2] true. [A-9] states the stronger preference: a view backed by a live query cannot drift, because there is nothing to keep in sync. Agent-maintained views are permitted because not every value is queryable, but they carry a reconciliation date so that staleness is visible rather than assumed away.

## 6. Schema

### 6.1 Required keys

**[S-1]** Every entity note MUST carry `domain`, whose value MUST be a member of the domain vocabulary declared in the manifest.

**[S-16]** Every entity note MUST carry `date_added`, the date the note entered the brain. `domain` and `date_added` are the only two keys required of every entity note.

**[S-2]** Every note belonging to an archetype that declares a status vocabulary (§5.1, §5.2, §5.6, and any other the instance chooses) MUST carry `status`, whose value MUST be a member of that archetype's declared vocabulary. Notes in archetypes without a declared status vocabulary MUST NOT carry a meaningless `status`.

**[S-3]** Every note MUST represent exactly one entity. Splitting one entity across files, or packing several entities into one file, is non-conforming.

> **Note (non-normative).** An earlier formulation required `status` on *every* note. Writing the archetype set out made that untenable: a background-context note and a body-measurement record have no lifecycle, and forcing a status onto them produces a vocabulary that means nothing. `domain` and `date_added` are the only keys universal to all entity notes.
>
> `date_added` is stored explicitly rather than derived from git because the two answer different questions and diverge in practice: a note's first commit is the date it was *committed*, which moves under rebases, history rewrites, bulk imports, and any period where the brain went uncommitted for a week. Capture date is a fact about the brain; commit date is a fact about the repository.

### 6.2 Key and value rules

**[S-4]** Frontmatter keys MUST be `snake_case` ASCII English.

**[S-5]** Controlled values MUST be `snake_case` ASCII English. Free-text values MAY be any language and MAY contain any Unicode.

**[S-6]** Filenames and directory names MUST be lowercase ASCII `kebab-case` with a `.md` extension, and SHOULD be descriptive enough to identify the entity without opening the file. Derived-view and root-level notes MAY use another casing where a frontend requires it, and MUST declare that in the manifest.

**[S-7]** Date values MUST be ISO 8601 calendar dates (`YYYY-MM-DD`), interpreted in the timezone declared in the manifest. A key that genuinely requires finer granularity MUST be declared in the manifest as a datetime key and MUST use RFC 3339 with an explicit offset (`2026-07-14T09:30:00-03:00`). A single key MUST NOT mix the two forms across notes.

### 6.3 Dated files

**[S-8]** Files in a dated series (§5.5) MUST encode their date in the filename using the filename date format declared in the manifest (§7), and files in a dated capture series (§5.6) MUST be named `<date>-<slug>.md` using that same format. The date is that of the record, the entry, or the capture.

**[S-18]** The declared filename date format MUST be used consistently across the whole instance. It SHOULD be `YYYY-MM-DD`, because that format alone sorts chronologically under plain lexical ordering — file listings, `ls`, and any frontend that sorts by name. An instance declaring another format accepts that its dated directories no longer list in date order. Frontmatter dates are unaffected and remain ISO 8601 under [S-7], since those are what other tools consume.

### 6.4 Reserved keys

The following keys have fixed meaning across all instances. An instance MAY omit any of them; if it uses one, it MUST use it with this meaning **[S-9]**.

| Key | Type | Meaning |
|---|---|---|
| `domain` | string | Life area; member of the declared domain vocabulary |
| `status` | string | Lifecycle state; member of the archetype's declared vocabulary |
| `external_id` | string or list | Pointer to the record of origin (§6.5) |
| `due` | date | The date by which the entity is expected to be complete |
| `priority` | declared | Relative importance |
| `progress` | declared | How far along the entity is; user-asserted, never computed |
| `source_url` | string | Origin URL of captured external material |
| `date_added` | date | When the note entered the brain. Required on every entity note ([S-16]) |
| `related` | list of strings | Repository-relative paths to related notes |
| `tags` | list of strings | Free vocabulary; MUST NOT be load-bearing for any procedure |

**[S-10]** An instance MAY define additional keys freely. Additional keys MUST NOT redefine a reserved key, and any key a procedure depends on MUST be declared in the manifest.

**[S-17]** A reserved key of type `declared` fixes its *meaning* but not its *representation*. The instance MUST declare its type in the manifest, and its vocabulary if that type is an enumeration. An instance representing `priority` as `high | medium | low` and one representing it as an integer 1–100 both conform. A procedure reading such a key MUST resolve its type from the manifest and MUST NOT assume one; a procedure that sorts or compares such a key MUST state what it does when the type is an unordered enumeration.

**[S-11]** Optional keys MUST be omitted when unknown rather than written with a placeholder or guessed value.

**[S-12]** `related` values MUST be repository-relative paths to existing notes, and MUST be omitted when no genuine relation exists. An agent MUST NOT assert a relation it cannot support from content.

### 6.5 External identifiers

**[S-13]** An external identifier MUST have the form `system:id`, where `system` is the identifier declared for that integration in the manifest and `id` is the record's stable identifier in that system.

**[S-14]** An instance MAY use readable aliases (a per-system key such as `<system>_id`) instead of or alongside `external_id`. If it does, it MUST declare the alias-to-system mapping in the manifest so that a portable procedure can resolve it.

**[S-15]** Deduplication on intake MUST be performed on the external identifier, never on title or summary text.

> **Rationale (non-normative).** Every integration otherwise adds its own key, and every new integration amends the specification. One form, declared aliases, no amendments.

## 7. The manifest

The manifest is the seam between the standard and the instance. It is the single file an agent reads to orient itself.

**[M-1]** An instance MUST contain a manifest at the repository root in a file named `megabrain.md`. The presence of a conforming `megabrain.md` is what identifies a repository as an instance.

**[M-2]** The manifest MUST declare, at minimum:

1. **`spec_version`** — the version of this specification the instance targets.
2. **`timezone`** — an IANA timezone identifier, used to resolve all dates ([S-7]).
3. **`domains`** — the complete domain vocabulary for this instance.
4. **`entities`** — for each directory of notes: its path, its archetype (§5), and, where the archetype requires one, its status vocabulary with terminal statuses identified.
5. **`fields`** — any non-reserved frontmatter key a procedure depends on, and the vocabulary of any controlled value the instance defines (for example the `priority` vocabulary).
6. **`integrations`** — for each enabled integration: its system identifier, its intake mode (§9), the path to its adapter procedure, and all instance-specific configuration values that adapter requires.
7. **`skills`** — the location of procedures and their layering (§8.3).
8. **`frontends`** — the frontends in use, as a list. An instance MAY declare zero, one, or many; multiple frontends over one instance is expected, not exceptional, since [C-1] makes the notes readable by anything.
9. **`filename_date_format`** — the date format used in dated filenames ([S-8]).

**[M-3]** Instance-specific configuration required by any procedure MUST live in the manifest. A procedure MUST NOT hardcode a value that would differ in another instance — project keys, field identifiers, account names, queries scoped to one organization, timezones, file paths outside the repository.

**[M-4]** All declarations of [M-2] MUST be YAML frontmatter in `megabrain.md`. The body below the frontmatter is prose for humans — what this brain is for, how its domains are meant to be used — and MUST NOT carry declarations of its own. A reader MUST NOT have to parse prose to learn the structure, and MUST NOT have to search for the manifest.

**[M-5]** The manifest MUST NOT be the only place any entity content lives. It declares structure, never content.

> **Rationale (non-normative).** Without [M-3] the reusable half of an integration adapter is contaminated with one person's project key and custom-field identifier, and copying it to another instance produces a procedure that fails in ways that look like the integration is broken. The procedure is portable; the tuning is instance data.
>
> An earlier formulation let the manifest be any data file or an embedded block at an unfixed name. That was a mistake: every validator and every core procedure would need a discovery step first, and [C-11]'s promise that an agent orients in one read would be false. A fixed filename with YAML frontmatter is parseable at a known path, editable in any Markdown frontend, and carries human prose in the same file — and naming it `megabrain.md` means an instance is identifiable at a glance, the way a repository with an `AGENTS.md` is.

## 8. Agent runtime contract

### 8.1 The agent root

**[R-1]** `AGENTS.md` MUST describe what the repository is, MUST state the working rules that apply when no procedure matches, and MUST contain a dispatch table mapping user intent to procedure files.

**[R-2]** Harness-specific instruction files MAY exist. Each MUST delegate all shared behavior to `AGENTS.md` rather than restating it, so that the two cannot drift apart.

**[R-15]** A harness shim MAY contain instructions genuinely required for that harness to function, and MAY contain procedures that only that harness can perform — scheduling, background execution, a tool another harness lacks. This is the correct home for such instructions.

**[R-16]** Behavior depending on a capability that not every harness has MUST NOT appear in `AGENTS.md`. `AGENTS.md` MUST remain fully executable by a harness whose only capabilities are reading and writing files. Harnesses MAY therefore differ in *how* and *whether* an operation is performed; they MUST NOT differ in the schema, the archetypes, or the completion protocol.

> **Rationale (non-normative).** A harness that cannot schedule anything should never read an instruction telling it to schedule something — it will either fail or improvise. Pushing capability-dependent behavior down into shims keeps the shared root executable everywhere, while letting a capable harness do more. The invariant is not "every harness behaves identically", it is "no harness is asked to do what it cannot, and none of them can change the data contract".

**[R-3]** `AGENTS.md` SHOULD remain short enough to be read in full at the start of every session. Detail belongs in procedures.

**[R-17]** `AGENTS.md` MUST follow this skeleton, in this order, with no section omitted:

1. **Identity** — one paragraph: what this repository is, and that it is a megabrain.
2. **Manifest pointer** — that `megabrain.md` holds the instance's declarations, and that it MUST be read before acting on anything structural.
3. **Dispatch table** — intent to procedure file, with several phrasings per row ([R-6]).
4. **The re-read rule** — [R-4] and [R-5], stated in substance.
5. **Working rules** — the fallback behavior when no row matches ([R-7]), including the write-safety rules of §8.4.
6. **Version control** — the content/contract split of §11.

**[R-18]** Instance-specific configuration, vocabularies, and domain knowledge MUST NOT appear in `AGENTS.md`. They belong in the manifest, in background-context notes, or in procedures. Two conforming instances' `AGENTS.md` files MUST differ only in their dispatch rows.

> **Rationale (non-normative).** A fixed skeleton makes conformance checkable instead of a judgment call, and means an agent entering an unfamiliar instance finds the same information in the same order every time. The rigidity costs nothing, because everything that legitimately varies between two people has somewhere else to live: the manifest for declarations, procedures for behavior, domain packs for anything peculiar to one life.

### 8.2 Dispatch

**[R-4]** When a request matches a dispatch table row, the agent MUST read that procedure file in full **in the current turn**, before making any tool call or file write covered by it.

**[R-5]** [R-4] applies even when the same procedure was read earlier in the same conversation or in a previous session. Procedures change between sessions; a remembered procedure is not a substitute for the file.

**[R-6]** Dispatch MUST match on intent, not on exact wording. The dispatch table SHOULD show several differently-phrased requests that route to the same procedure.

**[R-7]** When no row matches, the agent MUST fall back to the working rules in `AGENTS.md` rather than improvising a procedure.

> **Rationale (non-normative).** [R-4] and [R-5] are what make behavior reproducible across harnesses, models, and sessions. Without the in-turn re-read, an agent runs on a half-remembered version of a procedure that may have been rewritten since, and two sessions asked the same question produce different work.

### 8.3 Procedures

**[R-8]** Each procedure MUST cover exactly one operation, MUST state when it applies, and MUST state explicitly what to do when it cannot complete — consistent with [C-12].

**[R-9]** Procedures MUST be layered, and the layering MUST be visible in the repository structure and declared in the manifest:

- **Core procedures** — portable, shipped with the standard, containing no instance configuration.
- **Integration adapters** — one per external system, portable in procedure, configured from the manifest ([M-3]).
- **Domain packs** — procedures specific to one person's life areas. Pure instance content.

**[R-10]** A core procedure MUST contain no instance configuration and MUST NOT assume any domain, integration, or entity type exists beyond what it reads from the manifest.

**[R-11]** A procedure that depends on a manifest value MUST name that value, so that an instance missing it fails visibly rather than silently.

### 8.4 Write safety

**[R-12]** An agent MUST preserve user-written content and MUST NOT rewrite prose it did not author except when the request is to edit that prose.

**[R-13]** An agent MUST NOT modify priorities, statuses, or due dates as a side effect of a read-only request such as a briefing or a lookup.

**[R-14]** An agent MUST report the path of every note it creates or modifies, and the metadata it set.

## 9. Integration contract

The contract is standard; the adapters are instance.

**[I-1]** Every integration MUST be declared in the manifest with a system identifier used for external identifiers ([S-13]).

**[I-2]** Every integration MUST declare an **intake mode**:

- **`sweep`** — the agent MAY query it proactively as part of periodic procedures such as a daily briefing.
- **`on_demand`** — the agent MUST NOT query it unless the user asks about it in the moment, MUST NOT propose its records as capture candidates on its own, and MUST NOT fold it into periodic procedures.

**[I-3]** Intake MUST follow: query live → deduplicate on external identifier ([S-15]) → present candidates with enough context to decide → **wait for explicit approval** → write. Steps MUST NOT be skipped or reordered ([C-9]).

**[I-4]** Presented results MUST distinguish live data from repository content, and MUST state the scope of the query performed when a narrower or broader scope than the default was used.

**[I-5]** When a query fails or returns nothing, the agent MUST report that and stop the operation. It MUST NOT fall back to remembered values, and MUST NOT present repository content as if it were live ([C-12]).

**[I-6]** Each integration MUST declare a **write policy** in the manifest:

- **`read_only`** — the agent MUST NOT write to the system at all.
- **`on_request`** — the agent MAY write when the user asks for that exact action in the moment.
- **`autonomous`** — the agent MAY write as part of a declared procedure, without a per-action request.

An integration with no declared write policy MUST be treated as `read_only`.

**[I-8]** An `autonomous` policy MUST enumerate the specific operations authorized — replying to a message, transitioning a record, updating a field — and the agent MUST NOT perform an external write outside that set. Every external write MUST be reported to the user, whatever the policy. Write policy governs the external system only: authorization to write *out* is never authorization to create notes in the brain without approval ([C-9]).

**[I-7]** An adapter MUST record the reasoning behind any non-obvious query scoping it uses, so that the scoping can be re-evaluated rather than cargo-culted into the next instance.

## 10. Lifecycle and completion

**[L-1]** Each archetype with a status vocabulary MUST identify at least one terminal status in the manifest.

**[L-2]** On reaching a terminal status, an entity MUST be logged: one dated line appended to an append-only log (§5.4), stating what was completed, its domain, and the terminal status it reached.

**[L-3]** After logging, the note MUST be either deleted or moved to an archive location. The choice is the instance's, and MUST be declared in the manifest.

**[L-4]** An archived note retains its archetype and its frontmatter. Archiving MUST NOT rewrite the note's content.

**[L-5]** Logging MUST precede deletion or archiving. A completed entity that was never logged is a data loss event, not a completed entity.

**[L-6]** Captured external material (§5.6) MUST NOT be logged to the completion log. The log records work that closed, not material that was read.

## 11. Version control contract

**[G-1]** The repository MUST be a git repository, and the working tree MUST be the source of truth ([C-2]).

**[G-2]** An agent MAY commit changes to the **content layer**: notes, logs, journals, archives.

**[G-3]** An agent MUST NOT commit changes to the **contract layer** — the manifest, `AGENTS.md`, procedures, the archetype declarations, or the schema — without the user's explicit approval in the moment. Such changes SHOULD be left in the working tree with a summary of what changed, for the user to review.

**[G-4]** Commits made by an agent SHOULD identify the agent, using a trailer naming the harness actually running rather than a hardcoded name.

**[G-5]** Environment-specific workarounds — sandbox quirks, lock-file handling, platform-specific commands — MUST NOT appear in this specification or in any core procedure. They belong in instance-local notes.

> **Rationale (non-normative).** [G-3] is what keeps the contract human-owned. An agent that can silently commit a change to its own instructions can drift the instance without review, and the drift is invisible precisely because it is committed.

## 12. Frontend and canonical views

**[V-1]** A frontend MUST NOT be required to read or write an instance. Any frontend is optional and replaceable.

**[V-2]** The schema MUST be sufficient to render the canonical views below **without any additional tagging, indexing, or per-note markup** beyond the frontmatter this specification defines:

1. **Active work by domain** — all non-terminal notes of the ephemeral-work-item archetype, grouped by `domain`. Required of every instance.
2. **Durable entities by domain** — all notes of the durable-entity archetype, grouped by `domain`, showing status and, if declared, `progress`.
3. **Due soon** — all non-terminal notes carrying `due`, ordered by date. Required only of instances declaring `due`.
4. **Calendar** — the same set placed on a calendar by `due`. Required only of instances declaring `due`.

**[V-3]** If a view listed in [V-2] cannot be rendered from frontmatter alone, the instance's schema is non-conforming — the failure is in the schema, not in the frontend.

> **Note (non-normative).** [V-2] doubles as the practical conformance test. It is deliberately weaker than an earlier formulation that required all four views unconditionally: `due` is an optional profile field, and an instance that tracks no deadlines is not thereby non-conforming. Views 1 and 2 depend only on `domain` and `status`, which are the keys [S-1] and [S-2] guarantee.

## 13. Extension points

Four sanctioned axes of divergence. Divergence outside these axes is non-conforming.

**[X-1] Domains.** The domain vocabulary is open and MUST be declared by the instance ([M-2.3]). This specification MUST NOT define an allowed set of domains; any set appearing in documentation is illustration only.

**[X-2] Entity types.** An instance MAY define any entity directories it needs. Each MUST declare its archetype ([A-0]). The archetype set (§5) is closed; the directories are not.

**[X-3] Procedures.** An instance MAY add procedures freely, and MUST place each in the correct layer ([R-9]). Domain packs are unrestricted.

**[X-4] Integrations.** An instance MAY enable any integrations. The contract in §9 is fixed; the adapters are instance content.

## 14. Extending an instance

An instance grows: a new domain, a new entity type, a new integration, a new procedure. Extension is where conformance breaks in practice, because extensions are usually made by an agent acting on a request phrased in terms of the user's life — "start tracking my grant deadlines" — rather than in terms of the schema.

**[E-1]** An agent MUST NOT create a directory of notes that is not declared in the manifest. Creating the directory and declaring it are one operation, not two.

**[E-2]** Adding an entity type MUST follow this order: choose the archetype (§5) → choose the status vocabulary and identify its terminal statuses, where the archetype requires one → declare path, archetype, and vocabulary in the manifest → then create the directory and its first note.

**[E-3]** Adding a domain MUST mean adding it to the manifest's domain vocabulary before any note carries it. Adding an integration MUST follow §9, including its system identifier, intake mode, and write policy. Adding a procedure MUST place it in the correct layer (§8.3).

**[E-4]** An instance MUST ship its extension procedure as a core procedure — conventionally `extend-brain` — reachable from the dispatch table in `AGENTS.md`. Requests to start tracking something new MUST route to it.

**[E-5]** An instance MUST NOT require any agent to read this specification at runtime in order to stay conforming. Conformance is carried by `AGENTS.md`, the manifest, and the procedures. This document is for people building instances and tools, not a file agents consult during ordinary work.

> **Rationale (non-normative).** [E-5] is why [E-4] exists. A copy of this specification sitting in every instance would be read at the wrong moments — consuming context on unrelated requests — and still skipped at the one moment it mattered, because nothing would route to it. Encoding the rules as a procedure that the dispatch table points at means the specification enforces itself exactly when someone extends the brain, and stays out of the way otherwise. It is the same mechanism as [R-4]: behavior lives in procedures, and procedures are read when they apply.

## 15. Conformance

An instance conforms to this specification when it satisfies every **MUST** requirement above.

A conformance check consists of:

1. **Structure** — a git repository of Markdown notes with a `megabrain.md` manifest and an `AGENTS.md` at the root, the latter following the skeleton of [R-17] ([C-1], [C-3], [M-1]).
2. **Declaration** — every note directory declared with an archetype; every status vocabulary declared with terminal statuses; every procedure-required configuration value present in the manifest ([A-0], [L-1], [M-2], [M-3]).
3. **Schema** — every entity note carries a declared `domain` and a `date_added`; every note in a status-bearing archetype carries a declared `status`; every `declared`-type key resolves against the manifest; no note carries a reserved key with a non-reserved meaning ([S-1], [S-2], [S-9], [S-16], [S-17]).
4. **Views** — the applicable canonical views render from frontmatter alone ([V-2]).
5. **Extension** — every note directory is declared, and the instance ships an extension procedure reachable from the dispatch table ([E-1], [E-4]).
6. **Contract portability** — no core procedure contains a value that would differ in another instance ([R-10], [M-3]).

An instance MAY be checked mechanically for items 1–5. Item 6 requires reading the procedures.

## Appendix A — Illustrative frontmatter (non-normative)

Nothing below is required. These are examples of instances filling the schema, not a field set to copy.

An ephemeral work item in an instance that declares `priority` as an enumeration and `progress` as a percentage:

```yaml
---
domain: work
status: in_progress
date_added: 2026-07-02
priority: high
due: 2026-07-14
progress: 40
external_id: tracker:PROJ-123
---
```

The same archetype in an instance that declares `priority` as an integer and `progress` as an enumeration — equally conforming, because both declared their types ([S-17]):

```yaml
---
domain: teaching
status: in_progress
date_added: 2026-07-02
priority: 80
progress: nearly_there
---
```

A captured external in an instance that declares `tags` and `related`:

```yaml
---
domain: research
status: unread
source_url: https://example.org/paper
date_added: 2026-07-13
related: [projects/thesis.md]
---
```

A structured record in a measurement series — all observation values as keys, no prose required:

```yaml
---
domain: health
date_added: 2026-06-18
date: 2026-06-18
weight_kg: 78.2
body_fat_pct: 15.9
waist_cm: 79.5
---
```

`date` and `date_added` coincide when a record is filed the day it is observed, and diverge when it is filed later — which is exactly why both exist.

## Appendix B — Illustrative archetype mappings (non-normative)

Two instances with nothing in common, both conforming. The left column is the only thing they share.

| Archetype | An engineer who also studies | A professor |
|---|---|---|
| Ephemeral work item | `tasks/` | `tasks/` |
| Durable entity | `projects/` | `courses/`, `advisees/`, `papers/`, `grants/` |
| Background context | `context/` per domain | `context/` per domain |
| Append-only log | `history.md` | `history.md` |
| Dated series (prose) | `journal/` | `journal/` |
| Dated series (record) | body measurements | advising meetings, assessments |
| Captured external | `reading/` | `reading/`, much heavier |
| Derived view | a home note, a dashboard | a teaching-load dashboard |

Their manifests differ in every value and in no key.

## Appendix C — Out of scope (non-normative)

This specification does not define, and MUST NOT be extended to define: any person's domain vocabulary; the content of context notes; any particular integration's API usage; the language prose is written in; a frontend's plugins, themes, or query syntax; a note-editing UI; a synchronization service; conflict resolution beyond what git provides; or any environment-specific instruction.

## Changelog

- **0.1.0** — initial release. Extracted from a working instance spanning engineering, graduate study, and personal-health domains, and refined through two annotation rounds before release.
