"""Download fawazahmed0 Arabic Bukhari and Muslim editions."""

from __future__ import annotations

from pipeline.common import RAW, fetch, update_manifest

BUKHARI = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-bukhari.json"
MUSLIM = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/ara-muslim.json"
EDITIONS = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions.json"


def main() -> None:
    meta = [
        fetch(EDITIONS, RAW / "hadith" / "editions.json"),
        fetch(BUKHARI, RAW / "hadith" / "ara-bukhari.json"),
        fetch(MUSLIM, RAW / "hadith" / "ara-muslim.json"),
    ]
    update_manifest(meta)
    for m in meta:
        print(f"Hadith → {m['path']} sha256={m['sha256'][:12]}…")


if __name__ == "__main__":
    main()
