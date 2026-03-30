"""
Ask a question to a specific notebook with optional source selection.

CLI (after pip install):
    nblm-query --notebook 1 --question "What is the main finding?"
    nblm-query --notebook 1 --sources 2,5 --question "..."
    nblm-query --notebook "Shieldly" --question "Summarise all sources"
    nblm-query --notebook 1 --question "..." --conv-id <uuid>   # follow-up

Output: JSON to stdout
"""

import argparse
import asyncio
import json
import sys

import notebooklm


def _short_id(uuid_str: str) -> str:
    return uuid_str.replace("-", "")[:8]


def _resolve_notebook(notebooks, ref: str) -> tuple[str, str]:
    notebooks_list = list(notebooks)
    try:
        idx = int(ref)
        if 1 <= idx <= len(notebooks_list):
            nb = notebooks_list[idx - 1]
            return nb.id, nb.title
        raise ValueError(f"No notebook at index {idx}. Valid range: 1–{len(notebooks_list)}")
    except ValueError as e:
        if "No notebook" in str(e):
            raise

    ref_lower = ref.lower()
    matches = [nb for nb in notebooks_list if ref_lower in nb.title.lower()]
    if len(matches) == 1:
        return matches[0].id, matches[0].title
    if len(matches) > 1:
        raise ValueError(f"Ambiguous: '{ref}' matches {[nb.title for nb in matches]}")
    raise ValueError(f"No notebook matches '{ref}'")


def _resolve_sources(sources_list, indexes: list[int]) -> tuple[list[str], list[dict]]:
    ids, meta = [], []
    for idx in indexes:
        if 1 <= idx <= len(sources_list):
            src = sources_list[idx - 1]
            ids.append(src.id)
            meta.append({"index": idx, "id": src.id, "short_id": _short_id(src.id), "title": src.title or "(untitled)"})
        else:
            raise ValueError(f"Source index {idx} out of range. Valid: 1–{len(sources_list)}")
    return ids, meta


async def run_query(notebook_ref: str, question: str, source_indexes: list[int] | None, conv_id: str | None) -> dict:
    async with await notebooklm.NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        notebook_id, notebook_title = _resolve_notebook(notebooks, notebook_ref)

        source_ids, sources_used = None, []
        if source_indexes:
            sources_list = list(await client.sources.list(notebook_id))
            source_ids, sources_used = _resolve_sources(sources_list, source_indexes)

        result = await client.chat.ask(notebook_id, question, source_ids=source_ids, conversation_id=conv_id)

    references = [
        {"source_id": r.source_id, "citation_number": getattr(r, "citation_number", None), "cited_text": r.cited_text}
        for r in (result.references or [])
    ]

    return {
        "notebook_id": notebook_id,
        "notebook_title": notebook_title,
        "question": question,
        "sources_used": sources_used,
        "answer": result.answer,
        "conversation_id": result.conversation_id,
        "turn_number": result.turn_number,
        "is_follow_up": result.is_follow_up,
        "references": references,
    }


def main():
    parser = argparse.ArgumentParser(description="Ask a question to a NotebookLM notebook")
    parser.add_argument("--notebook", "-n", required=True, help="Notebook index or title prefix")
    parser.add_argument("--question", "-q", required=True, help="The question to ask")
    parser.add_argument("--sources", "-s", default=None,
                        help="Comma-separated source indexes (e.g. '1,3,5'). Omit to query all.")
    parser.add_argument("--conv-id", "-c", default=None, help="Conversation ID for follow-up")
    args = parser.parse_args()

    source_indexes = None
    if args.sources:
        try:
            source_indexes = [int(x.strip()) for x in args.sources.split(",") if x.strip()]
        except ValueError:
            print(json.dumps({"error": True, "code": "INVALID_SOURCES", "message": f"Invalid: {args.sources}"}), file=sys.stderr)
            sys.exit(1)

    try:
        result = asyncio.run(run_query(args.notebook, args.question, source_indexes, args.conv_id))
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
