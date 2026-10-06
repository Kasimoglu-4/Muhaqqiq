"""Run benchmark (v0 or v1 splits) and write a markdown report."""

from __future__ import annotations

import argparse
import csv
import time
from collections import Counter
from pathlib import Path

from eval.baseline_search import baseline_match
from muhaqqiq.db import ROOT, connect, init_db
from muhaqqiq.match import match

DEFAULT_BENCH = ROOT / "eval" / "benchmark_v0.csv"


def _load(path: Path, split: str | None) -> list[dict[str, str]]:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    if split and split != "all":
        if "split" in (rows[0] if rows else {}):
            rows = [r for r in rows if r.get("split") == split]
        elif path.name == "benchmark_dev.csv" and split != "dev" or path.name == "benchmark_holdout.csv" and split != "holdout":
            rows = []
    return rows


def run(path: Path, *, split: str | None = None) -> dict:
    init_db()
    conn = connect()
    rows = _load(path, split)
    correct = 0
    false_support = 0
    abstain_ok = 0
    abstain_total = 0
    over_abstain = 0
    should_match_total = 0
    latencies: list[float] = []
    baseline_correct = 0
    by_cat: Counter[str] = Counter()
    by_cat_ok: Counter[str] = Counter()
    failures: list[str] = []

    for row in rows:
        text = row["text"]
        expected = row["expected_status"].strip()
        category = row.get("category") or "other"
        by_cat[category] += 1
        should_not_support = row.get("never_supported", "").strip() in {"1", "true", "yes"}

        t0 = time.perf_counter()
        result = match(conn, text)
        latencies.append((time.perf_counter() - t0) * 1000)
        status = result["status"]

        if status == expected:
            correct += 1
            by_cat_ok[category] += 1
        else:
            failures.append(f"{row.get('id')}: got {status} expected {expected} ({category})")

        if should_not_support and status == "SUPPORTED":
            false_support += 1

        if expected == "UNDETERMINED":
            abstain_total += 1
            if status == "UNDETERMINED":
                abstain_ok += 1

        # Over-abstention: expected a match status but system abstained
        if expected in {"SUPPORTED", "CLOSE_WITH_DIFF", "ATTRIBUTED_RULING"}:
            should_match_total += 1
            if status == "UNDETERMINED":
                over_abstain += 1

        b = baseline_match(conn, text)
        if expected == "CLOSE_WITH_DIFF" and b in {"SUPPORTED", "CLOSE_WITH_DIFF"} or b == expected:
            baseline_correct += 1

    n = len(rows)
    latencies.sort()
    p50 = latencies[n // 2] if latencies else 0.0
    p95 = latencies[max(0, int(n * 0.95) - 1)] if latencies else 0.0
    conn.close()
    return {
        "n": n,
        "correct": correct,
        "false_support": false_support,
        "abstain_ok": abstain_ok,
        "abstain_total": abstain_total,
        "over_abstain": over_abstain,
        "should_match_total": should_match_total,
        "p50": p50,
        "p95": p95,
        "baseline_correct": baseline_correct,
        "by_cat": by_cat,
        "by_cat_ok": by_cat_ok,
        "failures": failures,
        "path": path,
        "split": split or "all",
    }


def render(stats: dict, title: str) -> str:
    n = stats["n"] or 1
    lines = [
        f"# {title}",
        "",
        f"Benchmark: `{stats['path'].name}` split=`{stats['split']}` ({stats['n']} items)",
        "",
        "| Metric | Value |",
        "| --- | --- |",
        f"| Accuracy | {stats['correct']}/{stats['n']} ({100 * stats['correct'] / n:.1f}%) |",
        f"| False-support count | {stats['false_support']} |",
        f"| Abstention correctness | {stats['abstain_ok']}/{stats['abstain_total']} |",
        f"| Over-abstention | {stats['over_abstain']}/{stats['should_match_total']} |",
        f"| Latency p50 (ms) | {stats['p50']:.1f} |",
        f"| Latency p95 (ms) | {stats['p95']:.1f} |",
        (
            f"| Baseline accuracy (approx) | {stats['baseline_correct']}/{stats['n']} "
            f"({100 * stats['baseline_correct'] / n:.1f}%) |"
        ),
        "",
        "## By category",
        "",
        "| Category | Correct | Total |",
        "| --- | --- | --- |",
    ]
    for cat in sorted(stats["by_cat"]):
        lines.append(f"| {cat} | {stats['by_cat_ok'][cat]} | {stats['by_cat'][cat]} |")
    lines.append("")
    if stats["failures"][:20]:
        lines.append("## Sample mismatches (first 20)")
        lines.append("")
        for f in stats["failures"][:20]:
            lines.append(f"- {f}")
        lines.append("")
    lines.append("Thresholds: see `muhaqqiq.decide`. Holdout numbers must not be used for tuning.")
    return "\n".join(lines) + "\n"


def write_heldout_json(stats: dict) -> None:
    import json
    from datetime import UTC, datetime

    from muhaqqiq import DATA_VERSION

    n = stats["n"] or 1
    accuracy = stats["correct"] / n
    baseline_accuracy = stats["baseline_correct"] / n
    payload = {
        "source": stats["path"].name,
        "split": stats["split"],
        "n": stats["n"],
        "correct": stats["correct"],
        "accuracy": accuracy,
        "accuracy_pct": round(100 * accuracy, 1),
        "false_support": stats["false_support"],
        "abstain_ok": stats["abstain_ok"],
        "abstain_total": stats["abstain_total"],
        "over_abstain": stats["over_abstain"],
        "should_match_total": stats["should_match_total"],
        "p50_ms": round(stats["p50"], 1),
        "p95_ms": round(stats["p95"], 1),
        "baseline_correct": stats["baseline_correct"],
        "baseline_accuracy": baseline_accuracy,
        "baseline_accuracy_pct": round(100 * baseline_accuracy, 1),
        "improvement_vs_baseline": (
            round(accuracy / baseline_accuracy, 2) if baseline_accuracy > 0 else None
        ),
        "by_category": {
            cat: {
                "correct": stats["by_cat_ok"][cat],
                "total": stats["by_cat"][cat],
            }
            for cat in sorted(stats["by_cat"])
        },
        "data_version": DATA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "reproducible_via": (
            "make eval-holdout  OR  "
            "uv run python -m eval.run_eval --bench eval/benchmark_v1.csv --split holdout"
        ),
        "technical_seal": None,
    }
    if stats["false_support"] == 0 and stats["n"] > 0:
        payload["technical_seal"] = {
            "data_version": DATA_VERSION,
            "false_support": 0,
            "accuracy": accuracy,
            "accuracy_pct": payload["accuracy_pct"],
            "holdout_n": stats["n"],
            "generated_at": payload["generated_at"],
        }
    out = ROOT / "apps" / "web" / "src" / "generated" / "eval_heldout.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote technical seal JSON → {out.relative_to(ROOT)}")


