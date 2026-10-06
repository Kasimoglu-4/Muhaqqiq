import type { Metadata } from "next";
import { fetchSources } from "@/lib/api";
import staticSources from "@/generated/sources.json";
import { dirFor, parseLang, t } from "@/lib/i18n";

export const metadata: Metadata = { title: "Sources" };

type Props = { searchParams: Promise<{ lang?: string }> };

type StaticSource = (typeof staticSources.sources)[number];

function cleanInline(text: string): string {
  return text.replace(/`([^`]+)`/g, "$1").replace(/\*\*([^*]+)\*\*/g, "$1");
}

function LicenseText({ text }: { text: string }) {
  const parts = text.split(/(\[[^\]]+\]\([^)]+\))/g);
  return (
    <>
      {parts.map((part, i) => {
        const m = part.match(/^\[([^\]]+)\]\(([^)]+)\)$/);
        if (m) {
          return (
            <a key={i} href={m[2]} target="_blank" rel="noopener noreferrer">
              {m[1]}
            </a>
          );
        }
        return <span key={i}>{cleanInline(part)}</span>;
      })}
    </>
  );
}

function SourceName({ name, url }: { name: string; url?: string | null }) {
  if (url) {
    return (
      <a
        className="source-name source-link"
        href={url}
        target="_blank"
        rel="noopener noreferrer"
      >
        {name}
      </a>
    );
  }
  return <div className="source-name">{name}</div>;
}

export default async function SourcesPage({ searchParams }: Props) {
  const lang = parseLang((await searchParams).lang);
  const m = t(lang);
  let apiVersion: string | undefined;
  try {
    const data = await fetchSources();
    apiVersion = data.data_version;
  } catch {
    /* optional */
  }

  const usedSources = staticSources.sources.filter(
    (s: StaticSource) => s.status === "used",
  );

  return (
    <main dir={dirFor(lang)} lang={lang}>
      <h1>{m.sourcesTitle}</h1>
      <p className="lead">
        {m.sourcesLeadApi}: {apiVersion || "—"}
      </p>

      <div className="card">
        <p className="meta sources-section-title">{m.sourcesLicenses}</p>
        <ul className="source-list">
          {usedSources.map((s) => (
            <li key={s.name} className="source-item">
              <SourceName name={s.name} url={s.url} />
              <div className="source-use">{s.use}</div>
              <div className="source-license">
                <LicenseText text={s.license} />
              </div>
              <div className="source-meta">
                {cleanInline(s.attribution)}
                {s.version ? ` · ${cleanInline(s.version)}` : ""}
              </div>
            </li>
          ))}
        </ul>
      </div>
    </main>
  );
}
