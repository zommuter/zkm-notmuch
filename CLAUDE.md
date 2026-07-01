# zkm-notmuch — notmuch tag amender for zkm

Amender plugin for [zkm](https://github.com/zommuter/zkm): reads tags from the
notmuch Xapian database (`notmuch dump --format=batch-tag`) and merges them into
`mail/messages/*.md` frontmatter via `zkm.amendments`. Historically the FIRST
amender in the zkm pipeline — it closes the gap where zkm-eml initialises
`tags: []` empty.

See `ARCHITECTURE.md` for design decisions with rationale and rejected
alternatives. See `ROADMAP.md` for the executor-facing task queue.

## Commands

```bash
uv sync                  # dev env (Python 3.11+); installs zkm editable from ../..
uv run pytest            # full suite — hermetic, no live notmuch (subprocess mocked)
uv run pytest -k <expr>  # one test / one roadmap item's done-check
uv run ruff check <changed files>   # lint (line-length 100, py311 target)
```

This repo is a **dev plugin repo** living at `~/src/zkm/plugins/zkm-notmuch/`
inside the zkm core checkout (gitignored by core, own git history, own tags).
The editable dep `zkm = { path = "../..", editable = true }` in `pyproject.toml`
resolves against the surrounding core checkout — `uv sync` only works from that
nesting (or an equivalent host worktree).

## Layout

```
convert.py                  # filesystem-discovery SHIM — re-exports zkm_notmuch.convert.convert
plugin.yaml                 # manifest for filesystem discovery (dev-symlink path)
src/zkm_notmuch/
├── __init__.py             # empty; package is the zkm.plugins entry-point target
├── convert.py              # REAL implementation
└── plugin.yaml             # manifest copy for entry-point discovery (wheel path)
tests/
├── conftest.py             # make_store / make_md helpers (tmp_path stores)
└── test_convert.py
```

### Dual discovery — why two plugin.yaml and a shim exist

Core discovers plugins two ways (filesystem wins on name collision):

1. **Filesystem** (dev): core scans `plugins/*/plugin.yaml`, then loads the repo-root
   `convert.py` via `importlib.util.spec_from_file_location`. Core's
   `_inject_plugin_venv` puts this repo's `src/` (and `.venv` site-packages) on
   `sys.path` first, which is what makes the shim's
   `from zkm_notmuch.convert import convert` work.
2. **Entry-point** (wheel): `[project.entry-points."zkm.plugins"] notmuch = "zkm_notmuch"`;
   core resolves the package dir and reads `src/zkm_notmuch/plugin.yaml` from it.

**Gotcha:** the two `plugin.yaml` files MUST stay byte-identical — edit both or
drift silently splits dev vs wheel behaviour (`tests/test_consistency.py` guards
this).

**Gotcha:** version appears in FOUR places: `pyproject.toml`, both `plugin.yaml`
copies, and `PLUGIN_VERSION` in `src/zkm_notmuch/convert.py`. Bump all four in
the same commit and tag `vX.Y.Z` (bump-and-tag rule).

## Amender contract (how core invokes this plugin)

- Amenders are **default-on**: after any `zkm convert <converter>` that created
  files, core runs every plugin whose `plugin.yaml` declares `kind: amender`
  (opt-out: `--no-amenders`). When a convert created 0 files, amenders are
  skipped with a notice that includes the pending-amendment count.
- **Amender scoping (core id:63bb):** core passes `created: list[Path]` to any
  amender whose `convert()` declares a `created` parameter (capability-probed via
  `inspect.signature`, same mechanism as `progress`). Explicit
  `zkm convert notmuch` passes `created=None` → full sweep.
- Amenders return `[]` from `convert()` — they modify frontmatter in place; run
  `zkm index` afterwards to pick up changes.
- Frontmatter is multi-producer via `zkm.amendments` (`emit_set` → queue →
  `apply_queue`; declarative full-set assert with attribution-aware retraction
  since f103, 2026-06-24); the md *body* is single-producer (zkm-eml's). Never
  write the body from this plugin.

**Current state (see ROADMAP.md):** all 5 roadmap items shipped — `plugin.yaml`
declares `kind: amender` (d0e9, auto-run after eml converts) and `convert()`
declares `created` (c353, batch-scoped emits).

## Config

Non-secret config lives in `<store>/zkm-config.yaml` under the plugin's section
(bare snake_case keys since the M2 migration — the old `.env` /
`NOTMUCH_CONFIG` env-var scheme is retired):

| Key | Default | Description |
|---|---|---|
| `config_file` | `""` (notmuch default discovery) | Path passed as `notmuch --config <path>` |
| `tags_exclude` | built-in system-tag list | Tags never copied to frontmatter; YAML list or comma-separated string |

## Testing conventions

- **Hermetic**: no live notmuch database, ever. Mock the CLI by patching
  `zkm_notmuch.convert.subprocess.run` to return a fake
  `notmuch dump --format=batch-tag` stdout.
- Stores are `tmp_path` git-inits via `tests/conftest.py:make_store`; md files
  via `make_md` (zkm-eml-shaped frontmatter with `message_id`).
- Message-ID convention under test: notmuch IDs have no angle brackets; zkm-eml
  frontmatter stores `<id>` — `_normalise_mid` bridges them.

## Conventions

- Python 3.11+, `uv` only (never bare pip), ruff, pytest, conventional commits.
- Versioning: bump-and-tag, loose-0.x (patch = bugfix only; minor = anything else).
- Lockfile (`uv.lock`) is committed (polyrepo convention).
- Keep `zkm` dep pin (`>=0.4,<1.0`) honest: if you start using a new core API,
  raise the floor.

## Relay contract <!-- relay-executor contract v6 -->

This repo is managed by a reviewer/executor relay. Load `/relay executor` before
working on any item, then follow its rules exactly.
