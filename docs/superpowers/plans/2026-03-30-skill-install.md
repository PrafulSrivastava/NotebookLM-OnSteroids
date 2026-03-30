# Skill Install Feature — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend `install.py` to copy the Claude Code skill (SKILL.md + scripts) into the user's chosen scope, alongside existing Python/Playwright setup.

**Architecture:** Three pure helper functions (`resolve_scope_path`, `copy_skill`) are unit-tested; two thin I/O wrappers (`_prompt_scope`, `_confirm_overwrite`) are not. `install_skill()` composes them and is wired into `main()`. `SKILL.md` is updated to reference scripts via the base directory injected by Claude Code.

**Tech Stack:** Python 3.12 stdlib only (`pathlib`, `shutil`, `sys`). Tests use `pytest`.

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `install.py` | Modify | Non-editable install + skill install step |
| `pyproject.toml` | Modify | Add `dev` optional dep for pytest |
| `tests/__init__.py` | Create | Empty — makes `tests/` a package |
| `tests/test_install.py` | Create | Unit tests for `resolve_scope_path` and `copy_skill` |
| `SKILL.md` | Modify | Update CLI commands to reference `<base_dir>/scripts/` |

---

## Task 1: Switch to non-editable pip install

**Files:**
- Modify: `install.py:31`

- [ ] **Step 1: Change the pip install command**

In `install.py`, find this line inside `main()`:

```python
    run(
        [sys.executable, "-m", "pip", "install", "-e", ".[browser]"],
        "Installing package and dependencies",
    )
```

Change to:

```python
    run(
        [sys.executable, "-m", "pip", "install", ".[browser]"],
        "Installing package and dependencies",
    )
```

- [ ] **Step 2: Verify the change looks right**

Run: `python -c "import install; import inspect; print(inspect.getsource(install.main))" 2>&1 | head -10`

Expected: the pip command shown has no `-e` flag.

- [ ] **Step 3: Commit**

```bash
git add install.py
git commit -m "Switch to non-editable pip install so CLI commands survive repo moves"
```

---

## Task 2: Add test infrastructure

**Files:**
- Modify: `pyproject.toml`
- Create: `tests/__init__.py`

- [ ] **Step 1: Add pytest to pyproject.toml dev dependencies**

In `pyproject.toml`, the `[project.optional-dependencies]` section currently has:

```toml
[project.optional-dependencies]
browser = [
    "playwright>=1.40.0",
]
```

Add a `dev` extra below it:

```toml
[project.optional-dependencies]
browser = [
    "playwright>=1.40.0",
]
dev = [
    "pytest>=8.0",
]
```

- [ ] **Step 2: Install dev deps**

Run: `pip install -e ".[dev]"`

Expected: pytest installs successfully.

- [ ] **Step 3: Create empty tests package**

Create `tests/__init__.py` with empty content (zero bytes).

- [ ] **Step 4: Verify pytest can discover tests**

Run: `pytest tests/ --collect-only`

Expected: `no tests ran` (no test file yet — this confirms discovery works).

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml tests/__init__.py
git commit -m "Add pytest dev dependency and tests package"
```

---

## Task 3: Implement `resolve_scope_path()` with TDD

**Files:**
- Create: `tests/test_install.py`
- Modify: `install.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_install.py`:

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_install.py -v`

Expected: 3 errors — `ImportError: cannot import name 'resolve_scope_path'`

- [ ] **Step 3: Add imports and helpers to install.py**

At the top of `install.py`, after the existing `import sys`, add:

```python
import shutil
from pathlib import Path
```

After the `run()` function definition (before `def main()`), add:

```python
SKILL_DEST_NAME = "notebooklm"


def _repo_root() -> Path:
    return Path(__file__).parent


def resolve_scope_path(scope: str) -> Path:
    """Return destination directory for given scope ('user' or 'repo')."""
    if scope == "user":
        return Path.home() / ".claude" / "skills" / SKILL_DEST_NAME
    if scope == "repo":
        return _repo_root() / ".claude" / "skills" / SKILL_DEST_NAME
    raise ValueError(f"Unknown scope: {scope!r}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_install.py::test_resolve_scope_user tests/test_install.py::test_resolve_scope_repo tests/test_install.py::test_resolve_scope_invalid -v`

