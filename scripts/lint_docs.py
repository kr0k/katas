"""Lint the submission's markdown for the things reviewers trip over.

Run:  uv run scripts/lint_docs.py

Checks
1. Every relative link resolves to a file, and every #anchor resolves to a heading
   (GitHub anchor rules) in the target file.
2. Every ADR file is listed in adrs/README.md and every listed ADR exists.
3. ADR <-> scenario symmetry: the ADRs a scenario README declares in its **ADRs:**
   line equal the ADRs in that scenario's row of the README traceability table.
4. Every FR marked with the AI emoji in requirements/03 links to a scenario.
5. Every FR-x.y / NFR-XXX-n / A-n / R-n / GD-n / ADR-nnnn id referenced anywhere
   is defined somewhere (requirements, game-day catalogue, adrs/).
6. No sentence of 12+ words appears twice anywhere in the corpus.
7. No mermaid block contains a ';' outside quotes — GitHub refuses to render it.
   scripts/check_mermaid.py renders every block with the real parser when Node is
   available; this check needs no Node.
8. The generated tables in the appendix models and the numbers derived from them in
   requirements/06 and the README match scripts/business_case.py (its --check).

Exit code 0 when clean, 1 when anything is wrong. Stdlib only.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import business_case  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
MD_FILES = sorted(p for p in ROOT.rglob("*.md") if ".git" not in p.parts and ".venv" not in p.parts)

LINK_RE = re.compile(r"\]\(([^)\s]+)\)")
HEADING_RE = re.compile(r"^#+\s+(.*?)\s*$")
ADR_ID_RE = re.compile(r"\bADR-\d{4}\b")
ID_PATTERNS = {
    "FR": re.compile(r"\bFR-\d+\.\d+\b"),
    "NFR": re.compile(r"\bNFR-[A-Z]+-\d+\b"),
    "A": re.compile(r"\bA\d{1,2}\b"),
    "R": re.compile(r"\bR\d{1,2}\b"),
    "GD": re.compile(r"\bGD-\d+\b"),
    "ADR": ADR_ID_RE,
}
# Files that *define* ids of a given kind (a table row starting with the id).
DEFINING_FILES = {
    "FR": [ROOT / "requirements/03-functional-requirements.md"],
    "NFR": [ROOT / "requirements/04-non-functional-requirements.md"],
    "A": [ROOT / "requirements/05-assumptions-and-constraints.md"],
    "R": [ROOT / "requirements/07-risks-and-mitigations.md"],
    "GD": [ROOT / "hld/core/resilience-validation.md"],
}

problems: list[str] = []


def rel(p: Path) -> str:
    return str(p.relative_to(ROOT))


def github_anchor(heading: str) -> str:
    a = heading.lower()
    a = re.sub(r"[^\w\s-]", "", a, flags=re.UNICODE)
    return a.strip().replace(" ", "-")


def prose_lines(path: Path):
    """Yield (line_no, line) skipping fenced code blocks."""
    in_code = False
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("```"):
            in_code = not in_code
            continue
        if not in_code:
            yield i, line


def check_links() -> None:
    anchors: dict[Path, set[str]] = {}
    for f in MD_FILES:
        anchors[f] = {github_anchor(m.group(1)) for _, l in prose_lines(f) if (m := HEADING_RE.match(l))}
    for f in MD_FILES:
        for ln, line in prose_lines(f):
            for link in LINK_RE.findall(line):
                if link.startswith(("http://", "https://", "mailto:")):
                    continue
                path, _, anchor = link.partition("#")
                target = f if path == "" else (f.parent / path).resolve()
                if not target.exists():
                    problems.append(f"{rel(f)}:{ln}: broken link {link}")
                    continue
                if anchor and target.is_file() and anchor not in anchors.get(target, set()):
                    problems.append(f"{rel(f)}:{ln}: missing anchor #{anchor} in {rel(target)}")


def check_adr_index() -> None:
    index = ROOT / "adrs/README.md"
    on_disk = {p.name for p in (ROOT / "adrs").glob("ADR-*.md")}
    listed = set(re.findall(r"\((ADR-\d{4}-[^)]+\.md)\)", index.read_text(encoding="utf-8")))
    for name in sorted(on_disk - listed):
        problems.append(f"adrs/README.md: {name} exists but is not in the index")
    for name in sorted(listed - on_disk):
        problems.append(f"adrs/README.md: {name} is listed but does not exist")


def check_scenario_symmetry() -> None:
    readme = ROOT / "README.md"
    rows: dict[str, set[str]] = {}
    for _, line in prose_lines(readme):
        m = re.search(r"\]\((hld/scenarios/[^/]+/README\.md)\)", line)
        if m and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            # traceability rows have 4 cells: capability | FR | HLD | ADRs; the scenario table has 5
            if len(cells) == 4:
                rows[m.group(1)] = set(ADR_ID_RE.findall(cells[3]))
    for scenario in sorted((ROOT / "hld/scenarios").glob("*/README.md")):
        key = rel(scenario)
        declared: set[str] = set()
        for _, line in prose_lines(scenario):
            if line.startswith("**ADRs:**"):
                declared = set(ADR_ID_RE.findall(line))
                break
        if not declared:
            problems.append(f"{key}: no **ADRs:** line")
            continue
        if key not in rows:
            problems.append(f"README.md: no traceability row links to {key}")
            continue
        for adr in sorted(declared - rows[key]):
            problems.append(f"README.md traceability: {key} declares {adr} but the row does not list it")
        for adr in sorted(rows[key] - declared):
            problems.append(f"{key}: README traceability lists {adr} but the scenario does not declare it")


def check_ai_frs_link_scenarios() -> None:
    frs = ROOT / "requirements/03-functional-requirements.md"
    for ln, line in prose_lines(frs):
        if "🤖" in line and line.startswith("| FR-") and "hld/scenarios/" not in line:
            problems.append(f"{rel(frs)}:{ln}: AI-marked FR does not link to a scenario")


def check_ids_defined() -> None:
    defined: dict[str, set[str]] = {k: set() for k in ID_PATTERNS}
    for kind, files in DEFINING_FILES.items():
        pat = ID_PATTERNS[kind]
        for f in files:
            for _, line in prose_lines(f):
                if line.startswith("|"):
                    first = line.strip("|").split("|")[0]
                    defined[kind].update(pat.findall(first))
    defined["ADR"] = {p.name[:8] for p in (ROOT / "adrs").glob("ADR-*.md")}
    for f in MD_FILES:
        if f.name == "TODOS.md":
            continue
        for ln, line in prose_lines(f):
            for kind, pat in ID_PATTERNS.items():
                for ident in pat.findall(line):
                    if ident not in defined[kind]:
                        problems.append(f"{rel(f)}:{ln}: {ident} is referenced but not defined")


MERMAID_QUOTED_RE = re.compile(r'"[^"]*"')


def check_mermaid_traps() -> None:
    """Catch the mermaid syntax that GitHub refuses to render.

    GitHub renders mermaid client-side and replaces a broken diagram with a parse
    error, which no link check sees. `scripts/check_mermaid.py` runs the real parser
    when Node is available; this covers the traps we have actually hit, with no
    dependency on it.
    """
    for f in MD_FILES:
        in_block = False
        block_start = 0
        for ln, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("```mermaid"):
                in_block, block_start = True, ln
                continue
            if in_block and stripped == "```":
                in_block = False
                continue
            if not in_block:
                continue
            # A semicolon separates statements in mermaid, so one inside an unquoted
            # label or message ends the statement early: the rest of the line is then
            # parsed as a new statement and the whole diagram fails.
            if ";" in MERMAID_QUOTED_RE.sub("", line):
                problems.append(
                    f"{rel(f)}:{ln}: ';' outside quotes in the mermaid block at line {block_start}"
                    " — mermaid reads it as a statement separator and the diagram will not render"
                )


SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?;])\s+")
INLINE_MD_RE = re.compile(r"\[([^\]]*)\]\([^)]*\)")


def check_duplicate_prose() -> None:
    """No sentence of 12+ words may appear twice in the corpus.

    Copy-paste is how the same fact ends up with two owners and then drifts. A fact
    belongs in one place; everywhere else links to it.
    """
    seen: dict[str, tuple[Path, int]] = {}
    for f in MD_FILES:
        for ln, line in prose_lines(f):
            text = INLINE_MD_RE.sub(r"\1", line)
            text = re.sub(r"[`*_>#|]", " ", text)
            text = re.sub(r"\s+", " ", text).strip()
            for sentence in SENTENCE_SPLIT_RE.split(text):
                words = sentence.lower().split()
                if len(words) < 12:
                    continue
                key = " ".join(words)
                if key in seen:
                    first = seen[key]
                    problems.append(
                        f"{rel(f)}:{ln}: sentence repeated from {rel(first[0])}:{first[1]} "
                        f"— keep the fact in one place and link to it: \"{sentence[:60]}...\""
                    )
                else:
                    seen[key] = (f, ln)


def check_business_case() -> None:
    problems.extend(business_case.check())


def main() -> int:
    check_links()
    check_adr_index()
    check_scenario_symmetry()
    check_ai_frs_link_scenarios()
    check_ids_defined()
    check_duplicate_prose()
    check_mermaid_traps()
    check_business_case()
    if problems:
        print("\n".join(sorted(set(problems))))
        print(f"\n{len(set(problems))} problem(s)")
        return 1
    print(f"OK: {len(MD_FILES)} markdown files, links/anchors, ADR index, scenario symmetry, FR links, ids, no duplicated prose, mermaid, business case")
    return 0


if __name__ == "__main__":
    sys.exit(main())
