"use client";

import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { LANGS, dirFor, parseLang, t, withLang, type Lang } from "@/lib/i18n";

function NavInner() {
  const pathname = usePathname() || "/";
  const params = useSearchParams();
  const lang = parseLang(params.get("lang"));
  const m = t(lang);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    document.documentElement.lang = lang;
    document.documentElement.dir = dirFor(lang);
  }, [lang]);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  const links = [
    { href: "/", label: m.navVerify },
    { href: "/how-it-works", label: m.navHow },
    { href: "/sources", label: m.navSources },
    { href: "/about", label: m.navAbout },
    { href: "/privacy", label: m.navPrivacy },
  ];

  function langHref(next: Lang) {
    const q = new URLSearchParams(params.toString());
    if (next === "ar") q.delete("lang");
    else q.set("lang", next);
    const qs = q.toString();
    return qs ? `${pathname}?${qs}` : pathname;
  }

  return (
    <header className="site-header">
      <nav className={`nav${open ? " is-open" : ""}`} aria-label={m.navAria}>
        <div className="nav-start">
          <button
            type="button"
            className="nav-toggle"
            aria-expanded={open}
            aria-controls="nav-links"
            onClick={() => setOpen((v) => !v)}
          >
            <span className="material-symbols-outlined" aria-hidden="true">
              {open ? "close" : "menu"}
            </span>
          </button>
          <Link href={withLang("/", lang)} className="nav-brand">
            <span className="nav-brand-icon" aria-hidden="true">
              <span className="material-symbols-outlined">auto_stories</span>
            </span>
            <span className="brand-link">{m.brand}</span>
          </Link>
          <div id="nav-links" className="nav-links">
            {links.map((l) => (
              <Link
                key={l.href}
                href={withLang(l.href, lang)}
                aria-current={pathname === l.href ? "page" : undefined}
              >
                {l.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="nav-end">
          <div className="nav-langs" role="navigation" aria-label="Language">
            {LANGS.map((l, i) => (
              <span key={l} className="nav-lang-item">
                {i > 0 ? <span className="nav-lang-sep" aria-hidden="true">|</span> : null}
                <Link href={langHref(l)} aria-current={lang === l ? "page" : undefined}>
                  {l.toUpperCase()}
                </Link>
              </span>
            ))}
          </div>
        </div>
      </nav>
    </header>
  );
}

export function Nav() {
  return (
    <Suspense fallback={<header className="site-header"><nav className="nav" /></header>}>
      <NavInner />
    </Suspense>
  );
}
