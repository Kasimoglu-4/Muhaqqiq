import { t, type Lang } from "@/lib/i18n";

/** Format RapidFuzz score (0–100) as a text-match label — not AI confidence. */
export function formatMatchScore(score: number | null | undefined, lang: Lang): string | null {
  if (score == null || Number.isNaN(score)) return null;
  const m = t(lang);
  if (score >= 99) return m.fullMatch;
  const n = Number.isInteger(score) ? String(score) : score.toFixed(1).replace(/\.0$/, "");
  return m.matchPercent.replace("{n}", n);
}

export function statusIcon(status: string): string {
  switch (status) {
    case "SUPPORTED":
      return "check_circle";
    case "CLOSE_WITH_DIFF":
      return "compare";
    case "ATTRIBUTED_RULING":
      return "gavel";
    default:
      return "help";
  }
}
