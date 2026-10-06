import type { MatchRef } from "@/lib/api";
import type { Lang } from "@/lib/i18n";

const QUOTE_MAX = 56;

export function truncateQuote(text: string, max = QUOTE_MAX): string {
  const cleaned = text.replace(/\s+/g, " ").trim();
  if (cleaned.length <= max) return cleaned;
  return `${cleaned.slice(0, max).trimEnd()}…`;
}

export function quotedDisplay(text: string): string {
  const inner = truncateQuote(text);
  if (!inner) return "";
  if (inner.startsWith("«") || inner.startsWith('"') || inner.startsWith("“")) return inner;
  return `«${inner}»`;
}

export function kindLabel(kind: string, lang: Lang): string {
  const k = kind === "enc_hadith" ? "hadith" : kind;
  if (lang === "en") {
    if (k === "quran") return "Quran verse";
    if (k === "hadith") return "Prophetic hadith";
    return "Known claim";
  }
  if (lang === "tr") {
    if (k === "quran") return "Kur'an ayeti";
    if (k === "hadith") return "Peygamber hadisi";
    return "Bilinen iddia";
  }
  if (k === "quran") return "آية قرآنية";
  if (k === "hadith") return "حديث نبوي";
  return "مطالبة معروفة";
}

export function sourceLine(match: MatchRef, lang: Lang): string {
  const ref = match.ref || {};
  if (match.kind === "quran") {
    const sura = ref.sura ?? "";
    const aya = ref.aya ?? "";
    if (lang === "en") return `Quran · ${sura}:${aya}`;
    if (lang === "tr") return `Kur'an · ${sura}:${aya}`;
    return `القرآن، سورة ${sura} آية ${aya}`;
  }
  if (match.kind === "hadith" || match.kind === "enc_hadith") {
    const collection = String(ref.collection ?? ref.source ?? "");
    const number = String(ref.number ?? "");
    if (lang === "en") {
      return number ? `${collection}, hadith ${number}` : collection;
    }
    if (lang === "tr") {
      return number ? `${collection}, hadis ${number}` : collection;
    }
    return number ? `${collection}، الحديث ${number}` : collection;
  }
  const claim = String(ref.claim_type ?? match.kind);
  if (lang === "en") return `Known claim (${claim})`;
  if (lang === "tr") return `Bilinen iddia (${claim})`;
  return `مطالبة معروفة (${claim})`;
}
