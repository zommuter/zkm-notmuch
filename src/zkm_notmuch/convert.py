"""zkm-notmuch — amend mail/messages/ frontmatter with notmuch xapian tags.

Reads tags via `notmuch dump --format=batch-tag`, emits amendment records
via zkm.amendments for every message that has non-excluded tags, then
applies the queue. Returns [] (amender pattern).

Message IDs: notmuch stores IDs without angle brackets; zkm-eml stores
raw_message_id WITH angle brackets in frontmatter. This module normalises
notmuch IDs to the <id> form before emitting amendment keys.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from zkm.amendments import apply_queue, emit

PLUGIN_NAME = "notmuch"
PLUGIN_VERSION = "0.3.0"

_DEFAULT_EXCLUDE = frozenset({
    "inbox", "unread", "attachment", "signed", "encrypted",
    "replied", "passed", "flagged", "deleted", "sent",
})


def convert(store_path: Path, config: dict, *, progress=None) -> list[Path]:
    """Amend mail/messages/ md files with notmuch tags.

    Returns [] — amender pattern; run `zkm index` after to pick up changes.
    """
    notmuch_config = str(config.get("config_file", "") or "").strip() or None
    excl_raw = config.get("tags_exclude", "")
    if isinstance(excl_raw, list):
        exclude = frozenset(t for t in excl_raw if t) or _DEFAULT_EXCLUDE
    else:
        raw_str = str(excl_raw).strip()
        exclude = frozenset(t.strip() for t in raw_str.split(",") if t.strip()) if raw_str else _DEFAULT_EXCLUDE

    tags_by_mid = _load_notmuch_tags(notmuch_config, exclude)

    total = len(tags_by_mid)
    for i, (message_id, tags) in enumerate(tags_by_mid.items(), 1):
        emit(
            store_path,
            key={"message_id": message_id},
            fields={"tags": sorted(tags)},
            emitted_by=PLUGIN_NAME,
        )
        if progress:
            progress(i, total, message_id)

    applied, pending = apply_queue(store_path)
    if applied:
        print(f"zkm-notmuch: applied {applied} amendment(s)", file=sys.stderr)
    if pending:
        print(
            f"zkm-notmuch: {pending} amendment(s) pending "
            "(run again after zkm-eml to resolve)",
            file=sys.stderr,
        )

    return []


# ---------------------------------------------------------------------------
# notmuch helpers
# ---------------------------------------------------------------------------


def _load_notmuch_tags(
    notmuch_config: str | None,
    exclude: frozenset[str],
) -> dict[str, set[str]]:
    """Return {message_id: set_of_tags} from `notmuch dump --format=batch-tag`.

    message_id values are normalised to include angle brackets to match
    the raw_message_id format stored by zkm-eml.
    """
    cmd = ["notmuch"]
    if notmuch_config:
        cmd += ["--config", notmuch_config]
    cmd += ["dump", "--format=batch-tag"]

    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return _parse_batch_tag(result.stdout, exclude)


def _parse_batch_tag(output: str, exclude: frozenset[str]) -> dict[str, set[str]]:
    """Parse `notmuch dump --format=batch-tag` output.

    Format per line: `+tag1 +tag2 -- id:MESSAGE-ID`
    Lines starting with `#` are header comments and are skipped.
    Only `+tag` entries (current tags) are collected; `-tag` entries (removals)
    do not appear in dump output but are tolerated and ignored.
    """
    result: dict[str, set[str]] = {}
    for line in output.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " -- id:" not in line:
            continue
        tags_part, mid_raw = line.split(" -- id:", 1)
        mid_raw = mid_raw.strip()
        message_id = _normalise_mid(mid_raw)
        tags = {
            t[1:] for t in tags_part.split()
            if t.startswith("+") and t[1:] not in exclude
        }
        if tags:
            result[message_id] = tags
    return result


def _normalise_mid(mid: str) -> str:
    """Wrap message ID in angle brackets if not already present."""
    if mid.startswith("<") and mid.endswith(">"):
        return mid
    return f"<{mid}>"
