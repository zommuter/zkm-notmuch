"""Repo-consistency guards for the dual-discovery layout (ARCHITECTURE.md §D5).

These are GREEN regression guards, not roadmap specs: the two plugin.yaml
copies must stay byte-identical, the version must agree across its four
declaration sites, and the repo-root shim must keep exposing convert() for
core's filesystem (dev-symlink) discovery path.
"""

from __future__ import annotations

import importlib.util
import tomllib
from pathlib import Path

import yaml

from zkm_notmuch.convert import PLUGIN_NAME, PLUGIN_VERSION

REPO_ROOT = Path(__file__).resolve().parent.parent
ROOT_YAML = REPO_ROOT / "plugin.yaml"
PACKAGED_YAML = REPO_ROOT / "src" / "zkm_notmuch" / "plugin.yaml"


def test_plugin_yaml_copies_are_identical():
    assert ROOT_YAML.read_bytes() == PACKAGED_YAML.read_bytes()


def test_version_sync_across_declaration_sites():
    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    manifest = yaml.safe_load(ROOT_YAML.read_text(encoding="utf-8"))
    assert (
        pyproject["project"]["version"]
        == str(manifest["version"])
        == PLUGIN_VERSION
    )


def test_manifest_name_matches_plugin_name():
    manifest = yaml.safe_load(ROOT_YAML.read_text(encoding="utf-8"))
    assert manifest["name"] == PLUGIN_NAME


def test_root_shim_exposes_convert():
    """Core file-loads the repo-root convert.py for filesystem discovery."""
    spec = importlib.util.spec_from_file_location(
        "zkm_plugin_notmuch_shim_under_test", REPO_ROOT / "convert.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert callable(mod.convert)
