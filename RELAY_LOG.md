# Relay log <!-- merge=union; append-only — never edit or reorder past entries -->

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
