# zkm-notmuch architecture

Design decisions with rationale and rejected alternatives. Companion to
`CLAUDE.md` (operational facts) and `ROADMAP.md` (open work).

## What this plugin is

A frontmatter **amender**: it never creates md files and never touches md
bodies. It reads the authoritative tag state from the notmuch Xapian database
and merges user-defined tags into the `tags:` list of mail messages that
zkm-eml already converted. `creates_dirs: []` and `convert()` returns `[]` —
both are deliberate signals of the amender pattern.

## Decision log

### D1 — Amend via zkm.amendments, not direct frontmatter writes

The md frontmatter is multi-producer (eml writes it first, notmuch adds tags,
zkm-ner adds entities). Direct read-modify-write from each producer would race
and lose attribution. Instead this plugin **emits** amendment records
(`<store>/.zkm-state/amendments/notmuch/<sha1>.json`) and calls core's
`apply_queue`, which:

- resolves each record's `key.message_id` against a one-shot index of all md
  frontmatter,
- merges fields per core rules (`tags` = set-union, sorted),
- appends the applied record to the per-md attribution sidecar
  (`<md>.amendments.json`),
- leaves unresolvable records queued ("run again after zkm-eml to resolve").

Rejected: writing frontmatter directly with `python-frontmatter` (the v0.0.x
prototype approach) — no attribution, no ordering guarantee, no pending queue
for mail that hasn't been converted yet. zkm-notmuch was the first amender and
effectively co-designed this contract.

Idempotence falls out of the engine: `emit` hashes (key, fields, emitted_by)
to a stable filename, and `apply_queue` skips records whose hash is already in
the sidecar. Re-running `zkm convert notmuch` with an unchanged database
produces no diff.

### D2 — Read tags via `notmuch dump --format=batch-tag` subprocess

One subprocess call returns the complete tag state for the whole database in a
line-oriented, stable, documented format (`+tag1 +tag2 -- id:MESSAGE-ID`,
`#`-prefixed header comments).

Rejected alternatives:

- **notmuch Python bindings** (`notmuch2`): CFFI bindings version-locked to the
  system libnotmuch; would couple the plugin venv to the host's notmuch
  install and break the sealed-uv-tool install path. A subprocess only needs
  the binary on PATH.
- **Per-message `notmuch search --output=tags id:...`**: one subprocess per
  message — O(n) process spawns vs one dump. The dump's full-database scope is
  fine because amendment emit is idempotent and cheap.
- **`notmuch dump --format=sup`**: legacy format, weaker quoting guarantees.

Parsing notes encoded in `_parse_batch_tag`: header comment lines are skipped;
lines without ` -- id:` are ignored (defensive); only `+tag` entries are
collected (`-tag` never appears in dump output but is tolerated).

### D3 — Message-ID normalisation: bracket on the plugin side

notmuch stores Message-IDs WITHOUT angle brackets; zkm-eml stores
`message_id: <id>` WITH brackets (raw RFC 5322 form). The amendment key must
match the frontmatter exactly, so `_normalise_mid` wraps bare IDs in `<...>`
before emitting. Already-bracketed IDs (rare, but notmuch passes through some
malformed mail) are left untouched.

Rejected: normalising on the zkm-eml side (stripping brackets there) — eml's
`message_id` is shared by other consumers (threading, dedup) and the raw form
is the safer canonical one; the consumer with the deviant form adapts.

### D4 — Tag exclusion list, default-deny for notmuch system tags

notmuch maintains workflow/system tags (`inbox`, `unread`, `attachment`,
`signed`, `encrypted`, `replied`, `passed`, `flagged`, `deleted`, `sent`) that
are mail-client state, not knowledge categorisation. They are excluded by
default; user content tags (`bill`, `receipt`, ...) pass through. The list is
configurable (`tags_exclude`) because users may define their own
workflow-only tags.

Chosen direction: **exclusion list** (deny-list) rather than an allow-list —
the set of system tags is small and closed; the set of user tags is open.
Messages whose tags are ALL excluded get no amendment record at all (no empty
emits).

Known sharp edge (roadmap df4e): an explicitly empty `tags_exclude: []`
currently falls back to the built-in defaults, so a user cannot opt into
"exclude nothing".

### D5 — Shim + package split (SB5 repackage)

Since v0.3.0 the implementation lives in `src/zkm_notmuch/convert.py` and the
repo-root `convert.py` is a one-line re-export shim. Rationale: core's
entry-point (wheel) discovery imports the `zkm_notmuch` package, while its
filesystem (dev-symlink) discovery file-loads the repo-root `convert.py`; both
paths must reach the same code. The cost is duplicated `plugin.yaml` manifests
(root + package) that must stay identical — guarded by `tests/test_consistency.py`.

Consequence to respect: tests and any new code must import/patch
`zkm_notmuch.convert` (the real module), never the root shim — patching
`convert.subprocess` patches nothing the implementation uses. (The original
test suite broke exactly this way after the repackage; repaired in the
2026-06-12 relay turn.)

### D6 — Amender invocation contract (core-side, documented here for executors)

- Core auto-runs every plugin with `kind: amender` after a converter run that
  created files; `--no-amenders` opts out; a 0-files-created run skips amenders
  and reports the pending-amendment count.
- Core capability-probes `convert()` via `inspect.signature`: a `progress`
  parameter gets a progress callback; a `created` parameter gets the list of
  files the triggering converter created (amender scoping, core id:63bb).
  Explicit `zkm convert notmuch` passes `created=None` → full sweep. Plugins
  without the parameter keep working (probe, not protocol bump).

Current gaps (both on the roadmap):

- `plugin.yaml` lacks `kind: amender` → core classifies this plugin as a
  converter and **never auto-runs it** after eml converts (d0e9).
- `convert()` declares `progress` but not `created` → no scoping; every
  invocation emits for the entire notmuch database (c353). Full-dump reading
  is inherent to D2 either way; scoping limits *emits* (and avoids queueing
  unresolvable records for mail outside the just-converted batch).

## Known limitations (deliberate, for now)

- **Tag removal does not propagate** (roadmap f103, HARD): the amendment engine
  only merges (set-union for `tags`); a tag deleted in notmuch stays in
  frontmatter forever. A removal design needs attribution-aware reconciliation
  (only retract tags this plugin contributed, using the sidecar's
  `emitted_by: notmuch` records) and probably a core-level removal semantic —
  cross-repo, judgment-heavy.
- **No notmuch-side writeback**: tags added in zkm frontmatter are never pushed
  into notmuch. One-way by design; notmuch is the tag source of truth for mail.
- **subprocess failures surface raw** (roadmap 1af4): a missing notmuch binary
  raises bare `FileNotFoundError`; a failed dump raises `CalledProcessError`
  with no hint. Both should become actionable error messages.
