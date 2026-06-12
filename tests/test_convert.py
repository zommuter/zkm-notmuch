"""Tests for zkm-notmuch convert.py."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import frontmatter

from conftest import make_md, make_store
from zkm_notmuch.convert import PLUGIN_NAME, _normalise_mid, _parse_batch_tag, convert

# ---------------------------------------------------------------------------
# _normalise_mid
# ---------------------------------------------------------------------------


def test_normalise_mid_adds_brackets():
    assert _normalise_mid("abc@example.com") == "<abc@example.com>"


def test_normalise_mid_preserves_existing_brackets():
    assert _normalise_mid("<abc@example.com>") == "<abc@example.com>"


# ---------------------------------------------------------------------------
# _parse_batch_tag
# ---------------------------------------------------------------------------

_EXCLUDE = frozenset({"inbox", "unread", "attachment"})


def test_parse_batch_tag_basic():
    output = "+inbox +bill -- id:abc@example.com\n"
    result = _parse_batch_tag(output, _EXCLUDE)
    assert result == {"<abc@example.com>": {"bill"}}


def test_parse_batch_tag_skips_comment_lines():
    output = "#notmuch-dump batch-tag:3 config,properties,tags\n+bill -- id:abc@example.com\n"
    result = _parse_batch_tag(output, _EXCLUDE)
    assert "<abc@example.com>" in result


def test_parse_batch_tag_excludes_system_tags():
    output = "+inbox +unread +attachment +receipt -- id:x@y.com\n"
    result = _parse_batch_tag(output, _EXCLUDE)
    assert result["<x@y.com>"] == {"receipt"}


def test_parse_batch_tag_skips_messages_with_only_excluded_tags():
    output = "+inbox +unread -- id:x@y.com\n"
    result = _parse_batch_tag(output, _EXCLUDE)
    assert result == {}


def test_parse_batch_tag_multiple_messages():
    output = (
        "+bill -- id:msg1@ex.com\n"
        "+receipt +invoice -- id:msg2@ex.com\n"
    )
    result = _parse_batch_tag(output, frozenset())
    assert result["<msg1@ex.com>"] == {"bill"}
    assert result["<msg2@ex.com>"] == {"receipt", "invoice"}


def test_parse_batch_tag_already_bracketed_mid():
    output = "+bill -- id:<abc@example.com>\n"
    result = _parse_batch_tag(output, frozenset())
    assert "<abc@example.com>" in result
    assert "<<abc@example.com>>" not in result


# ---------------------------------------------------------------------------
# convert — round-trip
# ---------------------------------------------------------------------------


def _fake_notmuch_output(lines: list[str]) -> MagicMock:
    m = MagicMock()
    m.stdout = "\n".join(lines) + "\n"
    return m


def test_convert_basic_round_trip(tmp_path):
    store = make_store(tmp_path)
    msgs = store / "mail" / "messages"
    md = make_md(msgs, "msg1.md", message_id="<abc@example.com>")

    dump_output = "+inbox +bill +receipt -- id:abc@example.com"
    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_notmuch_output([dump_output])):
        result = convert(store, {})

    assert result == []
    tags = frontmatter.load(md).metadata["tags"]
    assert "bill" in tags
    assert "receipt" in tags
    assert "inbox" not in tags


def test_convert_returns_empty_list(tmp_path):
    store = make_store(tmp_path)
    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_notmuch_output([])):
        result = convert(store, {})
    assert result == []


def test_convert_union_with_existing_tags(tmp_path):
    store = make_store(tmp_path)
    msgs = store / "mail" / "messages"
    md = make_md(msgs, "msg1.md", message_id="<abc@example.com>", tags=["existing"])

    dump_output = "+bill -- id:abc@example.com"
    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_notmuch_output([dump_output])):
        convert(store, {})

    tags = frontmatter.load(md).metadata["tags"]
    assert "existing" in tags
    assert "bill" in tags


def test_convert_idempotent(tmp_path):
    store = make_store(tmp_path)
    msgs = store / "mail" / "messages"
    md = make_md(msgs, "msg1.md", message_id="<abc@example.com>")

    dump_output = "+bill -- id:abc@example.com"
    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_notmuch_output([dump_output])):
        convert(store, {})
        convert(store, {})

    tags = frontmatter.load(md).metadata["tags"]
    assert tags.count("bill") == 1


def test_convert_unknown_message_id_leaves_queue_entry(tmp_path):
    store = make_store(tmp_path)

    dump_output = "+bill -- id:unknown@example.com"
    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_notmuch_output([dump_output])):
        convert(store, {})

    queue_files = list((store / ".zkm-state" / "amendments" / PLUGIN_NAME).glob("*.json"))
    assert len(queue_files) == 1


def test_convert_uses_config_file_flag(tmp_path):
    store = make_store(tmp_path)
    config_path = str(tmp_path / "my.notmuch-config")

    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_notmuch_output([])) as mock_run:
        convert(store, {"config_file": config_path})

    cmd = mock_run.call_args[0][0]
    assert "--config" in cmd
    assert config_path in cmd


def test_convert_no_config_flag_when_not_set(tmp_path):
    store = make_store(tmp_path)

    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_notmuch_output([])) as mock_run:
        convert(store, {})

    cmd = mock_run.call_args[0][0]
    assert "--config" not in cmd


def test_convert_sidecar_written_after_apply(tmp_path):
    store = make_store(tmp_path)
    msgs = store / "mail" / "messages"
    md = make_md(msgs, "msg1.md", message_id="<abc@example.com>")

    dump_output = "+bill -- id:abc@example.com"
    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_notmuch_output([dump_output])):
        convert(store, {})

    sidecar = Path(str(md) + ".amendments.json")
    assert sidecar.exists()
    data = json.loads(sidecar.read_text())
    assert data["applied"][0]["emitted_by"] == PLUGIN_NAME
    assert data["applied"][0]["fields"]["tags"] == ["bill"]
