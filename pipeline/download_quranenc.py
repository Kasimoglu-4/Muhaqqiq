"""Download QuranEnc EN/TR meanings (Add-next enrichment; no Arabic overwrite)."""

from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import httpx

from pipeline.common import RAW, sha256_bytes, update_manifest

BASE = "https://quranenc.com/api/v1/translation/sura"
TRANSLATIONS = {
    "en": "english_saheeh",
    "tr": "turkish_rwwad",
}


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--full", action="store_true", help="All 114 suras (default)")
    args = parser.parse_args(argv)

    out_dir = RAW / "quranenc"
    out_dir.mkdir(parents=True, exist_ok=True)
    max_sura = 114 if args.full else int(os.environ.get("MUHAQQIQ_QURANENC_MAX_SURA", "114"))
    meta_entries: list[dict] = []
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        for lang, key in TRANSLATIONS.items():
            bundle: dict[str, list] = {}
            for sura in range(1, max_sura + 1):
                url = f"{BASE}/{key}/{sura}"
                r = client.get(url)
                r.raise_for_status()
                payload = r.json()
                rows = payload.get("result") if isinstance(payload, dict) else payload
                if not isinstance(rows, list):
                    rows = [rows] if rows else []
                bundle[str(sura)] = rows
                print(f"QuranEnc {lang} sura {sura}/{max_sura}")
            dest = out_dir / f"{lang}_{key}.json"
            raw = json.dumps(
                {"translation_key": key, "lang": lang, "suras": bundle},
                ensure_ascii=False,
            ).encode("utf-8")
            dest.write_bytes(raw)
            meta_entries.append(
                {
                    "url": f"{BASE}/{key}/{{1..{max_sura}}}",
                    "path": str(dest.relative_to(Path(__file__).resolve().parents[1])).replace(
                        "\\", "/"
                    ),
                    "sha256": sha256_bytes(raw),
                    "retrieved_at": datetime.now(UTC).date().isoformat(),
                    "bytes": len(raw),
                }
            )
    update_manifest(meta_entries)
    print(f"QuranEnc → {out_dir} ({max_sura} suras × {len(TRANSLATIONS)} langs)")


if __name__ == "__main__":
    main()
