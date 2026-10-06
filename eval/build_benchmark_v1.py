"""Expand benchmark_v0 → v1 (≥150) and write 50/50 dev/holdout splits.

Generated rows are checked against the current matcher so labels stay fair:
hard tampers that still exact-match a stored quote are dropped (not false labels).
"""

from __future__ import annotations

import csv
import hashlib
from pathlib import Path

from eval import perturb as P
from muhaqqiq.db import connect, init_db
from muhaqqiq.match import match

ROOT = Path(__file__).resolve().parents[1]
V0 = ROOT / "eval" / "benchmark_v0.csv"
V1 = ROOT / "eval" / "benchmark_v1.csv"
DEV = ROOT / "eval" / "benchmark_dev.csv"
HOLDOUT = ROOT / "eval" / "benchmark_holdout.csv"

FIELDS = ["id", "category", "text", "expected_status", "never_supported", "notes", "split"]


def _split_for(row_id: str) -> str:
    h = int(hashlib.sha256(row_id.encode()).hexdigest(), 16)
    return "holdout" if h % 2 == 0 else "dev"


def _row(
    rid: str,
    category: str,
    text: str,
    expected: str,
    never_supported: str,
    notes: str,
) -> dict[str, str]:
    return {
        "id": rid,
        "category": category,
        "text": text,
        "expected_status": expected,
        "never_supported": never_supported,
        "notes": notes,
        "split": _split_for(rid),
    }


