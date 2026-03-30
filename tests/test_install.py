from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from install import resolve_scope_path, SKILL_DEST_NAME


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
