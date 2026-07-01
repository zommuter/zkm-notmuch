# zkm-notmuch architecture

Design decisions with rationale and rejected alternatives. Companion to
`CLAUDE.md` (operational facts) and `ROADMAP.md` (open work).

## What this plugin is

A frontmatter **amender**: it never creates md files and never touches md
bodies. It reads the authoritative tag state from the notmuch Xapian database
and syncs user-defined tags into the `tags:` list of mail messages that
zkm-eml already converted (additions AND attribution-aware removals — see D1). `creates_dirs: []` and `convert()` returns `[]` —
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
- applies fields per core rules — since the f103 migration (2026-06-24) the
  plugin emits **declarative full-set asserts** (`emit_set`, mode `"set"`):
  core diffs notmuch's previously stored set against the newly asserted one
  and retracts values whose ref-count drops to zero, so a tag deleted in
  notmuch disappears from frontmatter IFF notmuch was its sole producer —
  user/eml-authored tags are never retracted,
- appends the applied record to the per-md attribution sidecar
  (`<md>.amendments.json`),
- leaves unresolvable records queued ("run again after zkm-eml to resolve").

Rejected: writing frontmatter directly with `python-frontmatter` (the v0.0.x
prototype approach) — no attribution, no ordering guarantee, no pending queue
for mail that hasn't been converted yet. zkm-notmuch was the first amender and
effectively co-designed this contract.

Idempotence falls out of the engine: `emit_set` hashes (key, fields,
emitted_by, mode) to a stable filename, and `apply_queue` skips records whose hash
is already in the sidecar. Re-running `zkm convert notmuch` with an unchanged
database produces no diff.

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

Former sharp edge, fixed (df4e, 2026-06-13): an explicitly empty
`tags_exclude: []` now means "exclude nothing"; the built-in defaults apply
only when the key is absent (or an empty string).

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

Both former gaps closed 2026-06-13: `plugin.yaml` declares `kind: amender`
(d0e9), so core auto-runs this plugin after eml converts; and `convert()`
declares `created` (c353), so those auto-runs are scoped to the just-converted
batch (full-dump *reading* stays inherent to D2 — scoping filters the emit
loop and avoids queueing unresolvable records for mail outside the batch).

## Known limitations (deliberate, for now)

- **No notmuch-side writeback**: tags added in zkm frontmatter are never pushed
  into notmuch. One-way by design; notmuch is the tag source of truth for mail.

Former limitations, since shipped: tag removals now propagate via `emit_set`'s
attribution-aware retraction (f103, 2026-06-24; see D1) and notmuch CLI
failures raise actionable `RuntimeError`s — naming the missing binary, or
including the captured stderr on a non-zero exit (1af4, 2026-06-13).