def _suite_snapshot(stats: dict) -> dict:
    n = stats["n"] or 1
    accuracy = stats["correct"] / n
    baseline_accuracy = stats["baseline_correct"] / n
    return {
        "source": stats["path"].name,
        "split": stats["split"],
        "n": stats["n"],
        "correct": stats["correct"],
        "accuracy": accuracy,
        "accuracy_pct": round(100 * accuracy, 1),
        "false_support": stats["false_support"],
        "abstain_ok": stats["abstain_ok"],
        "abstain_total": stats["abstain_total"],
        "over_abstain": stats["over_abstain"],
        "should_match_total": stats["should_match_total"],
        "p50_ms": round(stats["p50"], 1),
        "p95_ms": round(stats["p95"], 1),
        "baseline_correct": stats["baseline_correct"],
        "baseline_accuracy_pct": round(100 * baseline_accuracy, 1),
        "improvement_vs_baseline": (
            round(accuracy / baseline_accuracy, 2) if baseline_accuracy > 0 else None
        ),
        "by_category": {
            cat: {
                "correct": stats["by_cat_ok"][cat],
                "total": stats["by_cat"][cat],
            }
            for cat in sorted(stats["by_cat"])
        },
    }


def write_metrics_json(stats: dict) -> Path:
    """Merge this run into docs/eval_metrics.json (public pitch / report source)."""
    import json
    from datetime import UTC, datetime

    from muhaqqiq import DATA_VERSION

    path = ROOT / "docs" / "eval_metrics.json"
    if path.exists():
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            doc = {}
    else:
        doc = {}

    snapshot = _suite_snapshot(stats)
    key = "holdout" if stats["split"] == "holdout" else (
        "phase0" if stats["path"].name == "benchmark_v0.csv" else "v1_all"
    )
    suites = doc.get("suites") if isinstance(doc.get("suites"), dict) else {}
    suites[key] = snapshot

    primary = suites.get("holdout") or snapshot
    doc = {
        "schema_version": 1,
        "primary_claim": "holdout",
        "data_version": DATA_VERSION,
        "generated_at": datetime.now(UTC).isoformat(),
        "notes": [
            "Offline labeled CSV benchmark — not live request logs.",
            "Primary public claim is holdout (not used for threshold tuning).",
            "OCR CER on real screenshots is not measured yet.",
            "Latency depends on the machine that ran the eval.",
        ],
        "main_metrics": {
            "false_support": primary["false_support"],
            "accuracy_pct": primary["accuracy_pct"],
            "correct": primary["correct"],
            "n": primary["n"],
            "baseline_accuracy_pct": primary["baseline_accuracy_pct"],
            "improvement_vs_baseline": primary["improvement_vs_baseline"],
            "abstention_correctness": (
                f"{primary['abstain_ok']}/{primary['abstain_total']}"
            ),
            "over_abstention": (
                f"{primary['over_abstain']}/{primary['should_match_total']}"
            ),
            "p50_ms": primary["p50_ms"],
            "p95_ms": primary["p95_ms"],
        },
        "suites": suites,
        "reproduce": {
            "phase0": "make eval",
            "holdout": "make eval-holdout",
            "v1_all": (
                "uv run python -m eval.run_eval --bench eval/benchmark_v1.csv "
                "--split all --out docs/eval_v1_results.md --title \"Benchmark v1 (all)\""
            ),
        },
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote metrics JSON → {path.relative_to(ROOT)}")
    return path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bench",
        type=Path,
        default=DEFAULT_BENCH,
        help="CSV path (default: benchmark_v0.csv for CI compatibility)",
    )
    parser.add_argument("--split", choices=["all", "dev", "holdout"], default="all")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--title", default=None)
    args = parser.parse_args()

    stats = run(args.bench, split=None if args.split == "all" else args.split)
    title = args.title or (
        "Held-out eval results" if args.split == "holdout" else "Eval results"
    )
    report = render(stats, title)
    out = args.out
    if out is None:
        if args.split == "holdout":
            out = ROOT / "docs" / "eval_heldout_results.md"
        elif args.bench.name == "benchmark_v0.csv":
            out = ROOT / "docs" / "phase0_results.md"
            # keep Phase 0 title for CI assert
            report = render(stats, "Phase 0 eval results")
        else:
            out = ROOT / "docs" / "eval_results.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(report, encoding="utf-8")
    print(report)
    write_metrics_json(stats)
    if args.split == "holdout":
        write_heldout_json(stats)
    if stats["false_support"] > 0:
        raise SystemExit(f"false-support={stats['false_support']} (must be 0)")


if __name__ == "__main__":
    main()
