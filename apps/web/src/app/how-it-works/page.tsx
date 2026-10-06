import type { Metadata } from "next";
import Link from "next/link";
import { dirFor, parseLang, statusLabel, t, withLang, type Lang } from "@/lib/i18n";

export const metadata: Metadata = { title: "How it works" };

type Props = { searchParams: Promise<{ lang?: string }> };

const STATUS_KEYS = ["SUPPORTED", "CLOSE_WITH_DIFF", "ATTRIBUTED_RULING", "UNDETERMINED"] as const;

function limits(lang: Lang): string[] {
  if (lang === "en") {
    return [
      "References and grades come only from stored data — never from a language model.",
      "“Supported” means the wording was found in a source, not that a surrounding claim is true.",
      "Personal fatwas, rulings on people/groups, and disputed issues are out of scope (Levels C/D).",
      "OCR text is shown for editing before verification; do not trust raw OCR blindly.",
      "AI-assisted tool, not a fatwa authority.",
    ];
  }
  if (lang === "tr") {
    return [
      "Referanslar ve dereceler yalnızca kayıtlı veriden gelir — dil modelinden üretilmez.",
      "“Destekleniyor”, metnin kaynakta bulunduğu anlamına gelir; çevresindeki iddianın doğruluğu değildir.",
      "Kişisel fetvalar, kişi/grup hükümleri ve ihtilaflı konular kapsam dışıdır (C/D düzeyleri).",
      "OCR metni doğrulamadan önce düzenlenebilir; ham OCR'a körü körüne güvenmeyin.",
      "Yapay zekâ destekli araçtır; fetva makamı değildir.",
    ];
  }
  return [
    "المراجع والأحكام تأتي فقط من بيانات مخزّنة — لا من نموذج لغوي.",
    "«مؤيَّد بمصدر» يعني وجود النص في المصدر، لا صحة الادعاء المحيط.",
    "الفتاوى الشخصية وأحكام الأشخاص/الجماعات والمسائل الخلافية خارج النطاق (المستويان ج/د).",
    "يُعرض نص OCR للتعديل قبل التحقق؛ لا تعتمد عليه بلا مراجعة.",
    "أداة مساعدة بالذكاء الاصطناعي وليست جهة فتوى.",
  ];
}

export default async function HowItWorksPage({ searchParams }: Props) {
  const lang = parseLang((await searchParams).lang);
  const m = t(lang);

  return (
    <main dir={dirFor(lang)} lang={lang}>
      <h1>{m.howTitle}</h1>
      <p className="lead">{m.howLead}</p>

      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <p className="meta" style={{ fontWeight: 700 }}>
          {m.howStatuses}
        </p>
        <ul className="meta">
          {STATUS_KEYS.map((k) => (
            <li key={k}>
              <strong>{statusLabel(lang, k)}</strong> <code>{k}</code>
            </li>
          ))}
        </ul>
      </div>

      <div className="card" style={{ marginBottom: "1.25rem" }}>
        <p className="meta" style={{ fontWeight: 700 }}>
          {m.howLimits}
        </p>
        <ul className="meta">
          {limits(lang).map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
      </div>

      <div className="card">
        <p className="meta" style={{ fontWeight: 700 }}>
          {m.howEval}
        </p>
        <p className="meta">
          {lang === "en"
            ? "Held-out false-support target is 0. See the public evaluation report in the repository."
            : lang === "tr"
              ? "Ayrılmış testte yanlış-destek hedefi 0'dır. Genel değerlendirme raporuna bakın."
              : "هدف الدعم الخاطئ على المجموعة المحجوزة هو صفر. انظر تقرير التقييم في المستودع."}
        </p>
        <p className="meta">
          <Link href={withLang("/", lang)}>{m.homeCtaVerify}</Link>
        </p>
      </div>
    </main>
  );
}
