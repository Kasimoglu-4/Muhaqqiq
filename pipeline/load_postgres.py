"""Load pinned data into Postgres (Phase 1). Requires DATABASE_URL."""

from __future__ import annotations

import csv
import json
import os
from datetime import UTC, datetime

from muhaqqiq.db import ROOT
from muhaqqiq.normalize import normalize, strip_bidi

RAW = ROOT / "data" / "raw"
SEED = ROOT / "data" / "fabricated_seed.csv"
SCHEMA = ROOT / "schema" / "postgres.sql"


def _connect():
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as e:
        raise SystemExit("psycopg not installed; uv sync --group postgres") from e

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL is required for Postgres load")
    conn = psycopg.connect(url, row_factory=dict_row)
    return conn


def _upsert_source(cur, *, name, url, license_, attribution, version) -> int:
    cur.execute("SELECT id FROM sources WHERE name = %s", (name,))
    row = cur.fetchone()
    today = datetime.now(UTC).date()
    if row:
        cur.execute(
            """
            UPDATE sources SET url=%s, license=%s, attribution=%s, version=%s, retrieved_at=%s
            WHERE id=%s
            """,
            (url, license_, attribution, version, today, row["id"]),
        )
        return int(row["id"])
    cur.execute(
        """
        INSERT INTO sources (name, url, license, attribution, version, retrieved_at)
        VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
        """,
        (name, url, license_, attribution, version, today),
    )
    return int(cur.fetchone()["id"])


def main() -> None:
    if not (RAW / "quran" / "quran.json").exists():
        from pipeline.download_sources import main as download

        download()

    conn = _connect()
    try:
        # Apply schema statements one-by-one (psycopg runs one command per execute)
        for stmt in SCHEMA.read_text(encoding="utf-8").split(";"):
            stmt = stmt.strip()
            if stmt:
                with conn.cursor() as cur:
                    cur.execute(stmt)

        with conn.cursor() as cur:
            for table in (
                "known_claim_rulings",
                "known_claims",
                "gradings",
                "translations",
                "cards",
                "hadiths",
                "quran_verses",
            ):
                cur.execute(f"TRUNCATE {table} RESTART IDENTITY CASCADE")

            q_sid = _upsert_source(
                cur,
                name="Tanzil (via quran-json)",
                url="https://tanzil.net/",
                license_="CC BY 3.0",
                attribution="Quran text from Tanzil.net (CC BY 3.0). Distributed via quran-json.",
                version="quran-json@3.1.2",
            )
            data = json.loads((RAW / "quran" / "quran.json").read_text(encoding="utf-8"))
            qn = 0
            for sura in data:
                sura_num = int(sura["id"])
                for verse in sura["verses"]:
                    text = strip_bidi(verse["text"].strip())
                    cur.execute(
                        """
                        INSERT INTO quran_verses
                          (sura, aya, text_uthmani, text_clean, norm_skeleton, source_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (sura_num, int(verse["id"]), text, text, normalize(text), q_sid),
                    )
                    qn += 1

            h_sid = _upsert_source(
                cur,
                name="fawazahmed0/hadith-api",
                url="https://github.com/fawazahmed0/hadith-api",
                license_="See edition licenses in upstream repo editions.json",
                attribution="Arabic hadith editions from fawazahmed0/hadith-api (jsDelivr).",
                version="hadith-api@1",
            )
            hn = 0
            for path, collection in (
                (RAW / "hadith" / "ara-bukhari.json", "Bukhari"),
                (RAW / "hadith" / "ara-muslim.json", "Muslim"),
            ):
                payload = json.loads(path.read_text(encoding="utf-8"))
                for h in payload.get("hadiths") or []:
                    number = str(h.get("hadithnumber") or h.get("number") or "")
                    text = strip_bidi((h.get("text") or "").strip())
                    if not text or not number:
                        continue
                    cur.execute(
                        """
                        INSERT INTO hadiths
                          (collection, number, text_ar, text_clean, norm_skeleton, source_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        ON CONFLICT (collection, number) DO UPDATE SET
                          text_ar=EXCLUDED.text_ar,
                          text_clean=EXCLUDED.text_clean,
                          norm_skeleton=EXCLUDED.norm_skeleton
                        """,
                        (collection, number, text, text, normalize(text), h_sid),
                    )
                    hn += 1

            k_sid = _upsert_source(
                cur,
                name="Curated fabricated/weak seed",
                url="",
                license_="Attribution per row",
                attribution="Rulings attributed to named scholars; see fabricated_seed.csv.",
                version="seed-v0",
            )
            kn = 0
            with SEED.open(encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    text = strip_bidi((row.get("text_ar") or "").strip())
                    if not text:
                        continue
                    cur.execute(
                        """
                        INSERT INTO known_claims (text_ar, norm_skeleton, claim_type, notes)
                        VALUES (%s, %s, %s, %s) RETURNING id
                        """,
                        (
                            text,
                            normalize(text),
                            row.get("claim_type") or "hadith",
                            "",
                        ),
                    )
                    claim_id = cur.fetchone()["id"]
                    cur.execute(
                        """
                        INSERT INTO known_claim_rulings
                          (claim_id, grader, ruling, reference, url, source_id)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        (
                            claim_id,
                            row.get("grader") or "غير مسمى",
                            row.get("ruling") or "",
                            row.get("reference") or "",
                            row.get("url") or "",
                            k_sid,
                        ),
                    )
                    kn += 1

        conn.commit()

        # Validate via counts
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) AS n FROM quran_verses")
            verses = cur.fetchone()["n"]
            cur.execute("SELECT COUNT(DISTINCT sura) AS n FROM quran_verses")
            suras = cur.fetchone()["n"]
            if verses != 6236 or suras != 114:
                raise SystemExit(f"Postgres validation failed: verses={verses} suras={suras}")
        print(f"Postgres loaded quran={qn} hadiths={hn} known_claims={kn}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
