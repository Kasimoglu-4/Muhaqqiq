import type { Metadata } from "next";
import { dirFor, parseLang, t } from "@/lib/i18n";

export const metadata: Metadata = { title: "About" };

type Props = { searchParams: Promise<{ lang?: string }> };

export default async function AboutPage({ searchParams }: Props) {
  const lang = parseLang((await searchParams).lang);
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
