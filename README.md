# zkm-notmuch

[zkm](https://github.com/zommuter/zkm) amender plugin that merges [notmuch](https://notmuchmail.org/) Xapian tags into the frontmatter of mail messages already converted by `zkm-eml`.

## What it does

- Reads tags via `notmuch dump --format=batch-tag`
- For each message whose `Message-ID` matches an existing `mail/messages/*.md` file, emits amendment records that extend the `tags:` list in frontmatter
- Amender pattern: returns `[]`, modifies frontmatter in place via `zkm.amendments`
- Normalises notmuch IDs (no angle brackets) to the zkm-eml form (`<id>`) before matching
- Skips system tags by default (`inbox`, `unread`, `attachment`, `signed`, `encrypted`, `replied`, `passed`, `flagged`, `deleted`, `sent`)

## Prerequisites

- [`notmuch`](https://notmuchmail.org/) installed and configured with an indexed mail database
- `zkm-eml` plugin already run (the amendment target is `mail/messages/*.md`)

## Install

End-user (wheel, entry-point discovery):

```bash
uv tool install zkm --with zkm-notmuch
```

Development (filesystem discovery) — clone this repo inside your zkm `plugins/` directory:

```bash
git clone https://github.com/zommuter/zkm-notmuch.git plugins/zkm-notmuch
```

## Configuration (in `<store>/zkm-config.yaml`)

```yaml
notmuch:
  config_file: ~/.notmuch-config   # optional; empty = notmuch default discovery
  tags_exclude: [inbox, unread]    # optional; overrides the built-in system-tag list
```

| Key | Default | Description |
|---|---|---|
| `config_file` | *(notmuch default discovery)* | Path passed as `notmuch --config <path>` |
| `tags_exclude` | *(built-in list)* | System tags to exclude — YAML list or comma-separated string |

## Run

```bash
zkm convert notmuch
```

## Development

```bash
cd plugins/zkm-notmuch
uv sync --extra dev
uv run pytest
```

## License

MIT — see [LICENSE](LICENSE)