Expected: 3 passed.

- [ ] **Step 5: Commit**

```bash
git add install.py tests/test_install.py
git commit -m "Add resolve_scope_path with tests"
```

---

## Task 4: Implement `copy_skill()` with TDD

**Files:**
- Modify: `tests/test_install.py`
- Modify: `install.py`

- [ ] **Step 1: Add failing tests for copy_skill**

Append to `tests/test_install.py`:

```python
from install import copy_skill


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_install.py -k "copy_skill" -v`

Expected: 3 errors — `ImportError: cannot import name 'copy_skill'`

- [ ] **Step 3: Implement copy_skill() in install.py**

After `resolve_scope_path()`, add:

```python
def copy_skill(dest: Path) -> None:
    """Copy SKILL.md and nblm_skill/*.py into dest/scripts/."""
    scripts = dest / "scripts"
    scripts.mkdir(parents=True, exist_ok=True)
    shutil.copy2(_repo_root() / "SKILL.md", dest / "SKILL.md")
    for py_file in (_repo_root() / "nblm_skill").glob("*.py"):
        shutil.copy2(py_file, scripts / py_file.name)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_install.py -v`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add install.py tests/test_install.py
git commit -m "Add copy_skill with tests"
```

---

## Task 5: Add prompt helpers, `install_skill()`, and wire into `main()`

**Files:**
- Modify: `install.py`

- [ ] **Step 1: Add `_prompt_scope()` after `copy_skill()`**

```python
def _prompt_scope() -> str | None:
    """Prompt user for install scope. Returns 'user', 'repo', or None (skip)."""
    print("\nWhere should the Claude Code skill be installed?")
    print("  [1] User scope  — ~/.claude/skills/notebooklm/   (available in all projects)")
    print("  [2] Repo scope  — .claude/skills/notebooklm/      (this project only)")
    print("  [3] Skip")
    while True:
        choice = input("Enter choice [1/2/3]: ").strip()
        if choice == "1":
            return "user"
        if choice == "2":
            return "repo"
        if choice == "3":
            return None
        print("  Invalid choice. Enter 1, 2, or 3.")
```

- [ ] **Step 2: Add `_confirm_overwrite()` after `_prompt_scope()`**

```python
def _confirm_overwrite(dest: Path) -> bool:
    """Return True if user confirms overwrite of existing skill at dest."""
    print(f"\nSkill already installed at: {dest}")
    return input("Overwrite? [y/N]: ").strip().lower() == "y"
```

- [ ] **Step 3: Add `install_skill()` after `_confirm_overwrite()`**

```python
def install_skill() -> None:
    scope = _prompt_scope()
    if scope is None:
        print("Skipping skill install.")
        return
    dest = resolve_scope_path(scope)
    if (dest / "SKILL.md").exists():
        if not _confirm_overwrite(dest):
            print("Skipping skill install.")
            return
    copy_skill(dest)
    print(f"\nSkill installed to: {dest}")
    print("To update the skill later, re-run: python install.py")
```

- [ ] **Step 4: Wire `install_skill()` into `main()`**

In `main()`, find the section:

```python
    print("\n" + "=" * 60)
    print("  Setup complete.")
    print("=" * 60)
```

Add a skill install block immediately before it:

```python
    print("\n" + "=" * 60)
    print("  Installing Claude Code skill")
    print("=" * 60)
    install_skill()

    print("\n" + "=" * 60)
    print("  Setup complete.")
    print("=" * 60)
