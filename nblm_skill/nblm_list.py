"""
List notebooks or sources.

CLI (after pip install):
    nblm-list                        # list all notebooks
    nblm-list --notebook 1           # list sources in notebook 1 (by index)
    nblm-list --notebook "Shieldly"  # fuzzy match by title

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


async def list_notebooks() -> list[dict]:
    async with await notebooklm.NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
    return [{"index": i + 1, "id": nb.id, "title": nb.title} for i, nb in enumerate(notebooks)]


async def list_sources(notebook_ref: str) -> dict:
    async with await notebooklm.NotebookLMClient.from_storage() as client:
        notebooks = await client.notebooks.list()
        notebook_id, notebook_title = _resolve_notebook(notebooks, notebook_ref)
        sources = await client.sources.list(notebook_id)

    return {
        "notebook_id": notebook_id,
        "notebook_title": notebook_title,
        "sources": [
            {
                "index": i + 1,
                "id": src.id,
                "short_id": _short_id(src.id),
                "title": src.title or "(untitled)",
                "status": src.status,
            }
            for i, src in enumerate(sources)
        ],
        "count": len(sources),
    }


def main():
    parser = argparse.ArgumentParser(description="List NotebookLM notebooks or sources")
    parser.add_argument("--notebook", "-n", default=None,
                        help="Notebook index or title prefix. Omit to list all notebooks.")
    args = parser.parse_args()

    try:
        if args.notebook is None:
            result = asyncio.run(list_notebooks())
            print(json.dumps({"notebooks": result, "count": len(result)}, ensure_ascii=False, indent=2))
        else:
            result = asyncio.run(list_sources(args.notebook))
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
