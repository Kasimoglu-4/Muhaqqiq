import type { Metadata } from "next";
import Link from "next/link";
import { ResultCard } from "@/components/ResultCard";
import { API_URL, fetchCard } from "@/lib/api";
import { dirFor, parseLang, statusLabel, t, withLang } from "@/lib/i18n";

type Props = {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ lang?: string }>;
};

export async function generateMetadata({ params, searchParams }: Props): Promise<Metadata> {
  const { id } = await params;
  const lang = parseLang((await searchParams).lang);
  const card = await fetchCard(id);
  const label = card ? statusLabel(lang, card.status, card.status_ar) : t(lang).brand;
  return {
    title: label,
    openGraph: {
      title: `${t(lang).brand} — ${label}`,
      description: t(lang).landingTag,
      images: [`${API_URL}/c/${id}/og.png`],
    },
  };
}

export default async function CardPage({ params, searchParams }: Props) {
  const { id } = await params;
  const lang = parseLang((await searchParams).lang);
  const m = t(lang);
  const card = await fetchCard(id);
  if (!card) {
    return (
      <main dir={dirFor(lang)} lang={lang}>
        <p className="error">{m.cardMissing}</p>
        <div className="back-row">
          <Link className="back-btn" href={withLang("/", lang)}>
            {m.newCheck}
          </Link>
        </div>
      </main>
    );
  }
  const result = {
    card_id: card.id,
    status: card.status,
    status_ar: statusLabel(lang, card.status, card.status_ar),
    matches: card.match_refs || [],
    diff: card.diff || [],
    diff_highlight: card.diff_highlight || [],
    user_diff_highlight: card.user_diff_highlight || [],
    correct_text: card.correct_text,
    matched_span: card.matched_span ?? null,
    gradings: card.gradings || [],
    score: card.score,
    card_url: `/c/${card.id}`,
    data_version: card.data_version,
    ai_disclosure: m.aiDisclosure,
    supported_means: m.supportedMeans,
  };

  const wide = result.status === "SUPPORTED";

  return (
    <main className={wide ? "result-main-wide" : undefined} dir={dirFor(lang)} lang={lang}>
      <ResultCard result={result} lang={lang} />
    </main>
  );
}
