"""Parse the Data sources table in README.md into structured rows for the licenses page."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES_MD = ROOT / "README.md"
OUT_JSON = ROOT / "apps" / "web" / "src" / "generated" / "sources.json"


def source_status(use: str, version: str) -> str:
    """Classify whether a source is shown as in-use on the public page."""
    if version.strip().lower() == "blocked":
        return "blocked"
    if "link-out" in use.lower() or "link out" in use.lower():
        return "link_out"
    return "used"


def parse_sources_md(text: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    in_table = False
    for line in text.splitlines():
        if line.startswith("| Name |"):
            in_table = True
            continue
        if in_table and line.startswith("| ---"):
            continue
        if in_table and line.startswith("|"):
            cells = [c.strip() for c in line.strip("|").split("|")]
            if len(cells) < 7:
                continue
            use, version = cells[1], cells[4]
            url = cells[5]
            if url in {"—", "-", "n/a", ""}:
                url = ""
            rows.append(
                {
                    "name": cells[0],
                    "use": use,
                    "license": cells[2],
                    "attribution": cells[3].strip('"'),
                    "version": version,
                    "url": url,
                    "script": cells[6],
                    "status": source_status(use, version),
                }
            )
            continue
        if in_table and not line.startswith("|"):
            in_table = False
    return rows


def main() -> None:
    rows = parse_sources_md(SOURCES_MD.read_text(encoding="utf-8"))
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    payload = {"source": "README.md", "sources": rows}
    OUT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    used = sum(1 for r in rows if r["status"] == "used")
    print(f"wrote {len(rows)} sources ({used} used) → {OUT_JSON.relative_to(ROOT)}")
    names = " ".join(r["name"] for r in rows)
    if "Tanzil" not in names or "Dorar" not in names:
        raise SystemExit("README sources table parse missing expected rows")


if __name__ == "__main__":
    main()
