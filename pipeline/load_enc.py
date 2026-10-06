"""Load QuranEnc / HadeethEnc enrichment into SQLite (never overwrites Core Arabic)."""

from __future__ import annotations

import json
import sqlite3
from datetime import UTC, datetime

from muhaqqiq.db import ROOT
from muhaqqiq.normalize import normalize, strip_bidi

RAW = ROOT / "data" / "raw"


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


def load_quranenc(conn: sqlite3.Connection) -> int:
    qdir = RAW / "quranenc"
    if not qdir.exists():
        return 0
    sid = _upsert_source(
        conn,
        name="QuranEnc",
        url="https://quranenc.com/",
        license_="No modify; credit QuranEnc.com; mention translation version",
        attribution="Quran meanings from QuranEnc.com (EN/TR). Not a substitute for Arabic.",
        version="API v1",
    )
    n = 0
    for path in sorted(qdir.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        lang = data.get("lang") or "en"
        suras = data.get("suras") or {}
        for rows in suras.values():
            if not isinstance(rows, list):
                continue
            for row in rows:
                try:
                    sura = int(row.get("sura"))
                    aya = int(row.get("aya"))
                except (TypeError, ValueError):
                    continue
                text = strip_bidi((row.get("translation") or "").strip())
                if not text:
                    continue
                verse = conn.execute(
                    "SELECT id FROM quran_verses WHERE sura=? AND aya=?",
                    (sura, aya),
                ).fetchone()
                if not verse:
                    continue
                conn.execute(
                    "DELETE FROM translations WHERE kind='quran' AND ref_id=? AND lang=?",
                    (verse["id"], lang),
                )
                conn.execute(
                    """
                    INSERT INTO translations (kind, ref_id, lang, text, source_id)
                    VALUES ('quran', ?, ?, ?, ?)
                    """,
                    (verse["id"], lang, text, sid),
                )
                n += 1
    return n


def load_hadeethenc(conn: sqlite3.Connection) -> int:
    path = RAW / "hadeethenc" / "hadeeths_bundle.json"
    if not path.exists():
        return 0
    sid = _upsert_source(
        conn,
        name="HadeethEnc",
        url="https://hadeethenc.com/",
        license_="No modify; credit HadeethEnc.com; keep per-row attribution",
        attribution="Grades and translations from HadeethEnc.com",
        version="API v1",
    )
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items") or []
    conn.execute("DELETE FROM enc_hadiths")
    # Remove prior Enc-linked gradings without hadith_id (enc-only)
    n = 0
    for item in items:
        enc_id = str(item.get("id") or "")
        ar = item.get("ar") or {}
        if isinstance(ar, dict) and ar.get("error"):
            continue
        text_ar = strip_bidi((ar.get("hadeeth") or ar.get("hadeeth_ar") or "").strip())
        if not text_ar:
            continue
        grade = (ar.get("grade") or ar.get("grade_ar") or "").strip()
        attribution = (ar.get("attribution") or ar.get("attribution_ar") or "").strip()
        reference = (ar.get("reference") or "").strip() or f"HadeethEnc #{enc_id}"
        url = f"https://hadeethenc.com/ar/hadeeth/{enc_id}"
        skeleton = normalize(text_ar)
        conn.execute(
            """
            INSERT OR REPLACE INTO enc_hadiths
              (enc_id, text_ar, norm_skeleton, attribution, grade, reference, url, source_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (enc_id, text_ar, skeleton, attribution, grade, reference, url, sid),
        )
        # Defer Sahihayn linking to strict full-string pass (see link_enc_hadith)
        # Still attach EN/TR translations when exact skeleton matches.
        hrow = conn.execute(
            "SELECT id FROM hadiths WHERE norm_skeleton = ? LIMIT 1",
            (skeleton,),
        ).fetchone()
        if hrow:
            conn.execute(
                "UPDATE hadiths SET enc_id = ?, proof_url = ? WHERE id = ?",
                (enc_id, url, hrow["id"]),
            )
            if grade:
                conn.execute(
                    "DELETE FROM gradings WHERE hadith_id=? AND source_id=?",
                    (hrow["id"], sid),
                )
                conn.execute(
                    """
                    INSERT INTO gradings
                      (hadith_id, grader, grade_label, grade_normalized, reference, url, source_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        hrow["id"],
                        attribution or "HadeethEnc",
                        grade,
                        grade,
                        reference,
                        url,
                        sid,
                    ),
                )
            for lang_key, lang in (("en", "en"), ("tr", "tr")):
                blob = item.get(lang_key) or {}
                t = strip_bidi((blob.get("hadeeth") or "").strip()) if isinstance(blob, dict) else ""
                if not t:
                    continue
                conn.execute(
                    "DELETE FROM translations WHERE kind='hadith' AND ref_id=? AND lang=?",
                    (hrow["id"], lang),
                )
                conn.execute(
                    """
                    INSERT INTO translations (kind, ref_id, lang, text, source_id)
                    VALUES ('hadith', ?, ?, ?, ?)
                    """,
                    (hrow["id"], lang, t, sid),
                )
        n += 1
    return n


def load_all_enc(conn: sqlite3.Connection) -> tuple[int, int]:
    from pipeline.link_enc_hadith import link_enc_to_sahihayn

    q = load_quranenc(conn)
    h = load_hadeethenc(conn)
    linked = link_enc_to_sahihayn(conn)
    print(f"Enc strict Sahihayn links={linked}")
    return q, h
