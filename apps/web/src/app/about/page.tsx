"use client";

import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { dirFor, parseLang, t } from "@/lib/i18n";

function AboutInner() {
  const lang = parseLang(useSearchParams().get("lang"));
  const m = t(lang);

  return (
    <main dir={dirFor(lang)} lang={lang}>
      <h1>{m.aboutTitle}</h1>
      <p className="lead">{m.aboutLead}</p>
      <div className="card meta">
        <p>{m.aboutP1}</p>
        <p>{m.aboutP2}</p>
        <p>{m.aboutP3}</p>
        <p>{m.aboutP4}</p>
        <p>{m.aboutP5}</p>
      </div>
    </main>
  );
}

export default function AboutPage() {
  return (
    <Suspense fallback={<p className="meta">…</p>}>
      <AboutInner />
    </Suspense>
  );
}
