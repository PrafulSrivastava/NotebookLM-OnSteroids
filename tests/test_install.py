from pathlib import Path
import pytest
from install import copy_skill, resolve_scope_path, SKILL_DEST_NAME


def test_resolve_scope_user():
    dest = resolve_scope_path("user")
    assert dest == Path.home() / ".claude" / "skills" / SKILL_DEST_NAME


def test_resolve_scope_repo():
    dest = resolve_scope_path("repo")
    repo_root = Path(__file__).parent.parent
    assert dest == repo_root / ".claude" / "skills" / SKILL_DEST_NAME


def test_resolve_scope_invalid():
    with pytest.raises(ValueError, match="Unknown scope"):
        resolve_scope_path("invalid")


def test_copy_skill_creates_structure(tmp_path):
    dest = tmp_path / "notebooklm"
    copy_skill(dest)

    assert (dest / "SKILL.md").exists()
    scripts = dest / "scripts"
    assert scripts.is_dir()
    for name in ("__init__.py", "nblm_list.py", "nblm_query.py", "nblm_pipeline.py"):
        assert (scripts / name).exists(), f"Missing scripts/{name}"


def test_copy_skill_overwrites_existing(tmp_path):
    dest = tmp_path / "notebooklm"
    copy_skill(dest)
    (dest / "SKILL.md").write_text("stale content", encoding="utf-8")
    copy_skill(dest)
    assert (dest / "SKILL.md").read_text(encoding="utf-8") != "stale content"


def test_copy_skill_idempotent(tmp_path):
    dest = tmp_path / "notebooklm"
    copy_skill(dest)
    copy_skill(dest)  # second call must not raise
    assert (dest / "SKILL.md").exists()
