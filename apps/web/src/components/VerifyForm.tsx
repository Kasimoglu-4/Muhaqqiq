"use client";

import { useRouter } from "next/navigation";
import { startTransition, useState } from "react";
import { ocrImage, verifyText } from "@/lib/api";
import { t, withLang, type Lang } from "@/lib/i18n";

const MAX_LEN = 2000;

export function VerifyForm({
  initialText = "",
  lang = "ar",
}: {
  initialText?: string;
  lang?: Lang;
}) {
  const router = useRouter();
  const m = t(lang);
  const [text, setText] = useState(initialText);
  const [fileName, setFileName] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const samples = [m.sample1, m.sample2, m.sample3];

  async function onVerify(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!text.trim()) {
      setError(m.errRequired);
      return;
    }
    setBusy(true);
    try {
      const result = await verifyText(text.trim());
      sessionStorage.setItem(
        `muhaqqiq:result:${result.card_id}`,
        JSON.stringify({ result, userText: text.trim() }),
      );
      startTransition(() => {
        router.push(withLang(`/result?id=${result.card_id}`, lang));
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setBusy(false);
    }
  }

  async function onImage(file: File | null) {
    if (!file) return;
    setFileName(file.name);
    setBusy(true);
    setError(null);
    try {
      const ocr = await ocrImage(file);
      const extracted = (ocr.extracted_text || "").trim();
      if (extracted) {
        setText(extracted);
        setMessage(m.ocrReview);
      } else {
        setMessage(ocr.provider === "stub" ? m.ocrStub : m.ocrEmpty);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "OCR error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <form className="verify-card" onSubmit={onVerify}>
      {message ? <p className="meta">{message}</p> : null}
      <label htmlFor="text" className="meta">
        {m.labelText}
      </label>
      <textarea
        id="text"
        name="text"
        maxLength={MAX_LEN}
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={m.placeholder}
        aria-label={m.labelText}
      />
      <div className="verify-toolbar">
        <p className="meta">
          {text.length}/{MAX_LEN}
        </p>
        {text ? (
          <button
            type="button"
            className="secondary verify-clear"
            onClick={() => {
              setText("");
              setMessage(null);
            }}
          >
            {m.clearText}
          </button>
        ) : null}
      </div>

      <p className="meta" style={{ marginTop: "0.85rem", marginBottom: 0 }}>
        {m.samplesLabel}
      </p>
      <div className="sample-row" role="group" aria-label={m.samplesLabel}>
        {samples.map((sample) => (
          <button
            key={sample}
            type="button"
            className="sample-chip"
            onClick={() => setText(sample)}
          >
            {sample}
          </button>
        ))}
      </div>

      <p className="meta file-upload-label" id="image-label">
        {m.labelImage}
      </p>
      <div className="verify-actions">
        <div className="file-upload" style={{ marginTop: 0 }}>
          <input
            id="image"
            name="image"
            type="file"
            accept="image/png,image/jpeg,image/webp,image/gif"
            className="file-upload-input"
            aria-labelledby="image-label"
            disabled={busy}
            onChange={(e) => {
              void onImage(e.target.files?.[0] ?? null);
              e.target.value = "";
            }}
          />
          <label htmlFor="image" className="btn secondary file-upload-btn">
            <span className="material-symbols-outlined" aria-hidden="true">
              image
            </span>
            {m.buttonChooseImage}
          </label>
          <span className="file-upload-name" aria-live="polite">
            {fileName ?? m.noFileSelected}
          </span>
        </div>
        <button type="submit" className="btn-primary" disabled={busy}>
          <span className="material-symbols-outlined" aria-hidden="true">
            search
          </span>
          {busy ? m.buttonBusy : m.buttonVerify}
        </button>
      </div>
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
    </form>
  );
}
