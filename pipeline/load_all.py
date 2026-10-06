"""Build SQLite DB from pinned raw sources + fabricated seed."""

from __future__ import annotations

import csv
import json
import sqlite3
from datetime import UTC, datetime
from pathlib import Path

from muhaqqiq.db import ROOT, init_db
from muhaqqiq.normalize import normalize, strip_bidi

RAW = ROOT / "data" / "raw"
SEED = ROOT / "data" / "fabricated_seed.csv"


def _upsert_source(
    conn: sqlite3.Connection,
    *,
    name: str,
    url: str,
    license_: str,
    attribution: str,
    version: str,
) -> int:
    row = conn.execute("SELECT id FROM sources WHERE name = ?", (name,)).fetchone()
    if row:
        conn.execute(
            """
            UPDATE sources SET url=?, license=?, attribution=?, version=?, retrieved_at=?
            WHERE id=?
            """,
            (url, license_, attribution, version, datetime.now(UTC).date().isoformat(), row["id"]),
        )
        return int(row["id"])
    cur = conn.execute(
        """
        INSERT INTO sources (name, url, license, attribution, version, retrieved_at)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name, url, license_, attribution, version, datetime.now(UTC).date().isoformat()),
    )
    return int(cur.lastrowid)


def _rebuild_fts(conn: sqlite3.Connection) -> None:
    # contentless FTS5 tables cannot DELETE; drop and recreate
    conn.executescript(
        """
        DROP TABLE IF EXISTS quran_fts;
        DROP TABLE IF EXISTS hadith_fts;
        DROP TABLE IF EXISTS claims_fts;
        CREATE VIRTUAL TABLE quran_fts USING fts5(
          norm_skeleton, verse_id UNINDEXED, content='', tokenize='unicode61'
        );
        CREATE VIRTUAL TABLE hadith_fts USING fts5(
          norm_skeleton, hadith_id UNINDEXED, content='', tokenize='unicode61'
        );
        CREATE VIRTUAL TABLE claims_fts USING fts5(
          norm_skeleton, claim_id UNINDEXED, content='', tokenize='unicode61'
        );
        """
    )
    # contentless fts5 only exposes rowid on MATCH — keep rowid == source table id
    for r in conn.execute("SELECT id, norm_skeleton FROM quran_verses"):
        conn.execute(
            "INSERT INTO quran_fts (rowid, norm_skeleton, verse_id) VALUES (?, ?, ?)",
            (r["id"], r["norm_skeleton"], r["id"]),
        )
    for r in conn.execute("SELECT id, norm_skeleton FROM hadiths"):
        conn.execute(
            "INSERT INTO hadith_fts (rowid, norm_skeleton, hadith_id) VALUES (?, ?, ?)",
            (r["id"], r["norm_skeleton"], r["id"]),
        )
    for r in conn.execute("SELECT id, norm_skeleton FROM known_claims"):
        conn.execute(
            "INSERT INTO claims_fts (rowid, norm_skeleton, claim_id) VALUES (?, ?, ?)",
            (r["id"], r["norm_skeleton"], r["id"]),
        )


def load_quran(conn: sqlite3.Connection) -> int:
    path = RAW / "quran" / "quran.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    sid = _upsert_source(
        conn,
        name="Tanzil (via quran-json)",
        url="https://tanzil.net/",
        license_="CC BY 3.0",
        attribution="Quran text from Tanzil.net (CC BY 3.0). Distributed via quran-json.",
        version="quran-json@3.1.2",
    )
    conn.execute("DELETE FROM quran_verses")
    n = 0
    # quran-json: list of surahs with verses[{text, id}] or nested
    surahs = data if isinstance(data, list) else data.get("surahs") or data.get("chapters")
    for sura in surahs:
        sura_num = int(sura.get("id") or sura.get("number"))
        verses = sura.get("verses") or sura.get("ayahs") or []
        for verse in verses:
            aya = int(verse.get("id") or verse.get("number") or verse.get("aya"))
            text = verse.get("text") or verse.get("text_uthmani") or ""
            text = strip_bidi(text.strip())
            if not text:
                continue
            clean = text
            skeleton = normalize(clean)
            conn.execute(
                """
                INSERT INTO quran_verses
                  (sura, aya, text_uthmani, text_clean, norm_skeleton, source_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (sura_num, aya, text, clean, skeleton, sid),
            )
            n += 1
    return n


def _load_hadith_edition(conn: sqlite3.Connection, path: Path, collection: str, source_id: int) -> int:
    data = json.loads(path.read_text(encoding="utf-8"))
    hadiths = data.get("hadiths") or data
    n = 0
    if isinstance(hadiths, dict):
        # sometimes keyed by number
        items = hadiths.values()
    else:
        items = hadiths
    for h in items:
        if not isinstance(h, dict):
            continue
        number = str(h.get("hadithnumber") or h.get("number") or h.get("id") or "")
        text = strip_bidi((h.get("text") or h.get("body") or "").strip())
        if not text:
            continue
        if not number:
            number = str(n + 1)
        skeleton = normalize(text)
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO hadiths
                  (collection, number, text_ar, text_clean, norm_skeleton, source_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (collection, number, text, text, skeleton, source_id),
            )
            n += 1
        except sqlite3.IntegrityError:
            continue
    return n


def load_hadith(conn: sqlite3.Connection) -> tuple[int, int]:
    sid = _upsert_source(
        conn,
        name="fawazahmed0/hadith-api",
        url="https://github.com/fawazahmed0/hadith-api",
        license_="See edition licenses in upstream repo",
        attribution="Arabic hadith editions from fawazahmed0/hadith-api (jsDelivr).",
        version="hadith-api@1",
    )
    conn.execute("DELETE FROM hadiths")
    b = _load_hadith_edition(conn, RAW / "hadith" / "ara-bukhari.json", "Bukhari", sid)
    m = _load_hadith_edition(conn, RAW / "hadith" / "ara-muslim.json", "Muslim", sid)
    return b, m


def load_known_claims(conn: sqlite3.Connection) -> int:
    if not SEED.exists():
        return 0
    sid = _upsert_source(
        conn,
        name="Curated fabricated/weak seed",
        url="",
        license_="Attribution per row",
        attribution="Rulings attributed to named scholars; see fabricated_seed.csv.",
        version="seed-v0",
    )
    conn.execute("DELETE FROM known_claim_rulings")
    conn.execute("DELETE FROM known_claims")
    n_rulings = 0
    claim_ids: dict[str, int] = {}
    with SEED.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            text = strip_bidi((row.get("text_ar") or "").strip())
            if not text:
                continue
            skeleton = normalize(text)
            if skeleton not in claim_ids:
                cur = conn.execute(
                    """
                    INSERT INTO known_claims (text_ar, norm_skeleton, claim_type, notes)
                    VALUES (?, ?, ?, ?)
                    """,
                    (text, skeleton, row.get("claim_type") or "hadith", ""),
                )
                claim_ids[skeleton] = int(cur.lastrowid)
            claim_id = claim_ids[skeleton]
            conn.execute(
                """
                INSERT INTO known_claim_rulings
                  (claim_id, grader, ruling, reference, url, source_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    claim_id,
                    row.get("grader") or "غير مسمى",
                    row.get("ruling") or "",
                    row.get("reference") or "",
                    row.get("url") or "",
                    sid,
                ),
            )
            n_rulings += 1
    return n_rulings


def main() -> None:
    from pipeline.load_enc import load_all_enc
    from pipeline.validate import validate_sqlite

    if not (RAW / "quran" / "quran.json").exists():
        from pipeline.download_sources import main as download

        download()
    conn = init_db()
    try:
        q = load_quran(conn)
        b, m = load_hadith(conn)
        k = load_known_claims(conn)
        qe, he = load_all_enc(conn)
        _rebuild_fts(conn)
        conn.commit()
        validate_sqlite(conn)
        print(
            f"Loaded quran={q} bukhari={b} muslim={m} claim_rulings={k} "
            f"quranenc_tr={qe} hadeethenc={he}"
        )
        print(f"DB → {ROOT / 'data' / 'build' / 'muhaqqiq.db'}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
