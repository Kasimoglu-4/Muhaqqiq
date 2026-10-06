import type { Metadata } from "next";
import Link from "next/link";
import { PRIVACY, type PrivacyLang } from "@/content/privacy";

export const metadata: Metadata = { title: "الخصوصية" };

type Props = { searchParams: Promise<{ lang?: string }> };

export default async function PrivacyPage({ searchParams }: Props) {
  const q = await searchParams;
  const lang = (["ar", "en", "tr"].includes(q.lang || "") ? q.lang : "ar") as PrivacyLang;
  const body = PRIVACY[lang];
  const dir = lang === "ar" ? "rtl" : "ltr";

  return (
    <main dir={dir} lang={lang}>
      <h1>{body.title}</h1>
      <p className="meta">
        <Link href="/privacy?lang=ar" aria-current={lang === "ar" ? "page" : undefined}>
          العربية
        </Link>
        {" · "}
        <Link href="/privacy?lang=en" aria-current={lang === "en" ? "page" : undefined}>
          English
        </Link>
        {" · "}
        <Link href="/privacy?lang=tr" aria-current={lang === "tr" ? "page" : undefined}>
          Türkçe
        </Link>
      </p>
      <div className="card meta" dir={dir} lang={lang}>
        {body.paragraphs.map((p) => (
          <p key={p.slice(0, 24)}>{p}</p>
        ))}
      </div>
    </main>
  );
}
