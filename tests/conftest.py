from __future__ import annotations

import subprocess
from pathlib import Path


def make_store(tmp_path: Path) -> Path:
    s = tmp_path / "store"
    s.mkdir()
    subprocess.run(["git", "init", "-q", str(s)], check=True)
    return s


def make_md(directory: Path, filename: str, *, message_id: str, tags: list | None = None) -> Path:
    """Write a minimal zkm-eml-style md with the given message_id."""
    import frontmatter
    meta = {
        "source": "eml",
        "date": "2026-05-08T10:00:00+00:00",
        "message_id": message_id,
        "tags": tags if tags is not None else [],
    }
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / filename
    path.write_text(frontmatter.dumps(frontmatter.Post("body", **meta)), encoding="utf-8")
    return path
