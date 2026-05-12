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

Clone this repo inside your zkm `plugins/` directory:

```bash
git clone https://github.com/zommuter/zkm-notmuch.git plugins/zkm-notmuch
```

## Configuration (in `<store>/.env`)

| Variable | Default | Description |
|---|---|---|
| `NOTMUCH_EXCLUDE_TAGS` | *(built-in list)* | Comma-separated tag names to skip |

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
