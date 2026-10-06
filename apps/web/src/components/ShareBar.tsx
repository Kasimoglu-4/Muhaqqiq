"use client";

import { useEffect, useState } from "react";
import { canNativeFileShare } from "@/lib/exportShareCard";
import { t, type Lang } from "@/lib/i18n";

type Props = {
  cardPath: string;
  absoluteUrl?: string;
  lang?: Lang;
  onShareImage?: () => void | Promise<void>;
  imageBusy?: boolean;
};

export function ShareBar({
  cardPath,
  absoluteUrl,
  lang = "ar",
  onShareImage,
  imageBusy = false,
}: Props) {
  const m = t(lang);
  const [copied, setCopied] = useState(false);
  const [preferDownload, setPreferDownload] = useState(true);
  const url =
    absoluteUrl ||
    (typeof window !== "undefined" ? `${window.location.origin}${cardPath}` : cardPath);
  const text = encodeURIComponent(m.brand);
  const enc = encodeURIComponent(url);

  useEffect(() => {
    setPreferDownload(!canNativeFileShare());
  }, []);

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  async function nativeShare() {
    if (navigator.share) {
      await navigator.share({ title: m.brand, text: m.landingTag, url });
    }
  }

  return (
    <div className="share" aria-label="share" style={{ marginTop: 0 }}>
      <button type="button" className="secondary" style={{ marginTop: 0 }} onClick={copy}>
        <span className="material-symbols-outlined" aria-hidden="true">
          link
        </span>
        {copied ? m.shareCopied : m.shareCopy}
      </button>
      <button type="button" className="secondary" style={{ marginTop: 0 }} onClick={nativeShare}>
        {m.shareNative}
      </button>
      {onShareImage ? (
        <button
          type="button"
          className="secondary"
          style={{ marginTop: 0 }}
          onClick={() => void onShareImage()}
          disabled={imageBusy}
        >
          {imageBusy
            ? m.shareImageBusy
            : preferDownload
              ? m.shareImageDownload
              : m.shareImage}
        </button>
      ) : null}
      <a
        className="btn secondary"
        style={{ marginTop: 0 }}
        href={`https://wa.me/?text=${text}%20${enc}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        {m.shareWa}
      </a>
      <a
        className="btn secondary"
        style={{ marginTop: 0 }}
        href={`https://t.me/share/url?url=${enc}&text=${text}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        {m.shareTg}
      </a>
      <a
        className="btn secondary"
        style={{ marginTop: 0 }}
        href={`https://twitter.com/intent/tweet?url=${enc}&text=${text}`}
        target="_blank"
        rel="noopener noreferrer"
      >
        {m.shareX}
      </a>
    </div>
  );
}
