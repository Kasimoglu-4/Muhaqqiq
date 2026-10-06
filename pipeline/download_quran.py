"""Download Tanzil-based Quran Arabic text (via quran-json)."""

from __future__ import annotations

from pipeline.common import RAW, fetch, update_manifest

QURAN_JSON = "https://cdn.jsdelivr.net/npm/quran-json@3.1.2/dist/quran.json"


def main() -> None:
    meta = fetch(QURAN_JSON, RAW / "quran" / "quran.json")
    update_manifest([meta])
    print(f"Quran → {meta['path']} sha256={meta['sha256'][:12]}…")


if __name__ == "__main__":
    main()
