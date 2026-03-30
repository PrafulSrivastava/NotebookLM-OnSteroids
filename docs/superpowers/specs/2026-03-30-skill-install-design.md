# Skill Install Feature — Design Spec
**Date:** 2026-03-30

## Overview

Extend `install.py` to install the NotebookLM-OnSteroids Claude Code skill alongside the Python dependencies, in a single command. Users choose user scope (global) or repo scope (local), and the skill folder is structured to match the standard Claude Code skill layout so scripts are referenced relative to the skill's position — independent of where it is installed.

---

## Goals

- One command (`python install.py`) handles everything: deps, browser, skill
- Skill works at user scope (`~/.claude/skills/notebooklm/`) or repo scope (`.claude/skills/notebooklm/`)
- Scripts referenced via `<base_dir>/scripts/` — no hardcoded paths
- CLI commands (`nblm-list`, `nblm-query`, `nblm-pipeline`) remain as convenience wrappers

---

## Non-goals

- Symlinks (copy only)
- Auto-updates to the skill after initial install
- Changes to the Python package API or CLI command behaviour

---

## Install flow

### Step 1 — Package install (changed from editable to non-editable)

```
pip install ".[browser]"
```

Previously `pip install -e ".[browser]"` (editable). Changed to non-editable so `nblm_skill/*.py` are copied into site-packages and the CLI entry points (`nblm-list`, `nblm-query`, `nblm-pipeline`) survive the repo being moved or deleted.

### Step 2 — Playwright browser (unchanged)

```
playwright install chromium
```

### Step 3 — Skill install (new)

**Scope prompt:**
```
Where should the Claude Code skill be installed?
  [1] User scope  — ~/.claude/skills/notebooklm/   (available in all projects)
  [2] Repo scope  — .claude/skills/notebooklm/      (this project only)
  [3] Skip
Enter choice [1/2/3]:
```

- Invalid input re-prompts (loop until valid).
- Choice `3` prints "Skipping skill install." and exits the step cleanly.

**Conflict check:**
If `SKILL.md` already exists at the destination:
```
Skill already installed at: <path>
Overwrite? [y/N]:
```
Default is **N** (skip). Only proceeds on explicit `y` or `Y`.

**Copy:**
1. Create `<dest>/scripts/` directory if it does not exist (`parents=True, exist_ok=True`)
2. Copy `SKILL.md` → `<dest>/SKILL.md`
3. Copy all `nblm_skill/*.py` → `<dest>/scripts/`

**Confirmation:**
```
Skill installed to: <dest>
To update the skill later, re-run: python install.py
```

---

## Installed skill layout

```
<dest>/
  SKILL.md
  scripts/
    __init__.py
    nblm_list.py
    nblm_query.py
    nblm_pipeline.py
```

Where `<dest>` is one of:
- `~/.claude/skills/notebooklm/` (user scope)
- `.claude/skills/notebooklm/` (repo scope, relative to repo root)

---

## SKILL.md changes

The CLI commands section is updated to reference scripts relative to the skill's location. Claude Code injects the skill's base directory as a `Base directory for this skill: <path>` line in every skill's system context — so SKILL.md instructs Claude to construct script paths from that injected base directory, not from a hardcoded absolute path or a shell variable.

Example wording in SKILL.md:
```
Scripts are in the `scripts/` subdirectory alongside this SKILL.md.
Use the base directory provided in your system context to build paths, e.g.:
  PYTHONUTF8=1 python "<base_dir>/scripts/nblm_list.py"
  PYTHONUTF8=1 python "<base_dir>/scripts/nblm_query.py" --notebook 1 --question "..."
  PYTHONUTF8=1 python "<base_dir>/scripts/nblm_pipeline.py" --legs '[...]'

If the pip-installed CLI commands are available, they can be used instead:
  PYTHONUTF8=1 nblm-list
  PYTHONUTF8=1 nblm-query --notebook 1 --question "..."
  PYTHONUTF8=1 nblm-pipeline --legs '[...]'
```

---

## Files changed

| File | Change |
|------|--------|
| `install.py` | Switch to non-editable install; add Step 3 (skill install) |
| `SKILL.md` | Update CLI command examples to use `<base_dir>/scripts/` as primary |

---

## Error handling

| Situation | Behaviour |
|-----------|-----------|
| User enters invalid scope choice | Re-prompt in a loop |
| Destination exists, user says N | Print "Skipping skill install." and continue |
| Destination exists, user says Y | Overwrite |
| `SKILL.md` missing from repo root | Print error and exit step (should never happen in a clean clone) |
| `nblm_skill/` missing from repo | Print error and exit step |

---

## Dependencies

No new dependencies. Uses only stdlib: `pathlib`, `shutil`, `sys`.
