"use client";

import { forwardRef } from "react";
import type { MatchRef } from "@/lib/api";
import { kindLabel, quotedDisplay, sourceLine } from "@/lib/shareCard";
import { t, type Lang } from "@/lib/i18n";

type Props = {
  statusLabel: string;
  quote: string;
  match: MatchRef;
  proofUrl?: string;
  lang?: Lang;
  /** When false, CTA is visual-only (for PNG export). */
  interactive?: boolean;
};

export const SupportedShareCard = forwardRef<HTMLDivElement, Props>(
  function SupportedShareCard(
    { statusLabel, quote, match, proofUrl = "", lang = "ar", interactive = true },
    ref,
  ) {
    const m = t(lang);
    const fullText = (match.text || quote || "").trim();
    const displayQuote = quotedDisplay(quote || fullText);
    const kind = kindLabel(match.kind, lang);
    const source = sourceLine(match, lang);

    function onViewSource() {
      if (!interactive) return;
      if (proofUrl) {
        window.open(proofUrl, "_blank", "noopener,noreferrer");
      }
    }

    return (
      <div
        ref={ref}
        className="share-card"
        dir={lang === "ar" ? "rtl" : "ltr"}
        lang={lang}
      >
        <div className="share-card-header">
          <span className="share-card-brand">{m.brand}</span>
          <span className="share-card-status">
            {/* Inline SVG: Material Symbols fonts are skipped during PNG export. */}
            <svg
              className="share-card-check"
              viewBox="0 0 24 24"
              width="16"
              height="16"
              aria-hidden="true"
              focusable="false"
            >
              <circle cx="12" cy="12" r="10" fill="currentColor" />
              <path
                d="M10.2 15.6 7.4 12.8l1.2-1.2 1.6 1.6 4.4-4.4 1.2 1.2-5.6 5.6z"
                fill="#ebf7f0"
              />
            </svg>
            {statusLabel}
          </span>
        </div>

        <p className="share-card-quote">{displayQuote}</p>
        <p className="share-card-kind">{kind}</p>
        <p className="share-card-source">{source}</p>

        {interactive ? (
          <button type="button" className="share-card-cta" onClick={onViewSource}>
            {m.viewSourceIsnad}
          </button>
        ) : (
          <span className="share-card-cta">{m.viewSourceIsnad}</span>
        )}
        <p className="share-card-foot">{m.shareCardDisclosure}</p>
      </div>
    );
  },
);
