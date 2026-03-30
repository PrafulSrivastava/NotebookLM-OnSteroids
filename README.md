# NotebookLM-OnSteroids

Multi-notebook, multi-source research pipelines for Google NotebookLM — with a Claude Code skill that can correlate answers across notebooks into a final synthesized insight.

## What it does

**Standard NotebookLM:** Ask a question inside one notebook.

**NotebookLM-OnSteroids:**
- Query any notebook by number or title
- Select specific sources within a notebook
- Run a **research pipeline**: ask different questions across different notebooks, then correlate all answers into a single final answer

Example pipeline:
> *"From notebook 1 sources 1,2: what are the behavioral triggers women use before activating SOS?
> From notebook 3 sources 4,5: what are the common red flags in founding team dynamics?
> Final: which founder archetypes are most likely to build an app that fails women at the critical moment?"*

---

## Installation

**Prerequisites:** Python 3.12+, a Google account with NotebookLM notebooks.

```bash
git clone https://github.com/your-username/NotebookLM-OnSteroids.git
cd NotebookLM-OnSteroids
python install.py
```

`install.py` handles everything:
1. `pip install -e ".[browser]"` — installs the package + Playwright
2. `playwright install chromium` — downloads the browser for Google login

**Then authenticate once:**
```bash
notebooklm login
```

This opens a browser. Sign in with the Google account that owns your notebooks. Session is saved to `~/.notebooklm/profiles/default/storage_state.json`. If your session expires later, just run `notebooklm login` again.

---

## CLI commands

### List notebooks
```bash
PYTHONUTF8=1 nblm-list
```
```json
{
  "notebooks": [
    {"index": 1, "id": "25dbba0e-...", "title": "Zero-Friction UX Patterns"},
    {"index": 2, "id": "dbaf11f0-...", "title": "Founding Dilemmas"}
  ]
}
```

### List sources in a notebook
```bash
PYTHONUTF8=1 nblm-list --notebook 1
PYTHONUTF8=1 nblm-list --notebook "Zero-Friction"   # fuzzy title match
```

### Ask a question
```bash
# All sources
PYTHONUTF8=1 nblm-query --notebook 1 --question "What is the main finding?"

# Specific sources
PYTHONUTF8=1 nblm-query --notebook 1 --sources 2,5 --question "What are the behavioral triggers?"

# Follow-up (continue a conversation thread)
PYTHONUTF8=1 nblm-query --notebook 1 --question "Can you elaborate?" --conv-id <uuid>
```

### Research pipeline
```bash
PYTHONUTF8=1 nblm-pipeline --legs '[
  {"notebook": 1, "sources": [1, 2], "question": "What are the behavioral triggers?"},
  {"notebook": 2, "sources": [4, 5], "question": "What are the founding team red flags?"}
]'

# Or from a file
PYTHONUTF8=1 nblm-pipeline --legs-file my_pipeline.json
```

All three commands output clean JSON to stdout. Errors go to stderr.

---

## Claude Code skill

Copy `SKILL.md` into your Claude Code skills directory to get full conversational support:

```
~/.claude/skills/notebooklm/SKILL.md
```

Once installed, you can say things like:
- *"List my notebooks"*
- *"From notebook 1 sources 1 and 3, what are the key findings?"*
- *"Run a pipeline: notebook 1 sources 1,2 → behavioral triggers; notebook 2 sources 4,5 → red flags. Final: which personas are highest risk?"*

Claude will handle intent parsing, run the right CLI commands, and synthesize the results.

---

## How it works

The three CLI tools use the `notebooklm-py` Python API directly (async, no subprocess overhead). They handle:
- Notebook resolution by index or fuzzy title match
- Source resolution by index
- Conversation threading
- Source caching within a pipeline run

The final synthesis step runs entirely in Claude's context — NotebookLM answers per-notebook, Claude correlates across notebooks.

---

## Dependencies

| Package | Role |
|---------|------|
| `notebooklm-py >= 0.3.4` | Python API for NotebookLM (handles auth + RPC) |
| `httpx >= 0.27` | Async HTTP |
| `playwright >= 1.40` | Browser automation for `notebooklm login` |
