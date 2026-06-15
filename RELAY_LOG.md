# Relay log <!-- merge=union; append-only — never edit or reorder past entries -->

## 2026-06-15 11:52 — hard-execute (claude-opus-4-8, fable-standin, relay-loop)

hard 20260615-1152: SIZED the only open [HARD] item id:f103 (propagate notmuch tag
REMOVALS to frontmatter) and DEFERRED it — too large for one bounded turn, no code
written, f103 stays open. HANDBACK below.

HANDBACK (id:f103, sizing): The item cannot finish cleanly+green in a single
single-repo turn for four interlocking reasons. (1) Cross-repo: the core dependency
is in a DIFFERENT repo (`~/src/zkm/src/zkm/amendments.py`), outside this child's
single-repo worktree; conventions.md mandates one subagent per repo. (2) Missing core
primitive: `zkm/amendments.py::merge_fields` implements tags as set-UNION ONLY
(`sorted(set(existing) | set(value))`, ~line 132) — `emit()` records additive fields,
there is NO retraction semantic. Removal requires a NEW core-level field-merge mode
(retract), a design decision with its own acceptance/tests/idempotence. (3)
Attribution-aware reconciliation: retract a tag ONLY if the `<md>.amendments.json`
sidecar attributes it to `emitted_by: notmuch`, never user-/eml-authored tags —
needs prior-attribution diffing. (4) Data-loss risk: wrongly retracting a
user-authored tag is destructive; a half-correct removal path is worse than leaving
it open (ROADMAP "Why HARD" note flags exactly this). The ROADMAP acceptance is an
explicit SKETCH, not a closed spec — it needs a design pass (likely a /meeting on the
core removal semantic) before it is even single-turn-HARD-ready. Recommended split for
a future strong session: (a) add a retract field-merge mode to `zkm.amendments` in the
CORE repo with its own red-green; (b) plugin-side diff (prior notmuch-attributed tags
minus current notmuch tags) emitting retraction records. No checkbox ticked, no test
manufactured. Baseline suite 29/29 green in the main checkout (the worktree's `../../`
editable-zkm source can't resolve under ~/.cache/ — known friction, not a defect; HEAD
is identical to the main checkout). routine_open=0; REVIEW_ME unchanged (0 open).

## 2026-06-13 — executor (claude-sonnet-4-6)

Worked id:d0e9, id:c353, id:1af4, id:df4e — all four ROUTINE items in one session.
d0e9: added `kind: amender` to both plugin.yaml files (root + src/zkm_notmuch/).
c353: added `created: list[Path] | None = None` kwarg to `convert()`; scoping filters
the emit loop while keeping the full notmuch dump global (one subprocess per spec).
Used `frontmatter.load` to read message_id from each created-batch md file.
1af4: wrapped `FileNotFoundError` and `CalledProcessError` in `RuntimeError` with
actionable messages that name `notmuch` and include stderr for non-zero exits.
df4e: replaced the falsy `frozenset(...) or _DEFAULT_EXCLUDE` trap with a sentinel
sentinel-based key-absent check; explicit empty list now means "exclude nothing".
Friction: worktree's `../../` relative zkm path doesn't resolve (worktree is two extra
levels deep under ~/.cache/); used absolute-path pyproject.toml temporarily for the
test run, reverted before commit. 29/29 tests green.

## 2026-06-12 22:03 — reviewer (claude-fable-5)

Handoff: first CLAUDE.md + ARCHITECTURE.md (D1-D6); README de-staled to zkm-config.yaml keys. Suite was collection-broken since SB5 — repaired to 16 green + consistency guards. KEY FIND: plugin.yaml lacks kind:amender so core never auto-runs the first amender after eml converts — top ROUTINE d0e9. ROADMAP 4 ROUTINE (d0e9, c353 created-scoped amending per core id:63bb, 1af4 CLI errors, df4e empty tags_exclude) + 1 HARD (f103 tag-removal propagation needs attribution-aware core semantics). 8 red specs; uv.lock now committed; @manual Gherkin; 3 REVIEW_ME.

## 2026-06-13 10:11 — executor (sonnet, relay-loop)

executor: all four ROUTINE items complete (d0e9 kind:amender, c353 created-scoped amending, 1af4 actionable CLI errors, df4e empty tags_exclude); 29/29 tests green

## 2026-06-13 15:11 — reviewer (claude-opus-4-8, fable-standin, relay-loop)

review: cf5e887 audited clean (docs-only, no gaming surface, 29 tests green); contract pointer v1→v2, ROADMAP/TODO synced, plugin-error-contract routed to inbox (4d69)

## 2026-06-13 23:53 — reviewer (claude-opus-4-8, fable-standin, relay-loop)

review 20260613-2304: 1 commit audited clean (REVIEW_ME triage only, no code/tests touched), 29 tests green, 4/4 ROUTINE verified, 1 HARD (f103) open, contract pointer v2 in sync

## 2026-06-15 11:04 — reviewer (claude-opus-4-8, fable-standin, relay-loop)

Review window fable-ckpt-20260613-2353..HEAD: one user manual commit (87c71be)
ticking the df4e REVIEW_ME box (interpretation confirmed: explicit `tags_exclude: []`
== exclude-nothing). Trust-but-verify clean: no test files deleted/weakened/skipped,
no implementation changed in the window, so no resurrection/fixture-special-casing
exposure. Full suite 29/29 green (run in the main checkout — the worktree's `../../`
editable-zkm path can't resolve two levels deep under ~/.cache/, known friction, not a
defect; HEAD identical to main checkout so the tree under review is exact). df4e pair
(incl. the absent-key behaviour guard) both pass. BDD `convert-notmuch.feature` is
fully @manual (live notmuch DB) — surfaced as the human checklist, not automated.
Spec-drift §4: migrated the stale relay pointer in CLAUDE.md from
`<!-- fables-executor contract v2 -->` (`/fables-executor` body) to v3
(`/relay executor`). No new ledger items in window (5b no-op). Roadmap unchanged:
d0e9/c353/1af4/df4e closed & verified, f103 [HARD] the only open item.
routine_open=0. REVIEW_ME now 0 open boxes.

## 2026-06-15 11:27 — reviewer (claude-opus-4-8, fable-standin, relay-loop)

review 20260615-1104: df4e user-confirm verified clean (29/29 green), stale relay pointer migrated v2→v3; f103 [HARD] the only open item
