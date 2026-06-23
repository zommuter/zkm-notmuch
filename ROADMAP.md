# Roadmap <!-- fables-turn roadmap v1 -->

Executor-facing task spec. Each item is sized for ONE Sonnet session. Items are
the single source of truth — TODO.md carries only a summary line. Executors tick
checkboxes; only the reviewer adds, removes, or re-scopes items.

## Items

- [x] Declare `kind: amender` in both plugin.yaml manifests [ROUTINE] <!-- id:d0e9 -->
  - **Acceptance**: `plugin.yaml` AND `src/zkm_notmuch/plugin.yaml` carry
    `kind: amender`; the two files stay byte-identical. After this, core's
    `list_amenders()` includes notmuch and `zkm convert eml` auto-runs it
    (user-observable: tags appear without a manual `zkm convert notmuch`).
  - **Tests**: `tests/test_roadmap_specs.py::test_d0e9_root_plugin_yaml_declares_kind_amender`,
    `::test_d0e9_packaged_plugin_yaml_declares_kind_amender` (GREEN)
  - **Done-check**: `uv run pytest -k "d0e9 or consistency"`
  - **Context**: see ARCHITECTURE.md §D6. Core defaults `kind` to `"converter"`
    when absent (`zkm/convert.py` Plugin dataclass) — that default is why the
    plugin is currently never auto-run. Edit BOTH yaml copies (CLAUDE.md gotcha);
    `tests/test_consistency.py` enforces identity.

- [x] Support `created`-scoped amending (core amender scoping, id:63bb) [ROUTINE] <!-- id:c353 -->
  - **Acceptance**: `convert()` gains a keyword param `created: list[Path] | None = None`.
    When `created` is a list, only message_ids whose md file is in `created`
    (matched via each created file's `message_id` frontmatter; non-md / missing /
    frontmatter-less entries skipped) get amendment records — no queue entries
    are emitted for messages outside the batch. `created=None` keeps today's
    full-sweep behaviour. Core's capability probe (`inspect.signature`) then
    passes `created` automatically after eml converts.
  - **Tests**: `tests/test_roadmap_specs.py::test_c353_convert_declares_created_param`,
    `::test_c353_created_scopes_emits_to_batch`,
    `::test_c353_created_none_full_sweep` (GREEN)
  - **Done-check**: `uv run pytest -k c353`
  - **Context**: ARCHITECTURE.md §D6; core probe in `zkm/convert.py`
    (`_supports_created`, `run_convert`). The notmuch dump itself stays global
    (one subprocess, §D2) — scoping filters the *emit* loop. Keep the existing
    `progress` param working.

- [x] Fail with actionable errors when the notmuch CLI is unavailable or fails [ROUTINE] <!-- id:1af4 -->
  - **Acceptance**: a missing `notmuch` binary (FileNotFoundError from
    subprocess) and a non-zero notmuch exit (CalledProcessError) both raise
    `RuntimeError` with a message that names `notmuch` and, for the non-zero
    case, includes the captured stderr. No raw subprocess tracebacks reach the
    user; core's amender loop then prints its one-line WARN instead of a stack.
  - **Tests**: `tests/test_roadmap_specs.py::test_1af4_missing_notmuch_binary_raises_runtime_error`,
    `::test_1af4_notmuch_failure_includes_stderr` (GREEN)
  - **Done-check**: `uv run pytest -k 1af4`
  - **Context**: `src/zkm_notmuch/convert.py::_load_notmuch_tags` (the
    `subprocess.run(..., check=True)` call). Judgment call logged in
    REVIEW_ME.md (exception type choice).

- [x] Treat explicit `tags_exclude: []` as "exclude nothing" [ROUTINE] <!-- id:df4e -->
  - **Acceptance**: a user who sets `tags_exclude: []` (explicit empty YAML
    list) gets ALL notmuch tags, including system tags like `inbox`. The
    built-in default list still applies when the key is absent or an empty
    string. Comma-string parsing unchanged.
  - **Tests**: `tests/test_roadmap_specs.py::test_df4e_explicit_empty_list_disables_exclusions`,
    `::test_df4e_absent_key_keeps_default_exclusions` (GREEN; the second is the
    behaviour-preserving guard)
  - **Done-check**: `uv run pytest -k df4e`
  - **Context**: `src/zkm_notmuch/convert.py::convert` exclusion resolution
    (`frozenset(...) or _DEFAULT_EXCLUDE` is the falsy-empty trap). See
    ARCHITECTURE.md §D4; judgment call logged in REVIEW_ME.md.

- [ ] Propagate notmuch tag REMOVALS to frontmatter [ROUTINE] <!-- id:f103 -->
  - **Acceptance**: deleting a tag in notmuch and re-running the amender removes
    it from frontmatter IFF notmuch was its (sole) producer; idempotent; a
    user/eml-authored tag the notmuch producer never emitted is NEVER retracted.
  - **Tests**: `tests/test_roadmap_specs.py::test_f103_removed_notmuch_tag_is_retracted`
    (RED — legacy additive `emit` set-unions, never shrinks),
    `::test_f103_user_authored_tag_is_not_retracted` (GREEN — attribution guard).
  - **Done-check**: `uv run pytest -k f103`
  - **Context** (reclassified `[HARD — meeting]` → `[ROUTINE]` 2026-06-23, decision
    D2 in zkm `docs/meeting-notes/2026-06-23-1807-zkm-amendments-removal-coherence.md`):
    the prior HARD blocker — "needs a new core-level removal semantic in
    `zkm.amendments`" — has **shipped**. Core now exposes `emit_set` (mode `"set"`,
    `zkm/src/zkm/amendments.py:77`): a DECLARATIVE full-set assert that, on apply,
    diffs the producer's stored set against the new set and drops values
    ref-counting to zero — retracting only `emitted_by: notmuch`'s OWN prior tags,
    never user/eml tags (`tags` is already in core `_SET_FIELDS`). The remaining
    work is a one-line-shaped plugin migration: switch the loop in
    `src/zkm_notmuch/convert.py:85` from `emit(...)` to `emit_set(...)` (identical
    signature) so each sweep asserts notmuch's CURRENT complete tag set per message.
    Keep `created`-scoping (`emit_set`'s diff is scoped to keys reported in the run,
    D4b) and the existing `apply_queue` flow. Update the `from zkm.amendments import`
    line to pull in `emit_set`.

## Repo chores (no id; fold into any session)

- `uv.lock` is now committed (flipped 2026-06-12); keep it in sync on dep changes.