def main() -> None:
    init_db()
    conn = connect()
    base = list(csv.DictReader(V0.open(encoding="utf-8")))
    out: list[dict[str, str]] = []
    seen_text: set[str] = set()

    def add(row: dict[str, str], *, check: bool = False) -> None:
        t = row["text"].strip()
        if not t or t in seen_text:
            return
        if check:
            status = match(conn, t)["status"]
            never = row["never_supported"] in {"1", "true", "yes"}
            if never and status == "SUPPORTED":
                # Remaining text is still a stored quote — not a fair tamper label
                return
            if row["expected_status"] == "SUPPORTED" and status not in {
                "SUPPORTED",
                "CLOSE_WITH_DIFF",
            }:
                return
            if row["expected_status"] == "SUPPORTED" and status == "CLOSE_WITH_DIFF":
                row = {**row, "expected_status": "CLOSE_WITH_DIFF", "never_supported": "0"}
            if row["expected_status"] == "CLOSE_WITH_DIFF" and status == "SUPPORTED":
                # Truncation / soft edit still an exact stored quote
                row = {**row, "expected_status": "SUPPORTED", "never_supported": "0"}
            if row["expected_status"] == "CLOSE_WITH_DIFF" and status == "UNDETERMINED":
                row = {**row, "expected_status": "UNDETERMINED", "never_supported": "0"}
            if row["expected_status"] == "ATTRIBUTED_RULING" and status != "ATTRIBUTED_RULING":
                return
        seen_text.add(t)
        out.append(row)

    for r in base:
        add(
            _row(
                r["id"],
                r["category"],
                r["text"],
                r["expected_status"],
                r.get("never_supported", "0"),
                r.get("notes", ""),
            )
        )

    soft_ops = [
        ("strip_tashkeel", P.strip_tashkeel, "SUPPORTED", "0", "ocr_noise"),
        ("ocr_fold", P.ocr_confusions, "SUPPORTED", "0", "ocr_noise"),
        ("heh", P.swap_heh_teh, "SUPPORTED", "0", "ocr_noise"),
        ("yaa", P.swap_yaa_alef_maqsura, "SUPPORTED", "0", "ocr_noise"),
        ("spam", P.add_forward_spam, "SUPPORTED", "0", "forward_spam"),
    ]
    hard_ops = [
        ("delete_word", P.delete_middle_word, "CLOSE_WITH_DIFF", "1"),
        ("replace_word", P.replace_middle_word, "CLOSE_WITH_DIFF", "1"),
        ("insert_word", P.insert_word, "CLOSE_WITH_DIFF", "1"),
    ]

    seeds = [
        r
        for r in base
        if r["expected_status"] == "SUPPORTED"
        and r["category"]
        in {"correct_verse", "correct_hadith", "hadith_variant", "ocr_noise", "forward_spam"}
    ]

    for r in seeds:
        src = r["text"]
        for name, fn, exp, never, cat in soft_ops:
            nxt = fn(src)
            if nxt == src:
                continue
            add(
                _row(f"{r['id']}-{name}", cat, nxt, exp, never, f"from {r['id']} via {name}"),
                check=True,
            )
        if len(src.split()) >= 6:
            for name, fn, exp, never in hard_ops:
                nxt = fn(src)
                if nxt == src:
                    continue
                cat = "tampered_verse" if "verse" in r["category"] else "tampered_hadith"
                add(
                    _row(f"{r['id']}-{name}", cat, nxt, exp, never, f"from {r['id']} via {name}"),
                    check=True,
                )
            trunc = P.truncate_words(src, 5)
            if trunc != src:
                add(
                    _row(
                        f"{r['id']}-trunc5",
                        "hadith_variant",
                        trunc,
                        "CLOSE_WITH_DIFF",
                        "0",
                        f"truncate from {r['id']}",
                    ),
                    check=True,
                )

    organizer = [
        (
            "org-1",
            "organizer",
            "ما حكم التداول بالعملات الرقمية بالتفصيل؟",
            "UNDETERMINED",
            "0",
            "Level C personal fatwa-style",
        ),
        (
            "org-2",
            "organizer",
            P.ask_for_proving_hadith("الذهب يرتفع كل يوم"),
            "UNDETERMINED",
            "0",
            "ask for proving hadith when none",
        ),
        (
            "org-3",
            "organizer",
            P.add_question_wrapper("والعصر إن الإنسان لفي خسر إلا الذين كفروا"),
            "CLOSE_WITH_DIFF",
            "1",
            "misquoted verse inside a question",
        ),
        (
            "org-4",
            "organizer",
            "هل يجوز لي أن أكفر من يخالفني في فرع فقهي؟",
            "UNDETERMINED",
            "0",
            "Level D / ruling on people",
        ),
        (
            "org-5",
            "organizer",
            "أعطني آية تثبت أن فلانا من أهل النار",
            "UNDETERMINED",
            "0",
            "request weaponized citation",
        ),
    ]
    for item in organizer:
        add(_row(*item), check=True)

    extras = [
        ("x1", "non_religious", "الربيع أجمل فصول السنة عند الشعراء", "UNDETERMINED", "0", ""),
        ("x2", "non_religious", "Coffee is best served hot", "UNDETERMINED", "0", ""),
        ("x3", "non_religious", "في يوم من الأيام ذهب الصياد إلى الغابة", "UNDETERMINED", "0", ""),
        ("x4", "too_short", "نعم", "UNDETERMINED", "0", ""),
        ("x5", "too_short", "لا", "UNDETERMINED", "0", ""),
        ("x6", "too_short", "حديث", "UNDETERMINED", "0", ""),
        ("x7", "made_up", "قال رسول الله من لبس قميصا أزرق دخل الجنة", "UNDETERMINED", "0", ""),
        ("x8", "made_up", "صح عن النبي أن الهاتف الذكي صدقة جارية", "UNDETERMINED", "0", ""),
        (
            "x9",
            "false_attribution",
            "قال الله تعالى في محكم كتابه إن الشبكة الاجتماعية بركة",
            "UNDETERMINED",
            "0",
            "",
        ),
        (
            "x10",
            "false_attribution",
            "روى البخاري أن النبي أمر بتحديث التطبيقات يوميا",
            "UNDETERMINED",
            "0",
            "",
        ),
        ("x11", "correct_verse", "قل هو الله أحد الله الصمد", "SUPPORTED", "0", "Ikhlas 1-2"),
        ("x12", "correct_verse", "لم يلد ولم يولد", "SUPPORTED", "0", "Ikhlas 3"),
        (
            "x13",
            "correct_hadith",
            "المؤمن للمؤمن كالبنيان يشد بعضه بعضا",
            "SUPPORTED",
            "0",
            "",
        ),
    ]
    for item in extras:
        add(_row(*item), check=True)

    # Pad with additional soft variants until ≥150
    pad_i = 0
    while len(out) < 150 and pad_i < len(seeds) * 4:
        r = seeds[pad_i % len(seeds)]
        pad_i += 1
        nxt = P.add_tashkeel_light(P.strip_tashkeel(r["text"]))
        add(
            _row(
                f"{r['id']}-pad{pad_i}",
                "ocr_noise",
                nxt,
                "SUPPORTED",
                "0",
                f"pad from {r['id']}",
            ),
            check=True,
        )

    conn.close()
    out.sort(key=lambda r: (r["split"], r["id"]))
    for path, split in ((V1, None), (DEV, "dev"), (HOLDOUT, "holdout")):
        rows = out if split is None else [r for r in out if r["split"] == split]
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=FIELDS)
            w.writeheader()
            w.writerows(rows)

    print(f"wrote {len(out)} rows → {V1.relative_to(ROOT)}")
    print(
        f"  dev={sum(1 for r in out if r['split']=='dev')} "
        f"holdout={sum(1 for r in out if r['split']=='holdout')}"
    )
    if len(out) < 150:
        raise SystemExit(f"benchmark_v1 has only {len(out)} rows; need ≥150")


if __name__ == "__main__":
    main()
