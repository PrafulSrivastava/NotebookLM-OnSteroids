"""
One-command setup for NotebookLM-OnSteroids.

    python install.py

What it does:
  1. pip install -e ".[browser]"   — installs this package + playwright
  2. playwright install chromium   — downloads the browser for login
  3. Prints next steps (notebooklm login)
"""

import subprocess
import sys


def run(cmd: list[str], desc: str) -> None:
    print(f"\n>>> {desc}")
    print(f"    {' '.join(cmd)}\n")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"\n[ERROR] Command failed (exit {result.returncode}). Fix the error above and re-run install.py.")
        sys.exit(result.returncode)


def main():
    print("=" * 60)
    print("  NotebookLM-OnSteroids — Setup")
    print("=" * 60)

    run(
        [sys.executable, "-m", "pip", "install", ".[browser]"],
        "Installing package and dependencies",
    )

    run(
        [sys.executable, "-m", "playwright", "install", "chromium"],
        "Installing Chromium browser (used for Google login)",
    )

    print("\n" + "=" * 60)
    print("  Setup complete.")
    print("=" * 60)
    print("""
Next step — authenticate with Google (run once):

    notebooklm login

This opens a browser. Sign in with the Google account that
owns your NotebookLM notebooks. The session is saved to:

    ~/.notebooklm/profiles/default/storage_state.json

After that, the three CLI commands are ready:

    nblm-list                            # list all notebooks
    nblm-list --notebook 1               # list sources in notebook 1
    nblm-query --notebook 1 -q "..."     # ask a question
    nblm-pipeline --legs '[...]'         # run a research pipeline

If your session expires later, just run:  notebooklm login
""")


if __name__ == "__main__":
    main()
