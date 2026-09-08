"""Render every mermaid block in the repository, so a diagram cannot reach GitHub broken.

Run:  uv run scripts/check_mermaid.py          validate all blocks
      uv run scripts/check_mermaid.py --keep    keep the rendered SVGs for inspection

GitHub renders mermaid itself and shows a parse error in place of the diagram, which
no link or anchor check can catch. This runs the real parser (@mermaid-js/mermaid-cli)
over each block and reports the file and line where a block starts.

Needs Node — `npx` on PATH. Exits 2 when Node is missing, so a caller can choose
whether that is a failure; lint_docs.py has a stdlib check for the traps we have
actually hit and does not depend on this script.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FENCE = "```"
MERMAID_CLI = "@mermaid-js/mermaid-cli@11"


def blocks() -> list[tuple[Path, int, str]]:
    """Every mermaid block as (file, first line of the block body, source)."""
    found = []
    for f in sorted(ROOT.rglob("*.md")):
        if ".git" in f.parts or ".venv" in f.parts:
            continue
        lines = f.read_text(encoding="utf-8").splitlines()
        start = None
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith(FENCE + "mermaid"):
                start = i
            elif start is not None and stripped == FENCE:
                found.append((f, start + 1, "\n".join(lines[start : i - 1]) + "\n"))
                start = None
    return found


def main(argv: list[str]) -> int:
    if not shutil.which("npx"):
        print("npx not found — install Node to validate mermaid blocks")
        return 2

    found = blocks()
    if not found:
        print("no mermaid blocks")
        return 0

    failures = []
    with tempfile.TemporaryDirectory() as tmp:
        tmpdir = Path(tmp)
        for f, line, source in found:
            rel = f.relative_to(ROOT)
            src = tmpdir / f"{str(rel).replace('/', '__')}__L{line}.mmd"
            src.write_text(source, encoding="utf-8")
            proc = subprocess.run(
                ["npx", "--yes", MERMAID_CLI, "-i", str(src), "-o", str(src.with_suffix(".svg"))],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                detail = next(
                    (l.strip() for l in proc.stderr.splitlines() if "error" in l.lower()),
                    proc.stderr.strip().splitlines()[-1] if proc.stderr.strip() else "unknown error",
                )
                failures.append(f"{rel}:{line}: {detail}")
            elif "--keep" in argv:
                shutil.copy(src.with_suffix(".svg"), ROOT / src.with_suffix(".svg").name)

    for problem in failures:
        print(problem)
    if failures:
        print(f"\n{len(failures)} of {len(found)} mermaid blocks fail to render")
        return 1
    print(f"OK: {len(found)} mermaid blocks render")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
