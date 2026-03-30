# NotebookLM-OnSteroids

Multi-notebook, multi-source research pipelines for Google NotebookLM, with a Claude Code skill that correlates answers across notebooks into a final synthesized insight.

## What it does

**Standard NotebookLM:** Ask a question inside one notebook.

**NotebookLM-OnSteroids:**
- Query any notebook by number or title
- Select specific sources within a notebook
- Run a **research pipeline**: ask different questions across different notebooks, then correlate all answers into a single final answer

### Example 1: Biology research

You have two notebooks. One contains CRISPR papers. Another contains clinical trial reports.

> *"From notebook 1 sources 1 and 2: what are the known mechanisms behind CRISPR off-target edits?*
> *From notebook 2 sources 3 and 4: what adverse effects have been reported in CRISPR gene therapy trials?*
> *Final: based on those mechanisms and adverse effects, which genomic regions carry the highest risk in clinical applications?"*

NotebookLM answers each leg from its own grounded sources. Claude then correlates both answers into the final response.

### Example 2: Climate science

You have one notebook of ocean temperature studies and another of atmospheric modelling papers.

> *"From notebook 1 sources 1 to 3: what do the studies say about ocean heat absorption trends over the past decade?*
> *From notebook 2 sources 2 and 5: what feedback loops are predicted to accelerate warming beyond 2 degrees?*
> *Final: given those absorption trends and feedback loops, which geographic regions face the most acute near-term climate risk?"*

---

## Installation

**Prerequisites:** Python 3.12+, a Google account with NotebookLM notebooks.

```bash
git clone https://github.com/your-username/NotebookLM-OnSteroids.git
cd NotebookLM-OnSteroids
python install.py
```

`install.py` handles everything:
1. `pip install -e ".[browser]"` - installs the package and Playwright
2. `playwright install chromium` - downloads the browser for Google login

**Then authenticate once:**
```bash
notebooklm login
```

This opens a browser. Sign in with the Google account that owns your notebooks. The session is saved to `~/.notebooklm/profiles/default/storage_state.json`. If your session expires later, just run `notebooklm login` again.

---

## CLI commands

### List notebooks
```bash
PYTHONUTF8=1 nblm-list
```
```json
{
  "notebooks": [
    {"index": 1, "id": "25dbba0e-...", "title": "CRISPR Research Papers"},
    {"index": 2, "id": "dbaf11f0-...", "title": "Gene Therapy Clinical Trials"}
  ]
}
```

### List sources in a notebook
```bash
PYTHONUTF8=1 nblm-list --notebook 1
PYTHONUTF8=1 nblm-list --notebook "CRISPR"   # fuzzy title match
```

### Ask a question
```bash
# All sources
PYTHONUTF8=1 nblm-query --notebook 1 --question "What is the main finding?"

# Specific sources only
PYTHONUTF8=1 nblm-query --notebook 1 --sources 1,3 --question "What are the known off-target mechanisms?"

# Follow-up on the same conversation thread
PYTHONUTF8=1 nblm-query --notebook 1 --question "Can you elaborate on Cas9 specificity?" --conv-id <uuid>
```

### Research pipeline
```bash
PYTHONUTF8=1 nblm-pipeline --legs '[
  {"notebook": 1, "sources": [1, 2], "question": "What are the known off-target edit mechanisms?"},
  {"notebook": 2, "sources": [3, 4], "question": "What adverse effects appear in clinical trial reports?"}
]'

# Or load legs from a file
PYTHONUTF8=1 nblm-pipeline --legs-file my_pipeline.json
```

All three commands output clean JSON to stdout. Errors go to stderr.

---

## Claude Code skill

Copy `SKILL.md` into your Claude Code skills directory for full conversational support:

```
~/.claude/skills/notebooklm/SKILL.md
```

Once installed, you can say things like:
- *"List my notebooks"*
- *"From notebook 1 sources 1 and 3, summarise the key findings"*
- *"Run a pipeline: notebook 1 sources 1 and 2, ask about off-target mechanisms; notebook 2 sources 3 and 4, ask about adverse effects. Final: which genomic regions are highest risk?"*

Claude handles intent parsing, runs the CLI commands, and synthesizes the results.

---

## How it works

The three CLI tools use the `notebooklm-py` Python API directly (async, no subprocess overhead). They handle:
- Notebook resolution by index or fuzzy title match
- Source resolution by index number
- Conversation threading across turns
- Source caching within a pipeline run (one auth session for all legs)

The final synthesis step runs in Claude's context. NotebookLM answers per-notebook from its grounded sources. Claude correlates across notebooks to answer the harder question that no single notebook could answer alone.

---

## Dependencies

| Package | Role |
|---------|------|
| `notebooklm-py >= 0.3.4` | Python API for NotebookLM (auth and RPC) |
| `httpx >= 0.27` | Async HTTP |
| `playwright >= 1.40` | Browser automation for `notebooklm login` |
