"""CI-blocking data validation."""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path

from pipeline.sura_lengths import SURA_VERSE_COUNTS

BIDI_RE = re.compile(r"[\u200c-\u200f\u202a-\u202e]")


def _fail(msg: str) -> None:
    raise SystemExit(f"VALIDATION FAILED: {msg}")


def validate_sqlite(conn: sqlite3.Connection) -> None:
    verses = conn.execute("SELECT COUNT(*) FROM quran_verses").fetchone()[0]
    if verses != 6236:
        _fail(f"expected 6236 verses, got {verses}")

    suras = conn.execute("SELECT COUNT(DISTINCT sura) FROM quran_verses").fetchone()[0]
    if suras != 114:
        _fail(f"expected 114 suras, got {suras}")

    rows = conn.execute(
        "SELECT sura, COUNT(*) AS n FROM quran_verses GROUP BY sura ORDER BY sura"
    ).fetchall()
    for sura, n in rows:
        expected = SURA_VERSE_COUNTS[sura - 1]
        if n != expected:
            _fail(f"sura {sura}: expected {expected} verses, got {n}")

    empty_h = conn.execute(
        "SELECT COUNT(*) FROM hadiths WHERE text_ar IS NULL OR trim(text_ar) = ''"
    ).fetchone()[0]
    if empty_h:
        _fail(f"{empty_h} hadith with empty text")

    missing_h = conn.execute(
        "SELECT COUNT(*) FROM hadiths WHERE collection IS NULL OR number IS NULL "
        "OR trim(collection) = '' OR trim(number) = ''"
    ).fetchone()[0]
    if missing_h:
        _fail(f"{missing_h} hadith missing collection/number")

    bad_sources = conn.execute(
        "SELECT COUNT(*) FROM sources WHERE license IS NULL OR trim(license) = '' "
        "OR attribution IS NULL OR trim(attribution) = ''"
    ).fetchone()[0]
    if bad_sources:
        _fail(f"{bad_sources} sources missing license/attribution")

    bad_rulings = conn.execute(
        "SELECT COUNT(*) FROM known_claim_rulings WHERE grader IS NULL OR trim(grader) = '' "
        "OR ruling IS NULL OR trim(ruling) = '' OR reference IS NULL OR trim(reference) = ''"
    ).fetchone()[0]
    if bad_rulings:
        _fail(f"{bad_rulings} known_claim_rulings missing grader/ruling/reference")

    # Encoding / bidi control characters in stored display text
    for table, col in (("quran_verses", "text_uthmani"), ("hadiths", "text_ar")):
        for row in conn.execute(f"SELECT id, {col} AS t FROM {table}"):
            if row["t"] and BIDI_RE.search(row["t"]):
                _fail(f"{table}.id={row['id']} contains bidi control characters")

    # Duplicate skeletons within Quran (should be rare but sura/aya unique is enough);
    # flag duplicate (collection, number) already enforced by UNIQUE.
    print(
        "Validation OK:",
        f"{verses} verses,",
        f"{suras} suras,",
        f"{conn.execute('SELECT COUNT(*) FROM hadiths').fetchone()[0]} hadiths,",
        f"{conn.execute('SELECT COUNT(*) FROM known_claims').fetchone()[0]} known claims,",
        f"{conn.execute('SELECT COUNT(*) FROM sources').fetchone()[0]} sources,",
        f"translations={conn.execute('SELECT COUNT(*) FROM translations').fetchone()[0]},",
        f"gradings={conn.execute('SELECT COUNT(*) FROM gradings').fetchone()[0]},",
        f"enc_hadiths={conn.execute('SELECT COUNT(*) FROM enc_hadiths').fetchone()[0]}",
    )


def main(db_path: str | None = None) -> None:
    from muhaqqiq.db import DEFAULT_DB, connect, init_db

    path = Path(db_path) if db_path else DEFAULT_DB
    if not path.exists():
        _fail(f"DB not found: {path} (run make data first)")
    conn = init_db(connect(path))
    try:
        validate_sqlite(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
