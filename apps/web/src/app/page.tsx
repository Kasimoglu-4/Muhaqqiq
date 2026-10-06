"use client";

import { Suspense, useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { VerifyForm } from "@/components/VerifyForm";
import { dirFor, parseLang, t } from "@/lib/i18n";

function HomeInner() {
  const params = useSearchParams();
  const lang = parseLang(params.get("lang"));
  const m = t(lang);
  const shared = useMemo(
    () => [params.get("text"), params.get("title"), params.get("url")].filter(Boolean).join("\n").trim(),
    [params],
  );

  return (
    <main dir={dirFor(lang)} lang={lang}>
      <section className="hero-block">
        <span className="hero-badge">
          <span className="material-symbols-outlined" aria-hidden="true">
            verified
          </span>
          {m.homeBadge}
        </span>
        <h1>
          <span className="brand">{m.brand}</span>
        </h1>
        <p className="lead">{m.landingTag}</p>
        <p className="lead">{m.homeLead}</p>
      </section>
      <section id="verify">
        <VerifyForm initialText={shared} lang={lang} />
      </section>
      <div className="trust-row">
        <div className="trust-item">
          <span className="material-symbols-outlined" aria-hidden="true">
            menu_book
          </span>
          <span>{m.trustSources}</span>
        </div>
        <div className="trust-item">
          <span className="material-symbols-outlined" aria-hidden="true">
            lock
          </span>
          <span>{m.trustPrivacy}</span>
        </div>
        <div className="trust-item">
          <span className="material-symbols-outlined" aria-hidden="true">
            info
          </span>
          <span>{m.trustNotFatwa}</span>
        </div>
      </div>
      <footer className="site-footer">{m.aiDisclosure}</footer>
    </main>
  );
}

export default function HomePage() {
  return (
    <Suspense fallback={<p className="meta">…</p>}>
      <HomeInner />
    </Suspense>
  );
}
