# Human review queue <!-- budget: 15 min -->

Judgment calls encoded in red tests — confirm or correct the interpretation.
Max ~10 open boxes; the reviewer prunes resolved ones each review turn.

- [x] tests/test_roadmap_specs.py::test_df4e_explicit_empty_list_disables_exclusions (roadmap:df4e) —
  interpretation: explicit `tags_exclude: []` means "exclude nothing", while an
  ABSENT key (or legacy empty string) keeps the built-in system-tag defaults.
  Alternative reading (empty always falls back to defaults — today's behaviour)
  would leave "no exclusions" inexpressible. — confirmed by user 2026-06-15 (review_me batch triage)

- [x] tests/test_roadmap_specs.py::test_c353_created_scopes_emits_to_batch (roadmap:c353) — confirmed by user 2026-06-13 (batch triage) —
  interpretation: when `created` is given, messages OUTSIDE the batch get no
  amendment queue entries at all (prevents unbounded pending-queue growth on
  every auto-run). Alternative: emit for everything and let entries sit
  pending — rejected, but it would make a created-scoped run also heal older
  unmatched mail. Explicit `zkm convert notmuch` (created=None) still
  full-sweeps, so the healing path remains available.
