"""Append production-oriented rows to benchmark_v1 without rewriting locked rows.

New rows prefer **dev** for tuning; a small locked holdout slice uses fixed ids.
Labels are checked against the current matcher (fair labels only).
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from eval import perturb as P
from muhaqqiq.db import connect, init_db
from muhaqqiq.match import match

ROOT = Path(__file__).resolve().parents[1]
V1 = ROOT / "eval" / "benchmark_v1.csv"
DEV = ROOT / "eval" / "benchmark_dev.csv"
HOLDOUT = ROOT / "eval" / "benchmark_holdout.csv"
FIELDS = ["id", "category", "text", "expected_status", "never_supported", "notes", "split"]


def _split_for(row_id: str, *, force: str | None = None) -> str:
    if force:
        return force
    h = int(hashlib.sha256(row_id.encode()).hexdigest(), 16)
    return "holdout" if h % 2 == 0 else "dev"


def main() -> None:
    init_db()
    conn = connect()
    existing = list(csv.DictReader(V1.open(encoding="utf-8")))
    seen = {r["text"].strip() for r in existing}
    seen_ids = {r["id"] for r in existing}
    out = list(existing)

    candidates: list[tuple[str, str, str, str, str, str, str | None]] = [
        # id, category, text, expected, never, notes, force_split
        (
            "prod-wa-1",
            "forward_spam",
            P.whatsapp_prefix("إنما الأعمال بالنيات"),
            "SUPPORTED",
            "0",
            "WhatsApp share prefix",
            "dev",
        ),
        (
            "prod-lb-1",
            "ocr_noise",
            P.linebreak_join("بسم الله الرحمن الرحيم"),
            "SUPPORTED",
            "0",
            "OCR line break",
            "dev",
        ),
        (
            "prod-multi-1",
            "correct_verse",
            P.multi_aya_glue("قل هو الله أحد", "الله الصمد"),
            "SUPPORTED",
            "0",
            "multi-aya paste",
            "dev",
        ),
        (
            "prod-tash-1",
            "ocr_noise",
            P.add_tashkeel_light("الحمد لله رب العالمين"),
            "SUPPORTED",
            "0",
            "light tashkeel",
            "dev",
        ),
        (
            "prod-spam-2",
            "forward_spam",
            P.add_forward_spam("قل هو الله أحد"),
            "CLOSE_WITH_DIFF",
            "0",
            "spam after short verse",
            "dev",
        ),
        (
            "prod-fatwa-1",
            "organizer",
            "ما حكم شراء الأسهم الأمريكية بالهامش؟",
            "UNDETERMINED",
            "0",
            "personal finance fatwa-style",
            "dev",
        ),
        (
            "prod-made-1",
            "made_up",
            "قال النبي من شرب القهوة قبل الفجر كتب له أجر حجة",
            "UNDETERMINED",
            "0",
            "viral made-up",
            "dev",
        ),
        (
            "prod-claim-1",
            "weak_fabricated",
            "اطلبوا العلم ولو في الصين",
            "ATTRIBUTED_RULING",
            "0",
            "known seed claim",
            "dev",
        ),
        (
            "prod-trunc-1",
            "tampered_hadith",
            P.truncate_words("إنما الأعمال بالنيات وإنما لكل امرئ ما نوى", 4),
            "CLOSE_WITH_DIFF",
            "1",
            "truncation",
            "dev",
        ),
        (
            "prod-ho-wa-1",
            "forward_spam",
            P.whatsapp_prefix("قل أعوذ برب الفلق"),
            "SUPPORTED",
            "0",
            "holdout WhatsApp prefix",
            "holdout",
        ),
        (
            "prod-ho-lb-1",
            "ocr_noise",
            P.linebreak_join("إنما الأعمال بالنيات"),
            "SUPPORTED",
            "0",
            "holdout OCR linebreak",
            "holdout",
        ),
        (
            "prod-ho-made-1",
            "made_up",
            "ثبت أن النبي حث على متابعة الحسابات المؤثرة",
            "UNDETERMINED",
            "0",
            "holdout made-up",
            "holdout",
        ),
        (
            "prod-ho-claim-1",
            "weak_fabricated",
            "أنا مدينة العلم وعلي بابها",
            "ATTRIBUTED_RULING",
            "0",
            "holdout attributed seed",
            "holdout",
        ),
        (
            "prod-ho-short-1",
            "too_short",
            "الله",
            "UNDETERMINED",
            "0",
            "holdout too short",
            "holdout",
        ),
        (
            "prod-vocab-short-1",
            "vocab_overlap_short",
            "ان تمطر السماء",
            "UNDETERMINED",
            "0",
            "3-word rain/sky overlap with istisqa hadith",
            "dev",
        ),
        (
            "prod-vocab-short-2",
            "vocab_overlap_short",
            "تمطر السماء ماء",
            "UNDETERMINED",
            "0",
            "scattered weather tokens vs long hadith",
            "dev",
        ),
        (
            "prod-scattered-1",
            "scattered_tokens",
            "انزل الله المطر على الناس",
            "UNDETERMINED",
            "0",
            "generic rain wording not a matn quote",
            "dev",
        ),
    ]

    added = 0
    for rid, cat, text, exp, never, notes, force in candidates:
        text = text.strip()
        if not text or text in seen or rid in seen_ids:
            continue
        status = match(conn, text)["status"]
        row_exp = exp
        row_never = never
        if never in {"1", "true", "yes"} and status == "SUPPORTED":
            continue
        if exp == "SUPPORTED" and status == "CLOSE_WITH_DIFF":
            row_exp = "CLOSE_WITH_DIFF"
            row_never = "0"
        elif exp == "SUPPORTED" and status not in {"SUPPORTED", "CLOSE_WITH_DIFF"}:
            continue
        elif exp == "CLOSE_WITH_DIFF" and status == "SUPPORTED":
            row_exp = "SUPPORTED"
            row_never = "0"
        elif exp == "CLOSE_WITH_DIFF" and status == "UNDETERMINED":
            row_exp = "UNDETERMINED"
            row_never = "0"
        elif exp == "ATTRIBUTED_RULING" and status != "ATTRIBUTED_RULING" or exp == "UNDETERMINED" and status == "SUPPORTED":
            continue
        split = _split_for(rid, force=force)
        out.append(
            {
                "id": rid,
                "category": cat,
                "text": text,
                "expected_status": row_exp,
                "never_supported": row_never,
                "notes": notes,
                "split": split,
            }
        )
        seen.add(text)
        seen_ids.add(rid)
        added += 1

    conn.close()
    out.sort(key=lambda r: (r["split"], r["id"]))
    for path, split in ((V1, None), (DEV, "dev"), (HOLDOUT, "holdout")):
        rows = out if split is None else [r for r in out if r["split"] == split]
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)

    print(f"appended {added} production rows; total={len(out)}")
    print(
        f"  dev={sum(1 for r in out if r['split']=='dev')} "
        f"holdout={sum(1 for r in out if r['split']=='holdout')}"
    )


if __name__ == "__main__":
    main()
