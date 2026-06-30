# Human review queue <!-- budget: 15 min -->

Judgment calls encoded in red tests — confirm or correct the interpretation.
Max ~10 open boxes; the reviewer prunes resolved ones each review turn.

- [x] Shared inbox dead-letter `routed:8b00` (f103 stage-2: emit_set full-set assert) — ✅ ack 2026-06-30 /relay human: confirmed: f103 closed green (31/31); routed:8b00 cleared via append.sh inbox-done 8b00 this reconcile pass.
  has LANDED — f103 closed & verified green 2026-06-24 (31/31). Run
  `~/.claude/skills/meeting/append.sh inbox-done 8b00` in the next cross-repo
  reconcile pass to clear it (report-only here; inbox is local-only, id:678e gated).
