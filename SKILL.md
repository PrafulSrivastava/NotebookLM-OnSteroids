---
name: notebooklm
description: Chat with any NotebookLM notebook and its research sources. Use this skill whenever the user wants to ask questions about their research, query notebooks, mentions sources by number (e.g. "in sources 1, 5, 7"), wants to summarize papers, or do anything with their NotebookLM research vault. Also triggers on "ask notebooklm", "from source X", "what does the notebook say", "query my research", "from notebook 2 sources 3 and 4", "cross-notebook", "compare notebooks", "research pipeline", "correlate answers", "chain questions across notebooks", or any time the user references multiple notebooks or sources together for a combined insight.
---

# NotebookLM Skill

Query any notebook, any sources — from a single lookup to a full multi-notebook research pipeline with correlated answers.

Requires: `notebooklm-on-steroids` installed via `python install.py` (see README).

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

---

## Session state (track in memory across turns)

- `notebooks[]` — fetched once, reused all session
- `sources[notebook_id]` — fetched per notebook on demand, cached
- `conv_ids[notebook_id]` — conversation ID per notebook for follow-up threading
- `pipeline_results[]` — accumulated leg results when running a Research Pipeline

---

## Recognising the query type

### Type A — Simple query (one notebook, one question)
> "from notebook 1, sources 2 and 5: what is the main finding?"

### Type B — Multi-notebook query
> "compare notebook 1 and notebook 3 on user safety"

### Type C — Research Pipeline
Multiple targeted questions → final correlation question. Recognise when the user:
- Provides a distinct "final question" after multiple sub-questions
- Uses "correlate", "chain", "pipeline", "use all answers to…"

> "From notebook 1 sources 1,2: what are behavioral triggers?
>  From notebook 3 sources 4,5: what are founding red flags?
>  Final: which personas are highest-risk?"

### Type D — Navigation
> "list notebooks", "list sources in notebook 3", "switch to notebook 2"

---

## Research Pipeline — detailed flow

**Step 1 — Confirm the pipeline (for 3+ legs or complex final question)**
Show a structured plan before running:
```
Pipeline plan:
  Leg 1 → Notebook 1 "..." · Sources 1, 2
           Q: "..."
  Leg 2 → Notebook 3 "..." · Sources 4, 5
           Q: "..."
  Final → "..."
Run this pipeline?
```

**Step 2 — Execute legs**
Run `nblm-pipeline --legs '[...]'`. Announce each leg briefly as it runs.

**Step 3 — Synthesize in Claude's context**
The `nblm-pipeline` script collects all leg answers. Claude then synthesizes:

```markdown
## Leg 1 — [Notebook Title] · Sources X, Y
**Q:** [leg question]
[answer with citations]

## Leg 2 — [Notebook Title] · Sources P, Q
**Q:** [leg question]
[answer with citations]

---

## Final Answer — [synthesis question]
[Deep synthesis that explicitly draws on findings from each leg.
Name which leg contributes which insight. Surface tensions and confirmations.]
```

The Final Answer is the highest-value output — not a summary, but a new answer to a harder question.

**Step 4 — Offer follow-up options**
- "Re-run any leg with different sources"
- "Add another leg and re-synthesize"
- "Ask a new final question using the same leg results" (no re-run needed — results are cached in `pipeline_results[]`)

---

## Conversation continuity

- Store `conv_ids[notebook_id]` after each query — pass as `--conv-id` for follow-ups
- Each notebook has its own thread
- Pipeline leg results persist in `pipeline_results[]` — re-use with new final questions without re-running legs

---

## Special commands

| User says | Action |
|-----------|--------|
| "list notebooks" | `nblm-list` |
| "list sources in notebook X" | `nblm-list --notebook X` |
| "switch to notebook X" | Set active notebook in session |
| "re-run leg 2 with sources 6,7" | Re-run that leg, update `pipeline_results`, re-synthesize |
| "new final question: [Q]" | Re-synthesize against existing `pipeline_results` |
| "deep research on X" | `notebooklm source add-research -n <id> --mode deep --no-wait "<X>"` |

---

## Error handling

- **Auth expired** → tell user to run `notebooklm login`
- **Source number out of range** → re-run `nblm-list --notebook X`, show valid range
- **Empty answer from a leg** → note it, continue pipeline, flag in Final Answer
- **Ambiguous notebook** → show matches, ask user to confirm