```

- [ ] **Step 5: Run all tests to confirm nothing broke**

Run: `pytest tests/ -v`

Expected: all tests pass.

- [ ] **Step 6: Smoke test the installer interactively**

Run: `python install.py`

Walk through the prompts:
- At the skill scope prompt, enter `3` (Skip) — verify "Skipping skill install." prints.
- Run again, enter `2` (Repo scope) — verify `.claude/skills/notebooklm/SKILL.md` is created.
- Run again, enter `2` — verify overwrite prompt appears, enter `N` — verify skip message.
- Run again, enter `2` — verify overwrite prompt appears, enter `y` — verify file is overwritten.

- [ ] **Step 7: Commit**

```bash
git add install.py
git commit -m "Add install_skill step to install.py with scope prompt and overwrite confirmation"
```

---

## Task 6: Update SKILL.md to reference scripts via base directory

**Files:**
- Modify: `SKILL.md`

Claude Code injects `Base directory for this skill: <path>` into every skill's system context. The skill should instruct Claude to build script paths from that injected base directory.

- [ ] **Step 1: Replace the CLI commands table and examples**

In `SKILL.md`, replace the entire `## CLI commands (available after install)` section (lines 12–45) with:

```markdown
## Scripts and CLI commands

The scripts for this skill are in the `scripts/` subdirectory alongside this `SKILL.md`.
Claude Code injects the skill's base directory as:
  `Base directory for this skill: <path>`
Use that injected path to construct script invocations.

**Primary (always works — relative to skill location):**
```bash
PYTHONUTF8=1 python "<base_dir>/scripts/nblm_list.py"
PYTHONUTF8=1 python "<base_dir>/scripts/nblm_list.py" --notebook 1
PYTHONUTF8=1 python "<base_dir>/scripts/nblm_list.py" --notebook "CRISPR"
```

```bash
PYTHONUTF8=1 python "<base_dir>/scripts/nblm_query.py" --notebook 1 --question "What is the main finding?"
PYTHONUTF8=1 python "<base_dir>/scripts/nblm_query.py" --notebook 1 --sources 2,5 --question "..."
PYTHONUTF8=1 python "<base_dir>/scripts/nblm_query.py" --notebook 1 --question "..." --conv-id <uuid>
```

```bash
PYTHONUTF8=1 python "<base_dir>/scripts/nblm_pipeline.py" --legs '[
  {"notebook": 1, "sources": [1, 2], "question": "What are the behavioral triggers?"},
  {"notebook": 3, "sources": [4, 5], "question": "What are the red flags?"}
]'
```

**Convenience aliases (available only when pip-installed):**
```bash
PYTHONUTF8=1 nblm-list
PYTHONUTF8=1 nblm-query --notebook 1 --question "..."
PYTHONUTF8=1 nblm-pipeline --legs '[...]'
```

Returns:
- `nblm-list` (no args): `{ notebooks: [{index, id, title}] }`
- `nblm-list --notebook N`: `{ notebook_title, sources: [{index, id, short_id, title}] }`
- `nblm-query`: `{ notebook_title, question, sources_used, answer, conversation_id, references }`
- `nblm-pipeline`: `{ pipeline: [{ leg, notebook_title, question, sources_used, answer, conversation_id, references, elapsed_ms }] }`

Always prefix with `PYTHONUTF8=1` on Windows.
```

- [ ] **Step 2: Verify SKILL.md renders cleanly**

Open `SKILL.md` and confirm:
- No broken code fences
- `<base_dir>` appears as a literal placeholder (not a shell variable)
- Both primary and convenience command blocks are present

- [ ] **Step 3: Commit**

```bash
git add SKILL.md
git commit -m "Update SKILL.md to reference scripts via injected base_dir"
```

---

## Self-review checklist

- [x] **Non-editable install** — Task 1 removes `-e`
- [x] **Scope prompt (user/repo/skip)** — Task 5 `_prompt_scope()`
- [x] **Conflict check with overwrite confirm** — Task 5 `_confirm_overwrite()`; default N
- [x] **Copy SKILL.md + nblm_skill/*.py to dest/scripts/** — Task 4 `copy_skill()`
- [x] **Confirmation message + re-run hint** — Task 5 `install_skill()`
- [x] **SKILL.md uses base_dir-relative paths** — Task 6
- [x] **CLI commands remain as convenience** — Task 6
- [x] **All new pure functions have tests** — Tasks 3 and 4
- [x] **No TBD or placeholders** — all steps show complete code
