"""
Run a multi-leg research pipeline across notebooks.
Claude does the final synthesis — this handles the plumbing.

CLI (after pip install):
    nblm-pipeline --legs '[
        {"notebook": 1, "sources": [1, 2], "question": "What are the behavioral triggers?"},
        {"notebook": 3, "sources": [4, 5], "question": "What are the red flags?"}
    ]'

    nblm-pipeline --legs-file pipeline.json

Each leg:
    notebook  : int (index) or str (title prefix)  — required
    sources   : list[int] (source indexes)          — optional, omit = all sources
    question  : str                                 — required
    conv_id   : str                                 — optional, for follow-ups

Output: JSON to stdout. All legs share one auth session for efficiency.
"""

import argparse
import asyncio
import json
import sys
import time

import notebooklm


def _short_id(uuid_str: str) -> str:
    return uuid_str.replace("-", "")[:8]


def _resolve_notebook(notebooks_list: list, ref) -> tuple[str, str]:
    try:
        idx = int(ref)
        if 1 <= idx <= len(notebooks_list):
            nb = notebooks_list[idx - 1]
            return nb.id, nb.title
        raise ValueError(f"No notebook at index {idx}. Valid range: 1–{len(notebooks_list)}")
    except ValueError as e:
        if "No notebook" in str(e):
            raise

    ref_lower = str(ref).lower()
    matches = [nb for nb in notebooks_list if ref_lower in nb.title.lower()]
    if len(matches) == 1:
        return matches[0].id, matches[0].title
    if len(matches) > 1:
        raise ValueError(f"Ambiguous: '{ref}' matches {[nb.title for nb in matches]}")
    raise ValueError(f"No notebook matches '{ref}'")


def _resolve_source_ids(sources_list: list, indexes: list[int]) -> tuple[list[str], list[dict]]:
    ids, meta = [], []
    for idx in indexes:
        if 1 <= idx <= len(sources_list):
            src = sources_list[idx - 1]
            ids.append(src.id)
            meta.append({"index": idx, "id": src.id, "short_id": _short_id(src.id), "title": src.title or "(untitled)"})
        else:
            raise ValueError(f"Source index {idx} out of range. Valid: 1–{len(sources_list)}")
    return ids, meta


async def run_pipeline(legs: list[dict]) -> dict:
    async with await notebooklm.NotebookLMClient.from_storage() as client:
        notebooks_list = list(await client.notebooks.list())
        sources_cache: dict[str, list] = {}
        results = []

        for leg_num, leg in enumerate(legs, start=1):
            notebook_ref = leg.get("notebook")
            question = leg.get("question", "").strip()
            source_indexes: list[int] | None = leg.get("sources")
            conv_id: str | None = leg.get("conv_id")

            if not notebook_ref:
                raise ValueError(f"Leg {leg_num} missing 'notebook'")
            if not question:
                raise ValueError(f"Leg {leg_num} missing 'question'")

            notebook_id, notebook_title = _resolve_notebook(notebooks_list, notebook_ref)

            source_ids, sources_meta = None, []
            if source_indexes:
                if notebook_id not in sources_cache:
                    sources_cache[notebook_id] = list(await client.sources.list(notebook_id))
                source_ids, sources_meta = _resolve_source_ids(sources_cache[notebook_id], source_indexes)

            t_start = time.monotonic()
            ask_result = await client.chat.ask(notebook_id, question, source_ids=source_ids, conversation_id=conv_id)
            elapsed_ms = int((time.monotonic() - t_start) * 1000)

            references = [
                {"source_id": r.source_id, "citation_number": getattr(r, "citation_number", None), "cited_text": r.cited_text}
                for r in (ask_result.references or [])
            ]

            results.append({
                "leg": leg_num,
                "notebook_id": notebook_id,
                "notebook_title": notebook_title,
                "question": question,
                "sources_used": sources_meta,
                "answer": ask_result.answer,
                "conversation_id": ask_result.conversation_id,
                "references": references,
                "elapsed_ms": elapsed_ms,
            })

    return {
        "pipeline": results,
        "leg_count": len(results),
        "notebooks_used": list({r["notebook_title"] for r in results}),
    }


def main():
    parser = argparse.ArgumentParser(description="Run a multi-leg NotebookLM research pipeline")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--legs", "-l", help="JSON string defining legs array")
    group.add_argument("--legs-file", "-f", help="Path to JSON file with legs array")
    args = parser.parse_args()

    try:
        if args.legs_file:
            with open(args.legs_file, encoding="utf-8") as fh:
                legs = json.load(fh)
        else:
            legs = json.loads(args.legs)
    except (json.JSONDecodeError, OSError) as e:
        print(json.dumps({"error": True, "code": "PARSE_ERROR", "message": str(e)}), file=sys.stderr)
        sys.exit(1)

    if not isinstance(legs, list) or not legs:
        print(json.dumps({"error": True, "code": "INVALID_LEGS", "message": "legs must be a non-empty array"}), file=sys.stderr)
        sys.exit(1)

    try:
        result = asyncio.run(run_pipeline(legs))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except notebooklm.AuthError as e:
        print(json.dumps({"error": True, "code": "AUTH_EXPIRED", "message": str(e)}), file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(json.dumps({"error": True, "code": "RESOLUTION_ERROR", "message": str(e)}), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(json.dumps({"error": True, "code": "ERROR", "message": str(e)}), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
