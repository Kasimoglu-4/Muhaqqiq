"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ResultCard } from "@/components/ResultCard";
import { type VerifyResult, fetchCard } from "@/lib/api";
import { parseLang, statusLabel, t, withLang } from "@/lib/i18n";

function CardInner() {
  const pathname = usePathname() || "";
  const params = useSearchParams();
  const fromPath = pathname.match(/^\/c\/([^/]+)/)?.[1];
  const id = fromPath || params.get("id");
  const lang = parseLang(params.get("lang"));
  const m = t(lang);
  const [payload, setPayload] = useState<{
    result: VerifyResult;
    userText?: string | null;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!id) {
      setError(m.idMissing);
      return;
    }
    const cached = sessionStorage.getItem(`muhaqqiq:result:${id}`);
    if (cached) {
      setPayload(JSON.parse(cached));
      return;
    }
    fetchCard(id).then((card) => {
      if (!card) {
        setError(m.cardMissing);
        return;
      }
      setPayload({
        result: {
          card_id: card.id,
          status: card.status,
          status_ar: statusLabel(lang, card.status, card.status_ar),
          matches: card.match_refs || [],
          diff: card.diff || [],
          diff_highlight: card.diff_highlight || [],
          user_diff_highlight: card.user_diff_highlight || [],
          correct_text: card.correct_text,
          matched_span: card.matched_span,
          gradings: card.gradings || [],
          score: card.score,
          card_url: `/c/${card.id}`,
          data_version: card.data_version,
          ai_disclosure: card.ai_disclosure,
          supported_means: card.supported_means,
        },
      });
    });
  }, [id, lang, m.cardMissing, m.idMissing]);

  if (error) {
    return (
      <main dir={lang === "ar" ? "rtl" : "ltr"} lang={lang}>
        <p className="error">{error}</p>
        <div className="back-row">
          <Link className="back-btn" href={withLang("/", lang)}>
            {m.newCheck}
          </Link>
        </div>
      </main>
    );
  }
  if (!payload) {
    return (
      <main dir={lang === "ar" ? "rtl" : "ltr"} lang={lang}>
        <p className="meta">{m.loading}</p>
      </main>
    );
  }

  const wide = payload.result.status === "SUPPORTED";

  return (
    <main
      className={wide ? "result-main-wide" : undefined}
      dir={lang === "ar" ? "rtl" : "ltr"}
      lang={lang}
    >
      <ResultCard result={payload.result} userText={payload.userText} lang={lang} />
    </main>
  );
}

export default function CardPage() {
  return (
    <Suspense fallback={<p className="meta">…</p>}>
      <CardInner />
    </Suspense>
  );
}
