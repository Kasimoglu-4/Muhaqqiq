"""Download HadeethEnc graded items + EN/TR text (Add-next; attribution preserved).

Full pin: default MUHAQQIQ_HADEETHENC_MAX=0 (all), or pass --full.
Resume: merges into data/raw/hadeethenc/hadeeths_bundle.json; reuses ids.json.
"""

from __future__ import annotations

import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path

import httpx

from pipeline.common import RAW, ROOT, sha256_bytes, update_manifest

LIST_URL = "https://hadeethenc.com/api/v1/hadeeths/list/"
ONE_URL = "https://hadeethenc.com/api/v1/hadeeths/one/"
CATS_URL = "https://hadeethenc.com/api/v1/categories/list/"
LANGS = ("ar", "en", "tr")
WORKERS = int(os.environ.get("MUHAQQIQ_HADEETHENC_WORKERS", "8"))


def _max_items(cli_full: bool) -> int:
    if cli_full:
        return 0
    raw = os.environ.get("MUHAQQIQ_HADEETHENC_MAX", "0").strip()
    if raw.lower() in {"", "0", "all", "full"}:
        return 0
    return int(raw)


def _collect_ids(client: httpx.Client, max_items: int) -> list[str]:
    cats = client.get(CATS_URL, params={"language": "ar"}).json()
    out_dir = RAW / "hadeethenc"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "categories_ar.json").write_text(
        json.dumps(cats, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    ids: list[str] = []
    seen: set[str] = set()
    cat_list = cats if isinstance(cats, list) else []
    for cat in cat_list:
        if max_items and len(ids) >= max_items:
            break
        cid = cat.get("id")
        if not cid:
            continue
        page = 1
        while True:
            if max_items and len(ids) >= max_items:
                break
            r = client.get(
                LIST_URL,
                params={
                    "language": "ar",
                    "category_id": cid,
                    "page": page,
                    "per_page": 100,
                },
            )
            r.raise_for_status()
            body = r.json()
            data = body.get("data") if isinstance(body, dict) else body
            if not data:
                break
            for item in data:
                hid = str(item.get("id") or "")
                if not hid or hid in seen:
                    continue
                seen.add(hid)
                ids.append(hid)
                if max_items and len(ids) >= max_items:
                    break
            meta = body.get("meta") if isinstance(body, dict) else {}
            last = int(meta.get("last_page") or page) if meta else page
            if page >= last:
                break
            page += 1
        if int(cid) % 25 == 0 or cid in {"1", "7"}:
            print(f"HadeethEnc ids after cat {cid}: {len(ids)}")
    return ids


def _fetch_one(hid: str) -> dict:
    detail: dict = {"id": hid}
    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        for lang in LANGS:
            try:
                r = client.get(ONE_URL, params={"id": hid, "language": lang})
                r.raise_for_status()
                detail[lang] = r.json()
            except (httpx.HTTPError, ValueError) as e:
                detail[lang] = {"error": str(e)}
    return detail


def _write_bundle(items: list[dict], dest: Path) -> None:
    raw = json.dumps(
        {"items": items, "count": len(items)},
        ensure_ascii=False,
    ).encode("utf-8")
    dest.write_bytes(raw)
    update_manifest(
        [
            {
                "url": ONE_URL,
                "path": str(dest.relative_to(ROOT)).replace("\\", "/"),
                "sha256": sha256_bytes(raw),
                "retrieved_at": datetime.now(UTC).date().isoformat(),
                "bytes": len(raw),
            }
        ]
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--full",
        action="store_true",
        help="Download all HadeethEnc items (ignore small caps)",
    )
    parser.add_argument(
        "--refresh-ids",
        action="store_true",
        help="Re-collect ids.json even if present",
    )
    args = parser.parse_args(argv)

    out_dir = RAW / "hadeethenc"
    out_dir.mkdir(parents=True, exist_ok=True)
    dest = out_dir / "hadeeths_bundle.json"
    ids_path = out_dir / "ids.json"
    max_items = _max_items(args.full)

    with httpx.Client(follow_redirects=True, timeout=60.0) as client:
        if ids_path.exists() and not args.refresh_ids and not max_items:
            ids = json.loads(ids_path.read_text(encoding="utf-8"))
            print(f"HadeethEnc reusing {len(ids)} ids from {ids_path}")
        else:
            ids = _collect_ids(client, max_items)
            ids_path.write_text(json.dumps(ids, ensure_ascii=False), encoding="utf-8")
            print(f"HadeethEnc collected {len(ids)} unique ids → {ids_path}")

    have: dict[str, dict] = {}
    if dest.exists():
        try:
            prev = json.loads(dest.read_text(encoding="utf-8"))
            for item in prev.get("items") or []:
                hid = str(item.get("id") or "")
                if hid and isinstance(item.get("ar"), dict) and not item["ar"].get("error"):
                    have[hid] = item
        except json.JSONDecodeError:
            pass
        print(f"HadeethEnc resume: {len(have)} already downloaded")

    pending = [hid for hid in ids if hid not in have]
    print(f"HadeethEnc to fetch: {len(pending)} (workers={WORKERS})")

    by_id = dict(have)
    done = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {pool.submit(_fetch_one, hid): hid for hid in pending}
        for fut in as_completed(futures):
            hid = futures[fut]
            by_id[hid] = fut.result()
            done += 1
            if done % 50 == 0 or done == len(pending):
                items = [by_id[i] for i in ids if i in by_id]
                _write_bundle(items, dest)
                print(f"HadeethEnc fetched {done}/{len(pending)} (bundle={len(items)})")

    items = [by_id[i] for i in ids if i in by_id]
    _write_bundle(items, dest)
    print(f"HadeethEnc → {dest} ({len(items)} items)")


if __name__ == "__main__":
    main()
