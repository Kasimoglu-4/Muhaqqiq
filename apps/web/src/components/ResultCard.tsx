"use client";

import Link from "next/link";
import { useRef, useState } from "react";
import type { Grading, VerifyResult } from "@/lib/api";
import { DiffAnalysis } from "@/components/DiffAnalysis";
import { FeedbackBar } from "@/components/FeedbackBar";
import { ShareBar } from "@/components/ShareBar";
import { SupportedShareCard } from "@/components/SupportedShareCard";
import { fillReply, replyKindForStatus } from "@/content/replyTemplates";
import {
  canNativeFileShare,
  downloadDataUrl,
  exportNodeToPng,
} from "@/lib/exportShareCard";
import { formatMatchScore, statusIcon } from "@/lib/matchScore";
import { kindLabel, sourceLine } from "@/lib/shareCard";
import { statusLabel, t, withLang, type Lang } from "@/lib/i18n";

type Props = {
  result: VerifyResult;
  userText?: string | null;
  absoluteCardUrl?: string;
  lang?: Lang;
};

function refLine(match: VerifyResult["matches"][0], m: ReturnType<typeof t>): string {
  if (match.kind === "quran" && match.ref) {
    return `${m.sourceQuran} · ${match.ref.sura}:${match.ref.aya}`;
  }
  if ((match.kind === "hadith" || match.kind === "enc_hadith") && match.ref) {
    return `${m.sourceHadith}: ${match.ref.collection} · ${match.ref.number}`;
  }
  return `${m.knownClaim} (${String(match.ref?.claim_type ?? match.kind)})`;
}

async function copyText(text: string) {
  await navigator.clipboard.writeText(text);
}

