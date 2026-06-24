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

import frontmatter as _frontmatter

from zkm.amendments import apply_queue, emit_set

PLUGIN_NAME = "notmuch"
PLUGIN_VERSION = "0.4.0"

_SENTINEL = object()  # distinguish "key absent" from "key present but falsy"

_DEFAULT_EXCLUDE = frozenset({
    "inbox", "unread", "attachment", "signed", "encrypted",
    "replied", "passed", "flagged", "deleted", "sent",
})


def convert(
    store_path: Path,
    config: dict,
    *,
    progress=None,
    created: list[Path] | None = None,
) -> list[Path]:
    """Amend mail/messages/ md files with notmuch tags.

    If *created* is a list of Paths, only messages whose md file is in that
    list (matched via the file's ``message_id`` frontmatter field) receive
    amendment records.  ``created=None`` (default) runs the full sweep.

    Returns [] — amender pattern; run ``zkm index`` after to pick up changes.
    """
    notmuch_config = str(config.get("config_file", "") or "").strip() or None

    excl_raw = config.get("tags_exclude", _SENTINEL)
    if excl_raw is _SENTINEL:
        # Key absent — use built-in defaults.
        exclude = _DEFAULT_EXCLUDE
    elif isinstance(excl_raw, list):
        # Explicit list: empty list means "exclude nothing"; non-empty filters.
        exclude = frozenset(t for t in excl_raw if t)
    else:
        raw_str = str(excl_raw).strip()
        exclude = (
            frozenset(t.strip() for t in raw_str.split(",") if t.strip())
            if raw_str
            else _DEFAULT_EXCLUDE
        )

    tags_by_mid = _load_notmuch_tags(notmuch_config, exclude)

    # Build a set of message_ids in the created batch (if scoped).
    created_mids: frozenset[str] | None = None
    if created is not None:
        batch_mids: set[str] = set()
        for md_path in created:
            try:
                post = _frontmatter.load(str(md_path))
                mid = post.metadata.get("message_id")
                if mid:
                    batch_mids.add(str(mid))
            except Exception:
                pass  # non-md or unreadable — skip per spec
        created_mids = frozenset(batch_mids)

    total = len(tags_by_mid)
    for i, (message_id, tags) in enumerate(tags_by_mid.items(), 1):
        if created_mids is not None and message_id not in created_mids:
            continue  # out-of-batch — skip emit
        emit_set(
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

    Raises RuntimeError (with an actionable message) on a missing notmuch
    binary or a non-zero notmuch exit — callers never see raw subprocess
    tracebacks.
    """
    cmd = ["notmuch"]
    if notmuch_config:
        cmd += ["--config", notmuch_config]
    cmd += ["dump", "--format=batch-tag"]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except FileNotFoundError as exc:
        raise RuntimeError(
            "notmuch binary not found — install notmuch and ensure it is on PATH"
        ) from exc
    except subprocess.CalledProcessError as exc:
        stderr_msg = (exc.stderr or "").strip()
        raise RuntimeError(
            f"notmuch exited with status {exc.returncode}: {stderr_msg}"
        ) from exc

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
