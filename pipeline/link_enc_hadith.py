"""Strict Enc ↔ Sahihayn linking (full-string ratio only; no containment).

Links store enc_id + proof_url on hadiths and optional gradings/translations.
Never invents grades — only copies stored HadeethEnc fields when ratio ≥ threshold.
"""

from __future__ import annotations

import sqlite3

from rapidfuzz import fuzz

from muhaqqiq.db import init_db

# Full-string fidelity — same spirit as Enc matching (no query ⊆ long matn)
MIN_RATIO = 99.0


def link_enc_to_sahihayn(conn: sqlite3.Connection, *, min_ratio: float = MIN_RATIO) -> int:
    enc_rows = conn.execute(
        "SELECT enc_id, text_ar, norm_skeleton, attribution, grade, reference, url FROM enc_hadiths"
    ).fetchall()
    hadiths = conn.execute("SELECT id, norm_skeleton FROM hadiths").fetchall()
    if not enc_rows or not hadiths:
        return 0

    # Index by length buckets for a cheaper scan
    by_len: dict[int, list] = {}
    for h in hadiths:
        n = len(h["norm_skeleton"] or "")
        by_len.setdefault(n, []).append(h)

    linked = 0
    sid_row = conn.execute("SELECT id FROM sources WHERE name = ?", ("HadeethEnc",)).fetchone()
    sid = int(sid_row["id"]) if sid_row else None

    for er in enc_rows:
        skeleton = er["norm_skeleton"] or ""
        if len(skeleton) < 12:
            continue
        best_id = None
        best_score = 0.0
        # Exact length ±10%
        lo, hi = int(len(skeleton) * 0.9), int(len(skeleton) * 1.1) + 1
        for n in range(lo, hi + 1):
            for h in by_len.get(n, []):
                if h["norm_skeleton"] == skeleton:
                    best_id, best_score = int(h["id"]), 100.0
                    break
                s = float(fuzz.ratio(skeleton, h["norm_skeleton"]))
                if s > best_score:
                    best_score = s
                    best_id = int(h["id"])
            if best_score >= 100.0:
                break
        if best_id is None or best_score < min_ratio:
            continue

        url = er["url"] or f"https://hadeethenc.com/ar/hadeeth/{er['enc_id']}"
        conn.execute(
            "UPDATE hadiths SET enc_id = ?, proof_url = ? WHERE id = ?",
            (er["enc_id"], url, best_id),
        )
        grade = (er["grade"] or "").strip()
        if grade and sid is not None:
            conn.execute(
                "DELETE FROM gradings WHERE hadith_id=? AND source_id=?",
                (best_id, sid),
            )
            conn.execute(
                """
                INSERT INTO gradings
                  (hadith_id, grader, grade_label, grade_normalized, reference, url, source_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    best_id,
                    (er["attribution"] or "HadeethEnc").strip() or "HadeethEnc",
                    grade,
                    grade,
                    (er["reference"] or f"HadeethEnc #{er['enc_id']}").strip(),
                    url,
                    sid,
                ),
            )
        linked += 1
    return linked


def main() -> None:
    conn = init_db()
    try:
        n = link_enc_to_sahihayn(conn)
        conn.commit()
        print(f"Linked {n} Sahihayn rows to HadeethEnc (ratio≥{MIN_RATIO})")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
