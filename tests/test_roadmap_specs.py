"""Spec-as-tests for ROADMAP.md items. Each test carries a # roadmap:XXXX tag.

These tests are intentionally RED at handoff time — an executor is done with an
item when its tests go green (plus a refactor pass), nothing else. Judgment
calls encoded here are listed in REVIEW_ME.md.
"""

from __future__ import annotations

import inspect
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import frontmatter
import pytest
import yaml

from conftest import make_md, make_store
from zkm_notmuch.convert import convert

REPO_ROOT = Path(__file__).resolve().parent.parent


def _fake_dump(lines: list[str]) -> MagicMock:
    m = MagicMock()
    m.stdout = "\n".join(lines) + "\n"
    return m


# ---------------------------------------------------------------------------
# d0e9 — declare kind: amender in both plugin.yaml manifests
# ---------------------------------------------------------------------------


def test_d0e9_root_plugin_yaml_declares_kind_amender():  # roadmap:d0e9
    data = yaml.safe_load((REPO_ROOT / "plugin.yaml").read_text(encoding="utf-8"))
    assert data.get("kind") == "amender"


def test_d0e9_packaged_plugin_yaml_declares_kind_amender():  # roadmap:d0e9
    manifest = REPO_ROOT / "src" / "zkm_notmuch" / "plugin.yaml"
    data = yaml.safe_load(manifest.read_text(encoding="utf-8"))
    assert data.get("kind") == "amender"


# ---------------------------------------------------------------------------
# c353 — created-scoped amending (core amender scoping, id:63bb)
# ---------------------------------------------------------------------------


def test_c353_convert_declares_created_param():  # roadmap:c353
    assert "created" in inspect.signature(convert).parameters


def test_c353_created_scopes_emits_to_batch(tmp_path):  # roadmap:c353
    store = make_store(tmp_path)
    msgs = store / "mail" / "messages"
    md1 = make_md(msgs, "msg1.md", message_id="<one@example.com>")
    md2 = make_md(msgs, "msg2.md", message_id="<two@example.com>")

    dump = [
        "+bill -- id:one@example.com",
        "+receipt -- id:two@example.com",
    ]
    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_dump(dump)):
        convert(store, {}, created=[md1])

    assert "bill" in frontmatter.load(md1).metadata["tags"]
    # out-of-batch message: untouched AND nothing queued for it
    assert frontmatter.load(md2).metadata["tags"] == []
    queue_root = store / ".zkm-state" / "amendments"
    assert not list(queue_root.rglob("*.json")) if queue_root.exists() else True


def test_c353_created_none_full_sweep(tmp_path):  # roadmap:c353
    store = make_store(tmp_path)
    msgs = store / "mail" / "messages"
    md1 = make_md(msgs, "msg1.md", message_id="<one@example.com>")
    md2 = make_md(msgs, "msg2.md", message_id="<two@example.com>")

    dump = [
        "+bill -- id:one@example.com",
        "+receipt -- id:two@example.com",
    ]
    with patch("zkm_notmuch.convert.subprocess.run", return_value=_fake_dump(dump)):
        convert(store, {}, created=None)

    assert "bill" in frontmatter.load(md1).metadata["tags"]
    assert "receipt" in frontmatter.load(md2).metadata["tags"]


# ---------------------------------------------------------------------------
# 1af4 — actionable errors when the notmuch CLI is unavailable or fails
# ---------------------------------------------------------------------------


def test_1af4_missing_notmuch_binary_raises_runtime_error(tmp_path):  # roadmap:1af4
    store = make_store(tmp_path)
    with patch(
        "zkm_notmuch.convert.subprocess.run",
        side_effect=FileNotFoundError("[Errno 2] No such file or directory: 'notmuch'"),
    ):
        with pytest.raises(RuntimeError, match="notmuch"):
            convert(store, {})


def test_1af4_notmuch_failure_includes_stderr(tmp_path):  # roadmap:1af4
    store = make_store(tmp_path)
    err = subprocess.CalledProcessError(
        1, ["notmuch", "dump", "--format=batch-tag"], stderr="database not found"
    )
    with patch("zkm_notmuch.convert.subprocess.run", side_effect=err):
        with pytest.raises(RuntimeError, match="database not found"):
            convert(store, {})


# ---------------------------------------------------------------------------
# df4e — explicit tags_exclude: [] means "exclude nothing"
# ---------------------------------------------------------------------------


def test_df4e_explicit_empty_list_disables_exclusions(tmp_path):  # roadmap:df4e
    store = make_store(tmp_path)
    msgs = store / "mail" / "messages"
    md = make_md(msgs, "msg1.md", message_id="<x@y.com>")

    with patch(
        "zkm_notmuch.convert.subprocess.run",
        return_value=_fake_dump(["+inbox +bill -- id:x@y.com"]),
    ):
        convert(store, {"tags_exclude": []})

    tags = frontmatter.load(md).metadata["tags"]
    assert "inbox" in tags
    assert "bill" in tags


def test_df4e_absent_key_keeps_default_exclusions(tmp_path):  # roadmap:df4e
    # Behaviour-preserving boundary guard (green at handoff): no tags_exclude
    # key at all still applies the built-in system-tag list.
    store = make_store(tmp_path)
    msgs = store / "mail" / "messages"
    md = make_md(msgs, "msg1.md", message_id="<x@y.com>")

    with patch(
        "zkm_notmuch.convert.subprocess.run",
        return_value=_fake_dump(["+inbox +bill -- id:x@y.com"]),
    ):
        convert(store, {})

    tags = frontmatter.load(md).metadata["tags"]
    assert "inbox" not in tags
    assert "bill" in tags
