"use client";

import { useState } from "react";
import { submitFeedback } from "@/lib/api";
import { t, type Lang } from "@/lib/i18n";

type Props = { cardId: string; lang?: Lang };

export function FeedbackBar({ cardId, lang = "ar" }: Props) {
  const m = t(lang);
  const [done, setDone] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reporting, setReporting] = useState(false);

  async function send(kind: "useful" | "wrong") {
    setBusy(true);
    setError(null);
    try {
      await submitFeedback({
        card_id: cardId,
        kind,
        comment: kind === "wrong" ? comment : "",
      });
      setDone(kind === "useful" ? m.feedbackThanks : m.feedbackReported);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Error");
    } finally {
      setBusy(false);
    }
  }

  if (done) {
    return <p className="meta">{done}</p>;
  }

  return (
    <div aria-label="feedback">
      <p className="meta" style={{ marginTop: 0 }}>
        {m.feedbackUsefulQ}
      </p>
      <div className="share" style={{ marginTop: "0.5rem" }}>
        <button
          type="button"
          className="secondary"
          disabled={busy}
          onClick={() => send("useful")}
          style={{ marginTop: 0 }}
        >
          <span className="material-symbols-outlined" aria-hidden="true">
            thumb_up
          </span>
          {m.feedbackUseful}
        </button>
        <button
          type="button"
          className="secondary"
          disabled={busy}
          onClick={() => {
            if (!reporting) {
              setReporting(true);
              return;
            }
            void send("wrong");
          }}
          style={{ marginTop: 0 }}
        >
          <span className="material-symbols-outlined" aria-hidden="true">
            flag
          </span>
          {reporting ? m.feedbackWrong : m.flagReview}
        </button>
      </div>
      {reporting ? (
        <>
          <label htmlFor="fb-comment" className="meta">
            {m.feedbackComment}
          </label>
          <textarea
            id="fb-comment"
            maxLength={500}
            value={comment}
            onChange={(e) => setComment(e.target.value)}
            rows={2}
            aria-label={m.feedbackComment}
            autoFocus
          />
        </>
      ) : null}
      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}
