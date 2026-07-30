#!/usr/bin/env python3
"""megabrain tooling: the conformance checker and the lock-file writer.

This is a managed file. It is replaced wholesale on upgrade, and local edits
are overwritten -- they survive only in git history [D-3].

Subcommands
-----------
  doctor        validate the instance against the spec_version it declares
  lock write    stamp .megabrain/lock.json (installer and upgrade only, [D-5])
  lock verify   report managed-file drift against the lock

Only the Python standard library is used, so an instance needs nothing but a
python3 on PATH.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

LOCK_PATH = Path(".megabrain/lock.json")
MANIFEST_PATH = Path("megabrain.md")
AGENTS_PATH = Path("AGENTS.md")

ARCHETYPES = {
    "ephemeral_work_item",
    "durable_entity",
    "background_context",
    "append_only_log",
    "dated_series",
    "captured_external",
    "derived_view",
}

# Archetypes that must declare a status vocabulary, per 5.1, 5.2 and 5.6.
STATUS_BEARING = {"ephemeral_work_item", "durable_entity", "captured_external"}

# Archetypes whose notes are not entity notes and carry no frontmatter.
NO_FRONTMATTER = {"append_only_log"}

RESERVED_KEYS = {
    "domain": "string",
    "status": "string",
    "external_id": "string_or_list",
    "due": "date",
    "priority": "declared",
    "progress": "declared",
    "source_url": "string",
    "date_added": "date",
    "related": "list",
    "tags": "list",
}

REQUIRED_MANIFEST_KEYS = [
    "spec_version",
    "timezone",
    "domains",
    "entities",
    "fields",
    "integrations",
    "skills",
    "frontends",
    "filename_date_format",
]

ISO_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
KEBAB = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*\.md$")
DATE_FORMAT_TOKENS = {"YYYY": r"\d{4}", "MM": r"\d{2}", "DD": r"\d{2}"}


# --------------------------------------------------------------------------
# A YAML subset parser.
#
# The specification constrains frontmatter to nested mappings, block and flow
# sequences, and plain scalars ([M-4] and 6.2). That subset is small enough to
# parse directly, which keeps the checker dependency-free -- PyYAML is not in
# the standard library, so any route here means writing a parser.
# --------------------------------------------------------------------------


class YamlError(ValueError):
    pass


def _strip_comment(text: str) -> str:
    """Remove a trailing `# ...` comment, respecting quotes."""
    quote = None
    for i, ch in enumerate(text):
        if quote:
            if ch == quote:
                quote = None
        elif ch in "\"'":
            quote = ch
        elif ch == "#" and (i == 0 or text[i - 1] in " \t"):
            return text[:i]
    return text


def _scalar(raw: str):
    text = _strip_comment(raw).strip()
    if not text:
        return None
    if len(text) >= 2 and text[0] == text[-1] and text[0] in "\"'":
        return text[1:-1]
    if text.startswith("[") and text.endswith("]"):
        inner = text[1:-1].strip()
        if not inner:
            return []
        return [_scalar(part) for part in inner.split(",")]
    low = text.lower()
    if low in ("null", "~"):
        return None
    if low == "true":
        return True
    if low == "false":
        return False
    try:
        return int(text)
    except ValueError:
        pass
    try:
        return float(text)
    except ValueError:
        pass
    return text


def _lines(text: str):
    out = []
    for number, line in enumerate(text.splitlines(), start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            raise YamlError(f"line {number}: tab in indentation")
        out.append((len(line) - len(line.lstrip()), line.strip(), number))
    return out


BLOCK_SCALAR_INDICATORS = (">", ">-", ">+", "|", "|-", "|+")


def _parse_block_scalar(items, index: int, parent_indent: int, indicator: str):
    """Consume a literal (`|`) or folded (`>`) block scalar.

    Blank lines and full-line comments were already dropped by _lines, so
    the joined text is an approximation of the YAML value -- adequate for
    the prose notes declarations carry, not a faithful scalar round-trip.
    """
    chunks = []
    while index < len(items) and items[index][0] > parent_indent:
        chunks.append(items[index][1])
        index += 1
    if indicator.startswith("|"):
        return "\n".join(chunks), index
    return " ".join(chunks), index


def _parse_block(items, index: int, indent: int):
    if index >= len(items):
        return None, index
    if items[index][1].startswith("- "):
        return _parse_sequence(items, index, indent)
    return _parse_mapping(items, index, indent)


def _parse_sequence(items, index: int, indent: int):
    result = []
    while index < len(items):
        level, content, number = items[index]
        if level < indent or not content.startswith("- "):
            break
        if level > indent:
            raise YamlError(f"line {number}: unexpected indentation")
        rest = content[2:].strip()
        index += 1
        if not rest:
            value, index = _parse_block(items, index, level + 1)
            result.append(value)
        elif ":" in rest and not rest.startswith(("[", '"', "'")):
            # An inline mapping opening a sequence entry.
            synthetic = [(level + 2, rest, number)] + items[index:]
            value, consumed = _parse_mapping(synthetic, 0, level + 2)
            index += consumed - 1
            result.append(value)
        else:
            result.append(_scalar(rest))
    return result, index


def _parse_mapping(items, index: int, indent: int):
    result = {}
    while index < len(items):
        level, content, number = items[index]
        if level < indent:
            break
        if level > indent:
            raise YamlError(f"line {number}: unexpected indentation")
        if content.startswith("- "):
            break
        if ":" not in content:
            raise YamlError(f"line {number}: expected 'key: value'")
        key, _, rest = content.partition(":")
        key = key.strip()
        rest = rest.strip()
        index += 1
        if rest and not rest.startswith("#"):
            if rest in BLOCK_SCALAR_INDICATORS:
                result[key], index = _parse_block_scalar(items, index, level, rest)
            else:
                result[key] = _scalar(rest)
            continue
        if index < len(items) and items[index][0] > level:
            result[key], index = _parse_block(items, index, items[index][0])
        elif index < len(items) and items[index][1].startswith("- ") and items[index][0] == level:
            # A block sequence indented flush with its key.
            result[key], index = _parse_sequence(items, index, level)
        else:
            result[key] = None
    return result, index


def parse_yaml(text: str) -> dict:
    items = _lines(text)
    if not items:
        return {}
    value, _ = _parse_block(items, 0, items[0][0])
    return value if isinstance(value, dict) else {}


def split_frontmatter(text: str):
    """Return (frontmatter_dict_or_None, body)."""
    if not text.startswith("---"):
        return None, text
    lines = text.split("\n")
    for i in range(1, len(lines)):
        if lines[i].strip() in ("---", "..."):
            return parse_yaml("\n".join(lines[1:i])), "\n".join(lines[i + 1 :])
    return None, text


# --------------------------------------------------------------------------
# Findings
# --------------------------------------------------------------------------


class Finding:
    def __init__(self, level: str, requirement: str, check: str, message: str):
        self.level = level  # "MUST" or "WARN"
        self.requirement = requirement
        self.check = check
        self.message = message

    def as_text(self) -> str:
        return f"{self.level:<4}  [{self.requirement}]  {self.check}: {self.message}"

    def as_dict(self) -> dict:
        return {
            "level": self.level,
            "requirement": self.requirement,
            "check": self.check,
            "message": self.message,
        }


class Instance:
    """Everything the checks read, loaded once."""

    def __init__(self, root: Path):
        self.root = root
        self.manifest = None
        self.manifest_error = None
        self.lock = None
        self.lock_error = None
        self._load()

    def _load(self):
        manifest_file = self.root / MANIFEST_PATH
        if manifest_file.is_file():
            try:
                front, _ = split_frontmatter(manifest_file.read_text(encoding="utf-8"))
                if front is None:
                    self.manifest_error = "no YAML frontmatter"
                else:
                    self.manifest = front
            except (YamlError, UnicodeDecodeError) as exc:
                self.manifest_error = str(exc)
        lock_file = self.root / LOCK_PATH
        if lock_file.is_file():
            try:
                self.lock = json.loads(lock_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                self.lock_error = str(exc)

    @property
    def spec_version(self) -> str:
        if isinstance(self.manifest, dict):
            value = self.manifest.get("spec_version")
            if value is not None:
                return str(value)
        return "0.0.0"

    @property
    def entities(self) -> dict:
        if isinstance(self.manifest, dict):
            value = self.manifest.get("entities")
            if isinstance(value, dict):
                return value
        return {}

    @property
    def domains(self) -> list:
        if isinstance(self.manifest, dict):
            value = self.manifest.get("domains")
            if isinstance(value, list):
                return [str(d) for d in value]
        return []

    def note_files(self, decl: dict):
        """Every .md note belonging to one entity declaration."""
        path = decl.get("path")
        if not path:
            return []
        target = self.root / str(path)
        if target.is_file():
            # A declared entity path that is not Markdown is not a note (2)
            # -- an Obsidian `.base` derived view, say -- so the note checks
            # (frontmatter, filenames) do not apply to it.
            return [target] if target.suffix == ".md" else []
        if not target.is_dir():
            return []
        return sorted(p for p in target.rglob("*.md") if p.is_file())

    def rel(self, path: Path) -> str:
        try:
            return str(path.relative_to(self.root))
        except ValueError:
            return str(path)


def version_tuple(value: str):
    parts = re.findall(r"\d+", value or "")
    nums = [int(p) for p in parts[:3]]
    while len(nums) < 3:
        nums.append(0)
    return tuple(nums)


# --------------------------------------------------------------------------
# The check registry.
#
# Each check is version-aware [D-18]: `since` is the earliest spec_version at
# which it applies, so a partially upgraded instance reports against the
# version it actually satisfies. Check ids are the vocabulary a migration
# step's `verify` field draws on [D-11].
# --------------------------------------------------------------------------

CHECKS = []


def check(check_id: str, item: int, since: str = "0.1.0"):
    def decorate(func):
        CHECKS.append(
            {"id": check_id, "item": item, "since": since, "run": func}
        )
        return func

    return decorate


# ---- Item 1: structure ----------------------------------------------------


@check("git-repo", 1)
def _git_repo(inst: Instance, out):
    if not (inst.root / ".git").exists():
        out.append(Finding("MUST", "C-1", "git-repo", "not a git repository"))


@check("manifest-present", 1)
def _manifest_present(inst: Instance, out):
    if not (inst.root / MANIFEST_PATH).is_file():
        out.append(Finding("MUST", "M-1", "manifest-present", "megabrain.md is missing from the repository root"))
    elif inst.manifest is None:
        out.append(
            Finding("MUST", "M-4", "manifest-present", f"megabrain.md frontmatter is unreadable: {inst.manifest_error}")
        )


@check("agents-present", 1)
def _agents_present(inst: Instance, out):
    if not (inst.root / AGENTS_PATH).is_file():
        out.append(Finding("MUST", "C-3", "agents-present", "AGENTS.md is missing from the repository root"))


@check("agents-skeleton", 1)
def _agents_skeleton(inst: Instance, out):
    path = inst.root / AGENTS_PATH
    if not path.is_file():
        return
    text = path.read_text(encoding="utf-8")
    headings = [h.strip().lower() for h in re.findall(r"^##\s+(.+)$", text, re.M)]
    expected = [
        ("identity", "identity"),
        ("manifest pointer", "manifest"),
        ("dispatch table", "dispatch"),
        ("the re-read rule", "re-read"),
        ("working rules", "working rules"),
        ("version control", "version control"),
    ]
    cursor = 0
    for label, needle in expected:
        found = None
        for i in range(cursor, len(headings)):
            if needle in headings[i] or needle.replace("-", "") in headings[i].replace("-", ""):
                found = i
                break
        if found is None:
            out.append(
                Finding("MUST", "R-17", "agents-skeleton", f"no section for '{label}' in the required order")
            )
        else:
            cursor = found + 1
    rows = _dispatch_rows(text)
    if not rows:
        out.append(Finding("MUST", "R-1", "agents-skeleton", "the dispatch table has no rows"))
    for intent, target in rows:
        if not (inst.root / target).is_file():
            out.append(
                Finding("MUST", "R-1", "agents-skeleton", f"dispatch row '{intent[:40]}' points at missing {target}")
            )


def _dispatch_rows(text: str):
    """Extract (intent, procedure path) pairs from the dispatch table."""
    rows = []
    for line in text.split("\n"):
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or "---|" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) < 2:
            continue
        target = re.search(r"`([^`]+\.md)`", cells[-1])
        if target:
            rows.append((cells[0], target.group(1)))
    return rows


@check("lock-present", 1, since="0.2.0")
def _lock_present(inst: Instance, out):
    if not (inst.root / LOCK_PATH).is_file():
        out.append(Finding("MUST", "D-4", "lock-present", ".megabrain/lock.json is missing"))
        return
    if inst.lock is None:
        out.append(Finding("MUST", "D-4", "lock-present", f".megabrain/lock.json is unreadable: {inst.lock_error}"))
        return
    for field in ("spec_version", "release", "source", "installed_at", "managed"):
        if field not in inst.lock:
            out.append(Finding("MUST", "D-4", "lock-present", f"lock file has no '{field}'"))
    if not isinstance(inst.lock.get("managed"), dict):
        out.append(Finding("MUST", "D-4", "lock-present", "lock file's 'managed' is not a map of path to hash"))
    for gray in ("AGENTS.md", "megabrain.md"):
        if isinstance(inst.lock.get("managed"), dict) and gray in inst.lock["managed"]:
            out.append(
                Finding("MUST", "D-2", "lock-present", f"{gray} is instance-owned and must not be in the hash map")
            )
    declared = inst.spec_version
    recorded = str(inst.lock.get("spec_version", ""))
    if recorded and declared and recorded != declared:
        out.append(
            Finding(
                "MUST",
                "D-6",
                "lock-present",
                f"lock records spec_version {recorded} but the manifest declares {declared}",
            )
        )


# ---- Item 2: declaration --------------------------------------------------


@check("manifest-required-keys", 2)
def _manifest_required_keys(inst: Instance, out):
    if not isinstance(inst.manifest, dict):
        return
    for key in REQUIRED_MANIFEST_KEYS:
        if key not in inst.manifest:
            out.append(Finding("MUST", "M-2", "manifest-required-keys", f"the manifest does not declare '{key}'"))
    tz = inst.manifest.get("timezone")
    if tz is not None and not re.match(r"^(UTC|[A-Za-z_]+/[A-Za-z0-9_+\-/]+)$", str(tz)):
        out.append(
            Finding("MUST", "S-7", "manifest-required-keys", f"timezone '{tz}' is not an IANA timezone identifier")
        )
    if not inst.domains and "domains" in inst.manifest:
        out.append(Finding("MUST", "M-2", "manifest-required-keys", "the domain vocabulary is empty"))


@check("entities-declared", 2)
def _entities_declared(inst: Instance, out):
    if not isinstance(inst.manifest, dict):
        return
    if not inst.entities:
        out.append(Finding("MUST", "M-2", "entities-declared", "the manifest declares no entity directories"))
    for name, decl in inst.entities.items():
        if not isinstance(decl, dict):
            out.append(Finding("MUST", "A-0", "entities-declared", f"entity '{name}' is not a declaration block"))
            continue
        if not decl.get("path"):
            out.append(Finding("MUST", "M-2", "entities-declared", f"entity '{name}' declares no path"))
        archetype = decl.get("archetype")
        if not archetype:
            out.append(Finding("MUST", "A-0", "entities-declared", f"entity '{name}' declares no archetype"))
        elif archetype not in ARCHETYPES:
            out.append(
                Finding("MUST", "A-0", "entities-declared", f"entity '{name}' declares unknown archetype '{archetype}'")
            )
        elif archetype == "dated_series" and decl.get("flavor") not in ("prose", "record"):
            out.append(
                Finding("MUST", "A-5", "entities-declared", f"dated series '{name}' declares no flavor prose|record")
            )
        elif archetype == "derived_view" and not decl.get("sources"):
            out.append(Finding("MUST", "A-8", "entities-declared", f"derived view '{name}' declares no sources"))


@check("status-vocabularies", 2)
def _status_vocabularies(inst: Instance, out):
    for name, decl in inst.entities.items():
        if not isinstance(decl, dict):
            continue
        archetype = decl.get("archetype")
        vocab = decl.get("status_vocabulary")
        terminal = decl.get("terminal_statuses")
        if archetype in STATUS_BEARING:
            if not isinstance(vocab, list) or not vocab:
                out.append(
                    Finding("MUST", "A-1", "status-vocabularies", f"entity '{name}' declares no status vocabulary")
                )
                continue
            if not isinstance(terminal, list) or not terminal:
                out.append(
                    Finding("MUST", "L-1", "status-vocabularies", f"entity '{name}' identifies no terminal status")
                )
                continue
            stray = [s for s in terminal if s not in vocab]
            if stray:
                out.append(
                    Finding(
                        "MUST",
                        "L-1",
                        "status-vocabularies",
                        f"entity '{name}' terminal statuses {stray} are not in its vocabulary",
                    )
                )
            if decl.get("on_terminal") not in ("delete", "archive", "retain"):
                out.append(
                    Finding(
                        "MUST",
                        "L-3",
                        "status-vocabularies",
                        f"entity '{name}' declares no on_terminal of delete|archive|retain",
                    )
                )
        elif isinstance(vocab, list) and vocab and (not isinstance(terminal, list) or not terminal):
            out.append(
                Finding("MUST", "L-1", "status-vocabularies", f"entity '{name}' declares a vocabulary but no terminal status")
            )


@check("entity-paths-exist", 2)
def _entity_paths_exist(inst: Instance, out):
    for name, decl in inst.entities.items():
        if not isinstance(decl, dict) or not decl.get("path"):
            continue
        target = inst.root / str(decl["path"])
        if not target.exists():
            out.append(
                Finding("MUST", "M-2", "entity-paths-exist", f"entity '{name}' declares {decl['path']}, which does not exist")
            )


# ---- Item 3: schema -------------------------------------------------------


def _iter_entity_notes(inst: Instance):
    for name, decl in inst.entities.items():
        if not isinstance(decl, dict):
            continue
        archetype = decl.get("archetype")
        if archetype in NO_FRONTMATTER:
            continue
        for path in inst.note_files(decl):
            yield name, decl, archetype, path


def _field_decl(inst: Instance, key: str):
    fields = inst.manifest.get("fields") if isinstance(inst.manifest, dict) else None
    if isinstance(fields, dict):
        value = fields.get(key)
        if isinstance(value, dict):
            return value
    return None


@check("note-schema", 3)
def _note_schema(inst: Instance, out):
    domains = set(inst.domains)
    for name, decl, archetype, path in _iter_entity_notes(inst):
        rel = inst.rel(path)
        try:
            front, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (YamlError, UnicodeDecodeError) as exc:
            out.append(Finding("MUST", "C-1", "note-schema", f"{rel}: unreadable frontmatter: {exc}"))
            continue
        if front is None:
            out.append(Finding("MUST", "S-1", "note-schema", f"{rel}: no YAML frontmatter"))
            continue
        domain = front.get("domain")
        if domain is None:
            out.append(Finding("MUST", "S-1", "note-schema", f"{rel}: no 'domain'"))
        elif str(domain) not in domains:
            out.append(
                Finding("MUST", "S-1", "note-schema", f"{rel}: domain '{domain}' is not in the declared vocabulary")
            )
        added = front.get("date_added")
        if added is None:
            out.append(Finding("MUST", "S-16", "note-schema", f"{rel}: no 'date_added'"))
        elif not ISO_DATE.match(str(added)):
            out.append(Finding("MUST", "S-7", "note-schema", f"{rel}: date_added '{added}' is not YYYY-MM-DD"))
        vocab = decl.get("status_vocabulary")
        status = front.get("status")
        if isinstance(vocab, list) and vocab:
            if status is None:
                out.append(Finding("MUST", "S-2", "note-schema", f"{rel}: no 'status'"))
            elif str(status) not in [str(v) for v in vocab]:
                out.append(
                    Finding("MUST", "S-2", "note-schema", f"{rel}: status '{status}' is not in the vocabulary of '{name}'")
                )
        elif status is not None:
            out.append(
                Finding(
                    "MUST",
                    "S-2",
                    "note-schema",
                    f"{rel}: carries 'status' but '{name}' declares no status vocabulary",
                )
            )


def _declared_systems(inst: Instance):
    """System identifiers usable in an external_id ([S-13], [S-14]).

    Integrations may be declared as a map keyed by name or as a list of
    declaration blocks; both appear in real manifests. An instance declaring
    none has no valid system, so every external_id in it is undeclared.
    """
    systems = set()
    integrations = inst.manifest.get("integrations") if isinstance(inst.manifest, dict) else None
    blocks = []
    if isinstance(integrations, dict):
        systems |= {str(k) for k in integrations}
        blocks = list(integrations.values())
    elif isinstance(integrations, list):
        blocks = integrations
    for decl in blocks:
        if isinstance(decl, dict):
            if decl.get("system"):
                systems.add(str(decl["system"]))
            for key in decl:
                if str(key).endswith("_id"):
                    systems.add(str(key)[: -len("_id")])
    return systems


@check("reserved-keys", 3)
def _reserved_keys(inst: Instance, out):
    systems = _declared_systems(inst)
    for _name, _decl, _archetype, path in _iter_entity_notes(inst):
        rel = inst.rel(path)
        try:
            front, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (YamlError, UnicodeDecodeError):
            continue
        if not isinstance(front, dict):
            continue
        for key, value in front.items():
            kind = RESERVED_KEYS.get(key)
            if kind is None or value is None:
                continue
            if kind == "date" and not ISO_DATE.match(str(value)):
                out.append(Finding("MUST", "S-9", "reserved-keys", f"{rel}: '{key}' value '{value}' is not a date"))
            elif kind == "list" and not isinstance(value, list):
                out.append(Finding("MUST", "S-9", "reserved-keys", f"{rel}: '{key}' must be a list"))
            elif kind == "declared":
                _check_declared(inst, out, rel, key, value)
            if key == "related" and isinstance(value, list):
                for target in value:
                    if not (inst.root / str(target)).is_file():
                        out.append(
                            Finding("MUST", "S-12", "reserved-keys", f"{rel}: related path '{target}' does not exist")
                        )
            if key == "external_id":
                for ident in value if isinstance(value, list) else [value]:
                    if ":" not in str(ident):
                        out.append(
                            Finding("MUST", "S-13", "reserved-keys", f"{rel}: external_id '{ident}' is not 'system:id'")
                        )
                    elif str(ident).split(":", 1)[0] not in systems:
                        out.append(
                            Finding(
                                "MUST",
                                "S-13",
                                "reserved-keys",
                                f"{rel}: external_id '{ident}' names an undeclared system",
                            )
                        )


def _check_declared(inst: Instance, out, rel: str, key: str, value):
    decl = _field_decl(inst, key)
    if decl is None:
        out.append(
            Finding("MUST", "S-17", "reserved-keys", f"{rel}: '{key}' is used but the manifest declares no type for it")
        )
        return
    kind = str(decl.get("type", ""))
    if kind == "enum":
        vocab = decl.get("vocabulary")
        if not isinstance(vocab, list) or not vocab:
            out.append(Finding("MUST", "S-17", "reserved-keys", f"'{key}' is declared enum with no vocabulary"))
        elif str(value) not in [str(v) for v in vocab]:
            out.append(
                Finding("MUST", "S-17", "reserved-keys", f"{rel}: '{key}' value '{value}' is not in its vocabulary")
            )
    elif kind == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            out.append(Finding("MUST", "S-17", "reserved-keys", f"{rel}: '{key}' value '{value}' is not an integer"))
            return
        span = decl.get("range")
        if isinstance(span, list) and len(span) == 2 and not (span[0] <= value <= span[1]):
            out.append(
                Finding("MUST", "S-17", "reserved-keys", f"{rel}: '{key}' value {value} is outside {span}")
            )


@check("filenames", 3)
def _filenames(inst: Instance, out):
    exceptions = set()
    if isinstance(inst.manifest, dict):
        declared = inst.manifest.get("filename_exceptions")
        if isinstance(declared, list):
            exceptions = {str(e) for e in declared}
    fmt = str(inst.manifest.get("filename_date_format", "YYYY-MM-DD")) if isinstance(inst.manifest, dict) else "YYYY-MM-DD"
    date_re = _date_format_regex(fmt)
    for name, decl, archetype, path in _iter_entity_notes(inst):
        rel = inst.rel(path)
        if path.name in exceptions:
            continue
        if not KEBAB.match(path.name):
            out.append(Finding("MUST", "S-6", "filenames", f"{rel}: filename is not lowercase kebab-case"))
            continue
        if archetype == "dated_series" and not re.match(rf"^{date_re}\.md$", path.name):
            out.append(
                Finding("MUST", "S-8", "filenames", f"{rel}: dated-series filename does not match '{fmt}'")
            )
        elif archetype == "captured_external" and not re.match(rf"^{date_re}-.+\.md$", path.name):
            out.append(
                Finding("MUST", "S-8", "filenames", f"{rel}: capture filename is not '<{fmt}>-<slug>.md'")
            )


def _date_format_regex(fmt: str) -> str:
    pattern = ""
    i = 0
    while i < len(fmt):
        for token, expr in DATE_FORMAT_TOKENS.items():
            if fmt.startswith(token, i):
                pattern += expr
                i += len(token)
                break
        else:
            pattern += re.escape(fmt[i])
            i += 1
    return pattern


# ---- Item 4: views --------------------------------------------------------


@check("views", 4)
def _views(inst: Instance, out):
    """Verify the canonical views by computing them ([V-2], [V-3]).

    Views 1 and 2 need `domain` and `status` on every non-terminal note. Views
    3 and 4 need `due` to be a date, which `reserved-keys` already enforces --
    `due` is reserved with a fixed type (6.4), so unlike `priority` and
    `progress` it needs no declaration in `fields` to be usable.
    """
    for name, decl, archetype, path in _iter_entity_notes(inst):
        if archetype not in ("ephemeral_work_item", "durable_entity"):
            continue
        rel = inst.rel(path)
        try:
            front, _ = split_frontmatter(path.read_text(encoding="utf-8"))
        except (YamlError, UnicodeDecodeError):
            continue
        if not isinstance(front, dict):
            continue
        terminal = [str(t) for t in (decl.get("terminal_statuses") or [])]
        if str(front.get("status")) in terminal:
            continue
        # Views 1 and 2 group non-terminal notes by domain.
        if front.get("domain") is None:
            out.append(
                Finding("MUST", "V-3", "views", f"{rel}: cannot be placed in the by-domain view without 'domain'")
            )
        if front.get("status") is None and decl.get("status_vocabulary"):
            out.append(
                Finding("MUST", "V-3", "views", f"{rel}: cannot be placed in the active-work view without 'status'")
            )


# ---- Item 5: extension ----------------------------------------------------


@check("undeclared-directories", 5)
def _undeclared_directories(inst: Instance, out):
    declared = set()
    for decl in inst.entities.values():
        if isinstance(decl, dict) and decl.get("path"):
            declared.add(str(decl["path"]).strip("/"))
    skills_root = "skills"
    if isinstance(inst.manifest, dict):
        skills = inst.manifest.get("skills")
        if isinstance(skills, dict) and skills.get("root"):
            skills_root = str(skills["root"]).strip("/")
    ignored_roots = {".git", ".megabrain", "scripts", "docs", skills_root}
    for dirpath, dirnames, filenames in os.walk(inst.root):
        current = Path(dirpath)
        rel = inst.rel(current)
        if rel == ".":
            dirnames[:] = [d for d in dirnames if d not in ignored_roots and not d.startswith(".")]
            continue
        top = rel.split(os.sep)[0]
        if top in ignored_roots:
            dirnames[:] = []
            continue
        undeclared = [
            f for f in filenames
            if f.endswith(".md") and not _declared_note(declared, os.path.join(rel, f))
        ]
        if undeclared:
            out.append(
                Finding(
                    "MUST",
                    "E-1",
                    "undeclared-directories",
                    f"{rel}/ holds notes not declared in the manifest: {', '.join(sorted(undeclared))}",
                )
            )


def _declared_note(declared: set, rel_note: str) -> bool:
    """A note is declared if it is a declared file path itself or lives
    under a declared directory."""
    return any(rel_note == d or rel_note.startswith(d + os.sep) for d in declared)


@check("extension-procedure", 5)
def _extension_procedure(inst: Instance, out):
    path = inst.root / AGENTS_PATH
    if not path.is_file():
        return
    rows = _dispatch_rows(path.read_text(encoding="utf-8"))
    for _intent, target in rows:
        if "extend" in target and (inst.root / target).is_file():
            return
    out.append(
        Finding("MUST", "E-4", "extension-procedure", "no extension procedure is reachable from the dispatch table")
    )


# ---- Item 6: contract portability -----------------------------------------


@check("managed-hashes", 6, since="0.2.0")
def _managed_hashes(inst: Instance, out):
    """Compare managed files against the lock ([D-4], 16 item 6).

    Drift is reported but does not fail conformance: the file belongs to the
    standard, and the next upgrade replaces it [D-3]. A managed file that has
    gone missing is a genuine violation.
    """
    if not isinstance(inst.lock, dict):
        return
    managed = inst.lock.get("managed")
    if not isinstance(managed, dict):
        return
    for rel, expected in sorted(managed.items()):
        target = inst.root / rel
        if not target.is_file():
            out.append(Finding("MUST", "D-1", "managed-hashes", f"managed file {rel} is missing"))
            continue
        actual = sha256_file(target)
        if actual != expected:
            out.append(
                Finding(
                    "WARN",
                    "D-3",
                    "managed-hashes",
                    f"{rel} has drifted from the release; the next upgrade will overwrite it",
                )
            )


# --------------------------------------------------------------------------
# Lock file
# --------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_managed_list(path: Path):
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        entries.append(line)
    return entries


def cmd_lock_write(args) -> int:
    root = Path(args.root).resolve()
    managed_list = Path(args.managed_list).resolve()
    if not managed_list.is_file():
        print(f"error: managed list not found: {managed_list}", file=sys.stderr)
        return 2
    spec_version = args.spec_version
    if not spec_version:
        inst = Instance(root)
        spec_version = inst.spec_version
    managed = {}
    for rel in read_managed_list(managed_list):
        target = root / rel
        if not target.is_file():
            print(f"error: managed file declared by the release is missing: {rel}", file=sys.stderr)
            return 2
        managed[rel] = sha256_file(target)
    payload = {
        "spec_version": spec_version,
        "release": args.release,
        "source": args.source,
        "installed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "managed": dict(sorted(managed.items())),
    }
    lock_file = root / LOCK_PATH
    lock_file.parent.mkdir(parents=True, exist_ok=True)
    lock_file.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    print(f"wrote {LOCK_PATH} for spec_version {spec_version} ({len(managed)} managed files)")
    return 0


def cmd_lock_verify(args) -> int:
    root = Path(args.root).resolve()
    inst = Instance(root)
    if not isinstance(inst.lock, dict):
        print("error: no readable .megabrain/lock.json", file=sys.stderr)
        return 2
    managed = inst.lock.get("managed") or {}
    drifted, missing = [], []
    for rel, expected in sorted(managed.items()):
        target = root / rel
        if not target.is_file():
            missing.append(rel)
        elif sha256_file(target) != expected:
            drifted.append(rel)
    for rel in missing:
        print(f"missing  {rel}")
    for rel in drifted:
        print(f"drifted  {rel}")
    if not missing and not drifted:
        print(f"clean    {len(managed)} managed files match the lock")
    return 1 if missing else 0


# --------------------------------------------------------------------------
# Doctor
# --------------------------------------------------------------------------


def cmd_doctor(args) -> int:
    root = Path(args.root).resolve()
    inst = Instance(root)
    version = args.spec_version or inst.spec_version
    current = version_tuple(version)

    selected = CHECKS
    if args.only:
        wanted = {name.strip() for name in args.only.split(",") if name.strip()}
        unknown = wanted - {c["id"] for c in CHECKS}
        if unknown:
            print(f"error: unknown check(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2
        selected = [c for c in CHECKS if c["id"] in wanted]

    applicable = [c for c in selected if version_tuple(c["since"]) <= current]
    skipped = [c for c in selected if c not in applicable]

    findings = []
    for entry in applicable:
        try:
            entry["run"](inst, findings)
        except Exception as exc:  # a broken check must not look like a pass
            findings.append(
                Finding("MUST", "D-19", entry["id"], f"the check itself failed: {type(exc).__name__}: {exc}")
            )

    violations = [f for f in findings if f.level == "MUST"]
    warnings = [f for f in findings if f.level == "WARN"]

    if args.format == "json":
        print(
            json.dumps(
                {
                    "root": str(root),
                    "spec_version": version,
                    "checks_run": [c["id"] for c in applicable],
                    "checks_skipped": [c["id"] for c in skipped],
                    "violations": [f.as_dict() for f in violations],
                    "warnings": [f.as_dict() for f in warnings],
                    "conforming": not violations,
                },
                indent=2,
            )
        )
        return 1 if violations else 0

    print(f"megabrain doctor - {root}")
    print(f"checking against spec_version {version} ({len(applicable)} checks)")
    if skipped:
        print(f"not applicable at this version: {', '.join(c['id'] for c in skipped)}")
    print("")
    for finding in violations + warnings:
        print(finding.as_text())
    if violations or warnings:
        print("")
    if violations:
        print(f"FAIL  {len(violations)} MUST violation(s), {len(warnings)} warning(s)")
        return 1
    print(f"PASS  conforms to {version}" + (f", {len(warnings)} warning(s)" if warnings else ""))
    return 0


def cmd_list_checks(args) -> int:
    for entry in CHECKS:
        print(f"{entry['id']:<24} item {entry['item']}  since {entry['since']}")
    return 0


# --------------------------------------------------------------------------


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="megabrain", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    doctor = sub.add_parser("doctor", help="validate the instance against its declared spec_version")
    doctor.add_argument("--root", default=".", help="instance root (default: the working directory)")
    doctor.add_argument("--spec-version", default=None, help="override the version to check against")
    doctor.add_argument("--only", default=None, help="comma-separated check ids to run (see list-checks)")
    doctor.add_argument("--format", choices=("text", "json"), default="text")
    doctor.set_defaults(func=cmd_doctor)

    listing = sub.add_parser("list-checks", help="enumerate the check registry")
    listing.set_defaults(func=cmd_list_checks)

    lock = sub.add_parser("lock", help="lock-file operations (installer and upgrade only)")
    lock_sub = lock.add_subparsers(dest="lock_command", required=True)

    write = lock_sub.add_parser("write", help="stamp .megabrain/lock.json")
    write.add_argument("--root", default=".", help="instance root (default: the working directory)")
    write.add_argument("--release", required=True, help="release identifier, e.g. v0.2.0")
    write.add_argument("--source", required=True, help="distribution source the release came from")
    write.add_argument("--managed-list", required=True, help="path to the release's MANAGED file")
    write.add_argument("--spec-version", default=None, help="defaults to the manifest's spec_version")
    write.set_defaults(func=cmd_lock_write)

    verify = lock_sub.add_parser("verify", help="report managed-file drift")
    verify.add_argument("--root", default=".", help="instance root (default: the working directory)")
    verify.set_defaults(func=cmd_lock_verify)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
