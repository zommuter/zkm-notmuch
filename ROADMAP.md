# Roadmap <!-- fables-turn roadmap v1 -->

Executor-facing task spec. Each item is sized for ONE Sonnet session. Items are
the single source of truth — TODO.md carries only a summary line. Executors tick
checkboxes; only the reviewer adds, removes, or re-scopes items.

## Items

- [ ] Declare `kind: amender` in both plugin.yaml manifests [ROUTINE] <!-- id:d0e9 -->
  - **Acceptance**: `plugin.yaml` AND `src/zkm_notmuch/plugin.yaml` carry
    `kind: amender`; the two files stay byte-identical. After this, core's
    `list_amenders()` includes notmuch and `zkm convert eml` auto-runs it
    (user-observable: tags appear without a manual `zkm convert notmuch`).
  - **Tests**: `tests/test_roadmap_specs.py::test_d0e9_root_plugin_yaml_declares_kind_amender`,
    `::test_d0e9_packaged_plugin_yaml_declares_kind_amender` (currently RED)
  - **Done-check**: `uv run pytest -k "d0e9 or consistency"`
  - **Context**: see ARCHITECTURE.md §D6. Core defaults `kind` to `"converter"`
    when absent (`zkm/convert.py` Plugin dataclass) — that default is why the
    plugin is currently never auto-run. Edit BOTH yaml copies (CLAUDE.md gotcha);
    `tests/test_consistency.py` enforces identity.

- [ ] Support `created`-scoped amending (core amender scoping, id:63bb) [ROUTINE] <!-- id:c353 -->
  - **Acceptance**: `convert()` gains a keyword param `created: list[Path] | None = None`.
    When `created` is a list, only message_ids whose md file is in `created`
    (matched via each created file's `message_id` frontmatter; non-md / missing /
    frontmatter-less entries skipped) get amendment records — no queue entries
    are emitted for messages outside the batch. `created=None` keeps today's
    full-sweep behaviour. Core's capability probe (`inspect.signature`) then
    passes `created` automatically after eml converts.
  - **Tests**: `tests/test_roadmap_specs.py::test_c353_convert_declares_created_param`,
    `::test_c353_created_scopes_emits_to_batch`,
    `::test_c353_created_none_full_sweep` (currently RED)
  - **Done-check**: `uv run pytest -k c353`
  - **Context**: ARCHITECTURE.md §D6; core probe in `zkm/convert.py`
    (`_supports_created`, `run_convert`). The notmuch dump itself stays global
    (one subprocess, §D2) — scoping filters the *emit* loop. Keep the existing
    `progress` param working.

- [ ] Fail with actionable errors when the notmuch CLI is unavailable or fails [ROUTINE] <!-- id:1af4 -->
  - **Acceptance**: a missing `notmuch` binary (FileNotFoundError from
    subprocess) and a non-zero notmuch exit (CalledProcessError) both raise
    `RuntimeError` with a message that names `notmuch` and, for the non-zero
    case, includes the captured stderr. No raw subprocess tracebacks reach the
    user; core's amender loop then prints its one-line WARN instead of a stack.
  - **Tests**: `tests/test_roadmap_specs.py::test_1af4_missing_notmuch_binary_raises_runtime_error`,
    `::test_1af4_notmuch_failure_includes_stderr` (currently RED)
  - **Done-check**: `uv run pytest -k 1af4`
  - **Context**: `src/zkm_notmuch/convert.py::_load_notmuch_tags` (the
    `subprocess.run(..., check=True)` call). Judgment call logged in
    REVIEW_ME.md (exception type choice).

- [ ] Treat explicit `tags_exclude: []` as "exclude nothing" [ROUTINE] <!-- id:df4e -->
  - **Acceptance**: a user who sets `tags_exclude: []` (explicit empty YAML
    list) gets ALL notmuch tags, including system tags like `inbox`. The
    built-in default list still applies when the key is absent or an empty
    string. Comma-string parsing unchanged.
  - **Tests**: `tests/test_roadmap_specs.py::test_df4e_explicit_empty_list_disables_exclusions`,
    `::test_df4e_absent_key_keeps_default_exclusions` (currently RED on the
    first; the second is the behaviour-preserving guard)
  - **Done-check**: `uv run pytest -k df4e`
  - **Context**: `src/zkm_notmuch/convert.py::convert` exclusion resolution
    (`frozenset(...) or _DEFAULT_EXCLUDE` is the falsy-empty trap). See
    ARCHITECTURE.md §D4; judgment call logged in REVIEW_ME.md.

- [ ] Propagate notmuch tag REMOVALS to frontmatter [HARD — strong model] <!-- id:f103 -->
  - **Why HARD**: the amendment engine only set-unions `tags`; removal needs an
    attribution-aware reconciliation (retract only tags previously contributed
    with `emitted_by: notmuch`, per the `<md>.amendments.json` sidecar, never
    user- or eml-authored tags) and most likely a new core-level removal
    semantic in `zkm.amendments` — cross-repo design with data-loss risk.
  - **Acceptance** (sketch): deleting a tag in notmuch and re-running the
    amender removes it from frontmatter iff notmuch was its (sole) producer;
    idempotent; attribution sidecar records the retraction.

## Repo chores (no id; fold into any session)

- `uv.lock` is now committed (flipped 2026-06-12); keep it in sync on dep changes.