export function ResultCard({ result, userText, absoluteCardUrl, lang = "ar" }: Props) {
  const m = t(lang);
  const statusAr = statusLabel(lang, result.status, result.status_ar);
  const match = result.matches?.[0];
  const cardPath = result.card_url || `/c/${result.card_id}`;
  const cardUrl = absoluteCardUrl || cardPath;
  const [copied, setCopied] = useState<string | null>(null);
  const [imageBusy, setImageBusy] = useState(false);
  const [imageMsg, setImageMsg] = useState<string | null>(null);
  const shareCardRef = useRef<HTMLDivElement>(null);

  const gradings: Grading[] =
    result.gradings?.length
      ? result.gradings
      : match?.gradings?.length
        ? match.gradings
        : match?.grading
          ? [match.grading]
          : [];

  const fullSourceText = (match?.text || result.correct_text || match?.correct_text || "").trim();
  const correctText =
    result.matched_span ||
    result.correct_text ||
    match?.correct_text ||
    match?.text ||
    "";
  const showFullSource =
    Boolean(result.matched_span) &&
    Boolean(match?.text) &&
    result.matched_span !== match?.text;
  const proofUrl =
    (match?.proof_url as string | undefined) ||
    (match?.ref?.proof_url as string | undefined) ||
    (gradings[0]?.url as string | undefined) ||
    "";

  const replyKind = replyKindForStatus(result.status);
  const reference = match ? refLine(match, m) : "";
  const scoreLabel = formatMatchScore(result.score, lang);
  const isSupported = result.status === "SUPPORTED" && Boolean(match);
  const isUndetermined = result.status === "UNDETERMINED";
  const showSharePreview = isSupported && Boolean(match);

  async function onCopy(label: string, text: string) {
    await copyText(text);
    setCopied(label);
    setTimeout(() => setCopied(null), 2000);
  }

  async function onShareImage() {
    if (!shareCardRef.current || imageBusy) return;
    setImageBusy(true);
    setImageMsg(m.shareImageBusy);
    const filename = `muhaqqiq-${result.card_id || "card"}.png`;
    try {
      const dataUrl = await exportNodeToPng(shareCardRef.current);
      const absUrl =
        absoluteCardUrl ||
        (typeof window !== "undefined" ? `${window.location.origin}${cardPath}` : cardPath);

      if (canNativeFileShare()) {
        const blob = await (await fetch(dataUrl)).blob();
        const file = new File([blob], filename, { type: "image/png" });
        if (navigator.canShare?.({ files: [file] })) {
          await navigator.share({
            files: [file],
            title: m.brand,
            text: `${statusAr} — ${absUrl}`,
          });
          setImageMsg(null);
          return;
        }
      }

      downloadDataUrl(dataUrl, filename);
      setImageMsg(m.shareImageSaved);
      setTimeout(() => setImageMsg(null), 2500);
    } catch {
      setImageMsg(null);
    } finally {
      setImageBusy(false);
    }
  }

  const breadcrumb = (
    <div className="result-breadcrumb">
      <Link className="back-btn" href={withLang("/", lang)}>
        {m.backToVerify}
      </Link>
      <span className="meta">
        {m.engineVersion}: {result.data_version}
      </span>
    </div>
  );

  if (isUndetermined) {
    return (
      <>
        {breadcrumb}
        <h1 className="headline-result" style={{ fontSize: "1.45rem", marginBottom: "1rem" }}>
          {m.resultTitle}
        </h1>
        <div className="undetermined-panel">
          <div className="undetermined-accent" />
          <div className="undetermined-body">
            <div className="status-top" style={{ borderBottom: "none", paddingBottom: 0, marginBottom: "1rem" }}>
              <span className={`status-pill ${result.status}`}>
                <span className="material-symbols-outlined" aria-hidden="true">
                  {statusIcon(result.status)}
                </span>
                {statusAr}
              </span>
              {result.card_id ? (
                <code className="meta">
                  {m.auditId}: #{result.card_id.slice(0, 8).toUpperCase()}
                </code>
              ) : null}
            </div>

            {userText ? (
              <div className="input-callout">
                <div className="input-callout-label">
                  <span className="material-symbols-outlined" aria-hidden="true">
                    edit_note
                  </span>
                  {m.inputQueryLabel}
                </div>
                <p className="verse" style={{ fontSize: "1.15rem" }}>
                  {userText}
                </p>
              </div>
            ) : null}

            <div className="method-note">
              <span className="material-symbols-outlined" aria-hidden="true">
                info
              </span>
              <p style={{ margin: 0 }}>{m.undeterminedLead}</p>
            </div>

            <ul className="undetermined-steps">
              <li>
                <span className="material-symbols-outlined" aria-hidden="true">
                  search
                </span>
                {m.undeterminedStep1}
              </li>
              <li>
                <span className="material-symbols-outlined" aria-hidden="true">
                  menu_book
                </span>
                {m.undeterminedStep2}
              </li>
              <li>
                <span className="material-symbols-outlined" aria-hidden="true">
                  school
                </span>
                {m.undeterminedStep3}
              </li>
            </ul>

            <div className="verify-actions">
              <Link className="btn" href={withLang("/", lang)}>
                <span className="material-symbols-outlined" aria-hidden="true">
                  add
                </span>
                {m.newCheck}
              </Link>
            </div>

            <div className="integrity-box">{m.undeterminedIntegrity}</div>

            {result.card_id ? (
              <div className="feedback-compact">
                <FeedbackBar cardId={result.card_id} lang={lang} />
              </div>
            ) : null}

            <div className="foot">
              <p>{m.aiDisclosure}</p>
              <p>
                {m.permanentLink}: <a href={cardPath}>{cardPath}</a>
              </p>
            </div>
          </div>
        </div>
      </>
    );
  }

  const analysis = (
    <article className="status-card">
      <div className="status-top">
        <span className={`status-pill ${result.status}`}>
          <span className="material-symbols-outlined" aria-hidden="true">
            {statusIcon(result.status)}
          </span>
          {statusAr}
        </span>
        {scoreLabel ? (
          <div className="score-row">
            <span className="meta" style={{ margin: 0 }}>
              {m.matchScoreLabel}
            </span>
            <span className={`score-chip${result.status === "CLOSE_WITH_DIFF" ? " warn" : ""}`}>
              {scoreLabel}
            </span>
          </div>
        ) : null}
      </div>

      {userText ? (
        <div className="input-callout">
          <div className="input-callout-label">
            <span className="material-symbols-outlined" aria-hidden="true">
              edit_note
            </span>
            {m.inputQueryLabel}
          </div>
          <p style={{ margin: 0, lineHeight: 1.7 }}>{userText}</p>
        </div>
      ) : null}

      {match && result.status !== "ATTRIBUTED_RULING" ? (
        <section>
          <div className="input-callout-label" style={{ marginBottom: "0.35rem" }}>
            <span className="material-symbols-outlined" aria-hidden="true">
              menu_book
            </span>
            {m.canonicalLabel}
          </div>
          <div className="canonical-block">
            <p className="verse">{fullSourceText || correctText}</p>
          </div>
          <div className="ref-block">
            <p style={{ margin: 0, fontWeight: 700 }}>
              {sourceLine(match, lang) || reference}
            </p>
            <p className="meta" style={{ margin: "0.35rem 0 0" }}>
              {kindLabel(match.kind, lang)}
              {gradings[0]?.grade || gradings[0]?.ruling
                ? ` · ${gradings[0].grade || gradings[0].ruling}`
                : ""}
            </p>
            {proofUrl ? (
              <p className="meta" style={{ margin: "0.5rem 0 0" }}>
                <a href={proofUrl} rel="noopener noreferrer" target="_blank">
                  {m.viewSourceIsnad}
                </a>
              </p>
            ) : null}
          </div>
        </section>
      ) : null}

      {result.status === "CLOSE_WITH_DIFF" && showFullSource ? (
        <details className="meta" style={{ marginBottom: "1rem" }}>
          <summary>{m.fullSource}</summary>
          <p className="verse">{match?.text}</p>
        </details>
      ) : null}

      {result.status === "ATTRIBUTED_RULING" && gradings.length ? (
        <section className="rulings">
          <p className="meta">{m.attributedRulings}</p>
          <ul>
            {gradings.map((g, i) => (
              <li key={i}>
                {m.rulingOf} {g.grader}: {g.grade || g.ruling} ({g.reference})
                {g.url ? (
                  <>
                    {" "}
                    ·{" "}
                    <a href={g.url} rel="noopener noreferrer" target="_blank">
                      {m.proofLink}
                    </a>
                  </>
                ) : null}
              </li>
            ))}
          </ul>
          {match?.text ? <p className="verse">{match.text}</p> : null}
          {reference ? <p className="meta">{reference}</p> : null}
          <p className="meta foot-note">{m.rulingsFooter}</p>
        </section>
      ) : null}

      {match?.translations?.length ? (
        <div className="meta translations" style={{ marginBottom: "1rem" }}>
          <p className="meta">{m.meanings}</p>
          {match.translations
            .filter((tr) => tr.lang === "en" || tr.lang === "tr")
            .map((tr) => (
              <p key={tr.lang}>
                <strong>{tr.lang.toUpperCase()}:</strong> {tr.text}
              </p>
            ))}
        </div>
      ) : null}

      <div className="method-note">
        <span className="material-symbols-outlined" aria-hidden="true">
          info
        </span>
        <p style={{ margin: 0 }}>
          <strong>{m.methodNoteTitle}</strong> {m.supportedMeans}
        </p>
      </div>

      <div className="meta-bar">
        {result.card_id ? (
          <span>
            {m.auditId}: <code>#{result.card_id.slice(0, 8).toUpperCase()}</code>
          </span>
        ) : null}
        <span>
          {m.dataVersion}: <strong style={{ color: "var(--ink)", fontWeight: 600 }}>{result.data_version}</strong>
        </span>
      </div>

      <div className="actions-row">
        <div className="share" style={{ marginTop: 0 }}>
          {(fullSourceText || correctText) &&
          (result.status === "SUPPORTED" || result.status === "CLOSE_WITH_DIFF") ? (
            <button
              type="button"
              className="secondary"
              style={{ marginTop: 0 }}
              onClick={() => onCopy("correct", fullSourceText || correctText)}
            >
              {copied === "correct" ? m.copied : m.copyCorrect}
            </button>
          ) : null}
          {replyKind ? (
            <button
              type="button"
              className="secondary"
              style={{ marginTop: 0 }}
              onClick={() =>
                onCopy(
                  "reply",
                  fillReply(
                    replyKind,
                    lang,
                    {
                      correct_text: fullSourceText || correctText,
                      reference,
                      proof_url: proofUrl,
                      card_url: cardUrl,
                      grader: gradings[0]?.grader,
                      grade: gradings[0]?.grade || gradings[0]?.ruling,
                    },
                    "full",
                  ),
                )
              }
            >
              {copied === "reply" ? m.copied : m.copyPoliteReply}
            </button>
          ) : null}
        </div>
        <ShareBar
          cardPath={cardPath}
          absoluteUrl={absoluteCardUrl}
          lang={lang}
          onShareImage={isSupported ? onShareImage : undefined}
          imageBusy={imageBusy}
        />
      </div>
      {imageMsg ? <p className="meta">{imageMsg}</p> : null}

      {result.card_id ? (
        <div className="feedback-compact">
          <FeedbackBar cardId={result.card_id} lang={lang} />
        </div>
      ) : null}

      <div className="foot">
        <p>{m.aiDisclosure}</p>
        <p>
          {m.permanentLink}: <a href={cardPath}>{cardPath}</a>
        </p>
      </div>
    </article>
  );

  return (
    <>
      {breadcrumb}
      <h1 style={{ fontSize: "1.45rem", marginBottom: "1rem" }}>{m.resultTitle}</h1>
      <div className={`result-layout${showSharePreview ? " has-share" : ""}`}>
        <div>
          {analysis}
          <DiffAnalysis
            lang={lang}
            status={result.status}
            userText={userText}
            sourceText={fullSourceText || correctText}
            diffHighlight={result.diff_highlight}
            userDiffHighlight={result.user_diff_highlight}
            diff={result.diff}
          />
        </div>

        {showSharePreview && match ? (
          <aside className="share-card-stage">
            <div className="share-card-stage-label">
              <span>{m.shareCardLabel}</span>
              <span>{m.shareCardSize}</span>
            </div>
            <SupportedShareCard
              statusLabel={statusAr}
              quote={fullSourceText || correctText}
              match={match}
              proofUrl={proofUrl}
              lang={lang}
              interactive
            />
          </aside>
        ) : null}
      </div>

      {/* Off-screen export target (separate instance for PNG) */}
      {isSupported && match ? (
        <div className="share-card-export" aria-hidden="true">
          <SupportedShareCard
            ref={shareCardRef}
            statusLabel={statusAr}
            quote={fullSourceText || correctText}
            match={match}
            proofUrl={proofUrl}
            lang={lang}
            interactive={false}
          />
        </div>
      ) : null}
    </>
  );
}
