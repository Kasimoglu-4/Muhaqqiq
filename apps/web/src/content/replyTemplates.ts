/** Fixed polite-reply templates — never LLM-generated. Placeholders from stored fields only. */

export type ReplyKind = "close" | "attributed" | "supported_copy";
export type ReplyLang = "ar" | "en" | "tr";

export const REPLY_TEMPLATES: Record<
  ReplyKind,
  Record<ReplyLang, { full: string; short: string }>
> = {
  close: {
    ar: {
      full: "جزاك الله خيراً، وجدتُ أن النص في المصدر هكذا: «{correct_text}» ({reference}). للتفاصيل: {card_url}",
      short: "جزاك الله خيراً، النص الصحيح: «{correct_text}» ({reference})",
    },
    en: {
      full: "Jazakallahu khayran — the source text is: «{correct_text}» ({reference}). Details: {card_url}",
      short: "The correct text is: «{correct_text}» ({reference})",
    },
    tr: {
      full: "Allah razı olsun — kaynak metin şöyle: «{correct_text}» ({reference}). Ayrıntılar: {card_url}",
      short: "Doğru metin: «{correct_text}» ({reference})",
    },
  },
  attributed: {
    ar: {
      full: "جزاك الله خيراً، هذا اللفظ يُنسب بحكم مخزّن: حكم {grader}: {grade} ({reference}). البطاقة: {card_url}",
      short: "حكم {grader}: {grade} ({reference}) — {card_url}",
    },
    en: {
      full: "Jazakallahu khayran — a stored ruling attributes this wording: Ruling of {grader}: {grade} ({reference}). Card: {card_url}",
      short: "Ruling of {grader}: {grade} ({reference})",
    },
    tr: {
      full: "Allah razı olsun — kayıtlı hüküm: {grader} hükmü: {grade} ({reference}). Kart: {card_url}",
      short: "{grader} hükmü: {grade} ({reference})",
    },
  },
  supported_copy: {
    ar: {
      full: "النص في المصدر: «{correct_text}» ({reference}). {proof_url}",
      short: "«{correct_text}» ({reference})",
    },
    en: {
      full: "Source text: «{correct_text}» ({reference}). {proof_url}",
      short: "«{correct_text}» ({reference})",
    },
    tr: {
      full: "Kaynak metin: «{correct_text}» ({reference}). {proof_url}",
      short: "«{correct_text}» ({reference})",
    },
  },
};

export function fillReply(
  kind: ReplyKind,
  lang: ReplyLang,
  fields: Record<string, string | undefined | null>,
  variant: "full" | "short" = "full",
): string {
  const tpl = REPLY_TEMPLATES[kind][lang][variant];
  return tpl.replace(/\{(\w+)\}/g, (_, key: string) => fields[key] ?? "");
}

export function replyKindForStatus(status: string): ReplyKind | null {
  if (status === "CLOSE_WITH_DIFF") return "close";
  if (status === "ATTRIBUTED_RULING") return "attributed";
  if (status === "SUPPORTED") return "supported_copy";
  return null;
}
