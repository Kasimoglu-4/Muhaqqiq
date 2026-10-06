"use client";

import { useMemo } from "react";
import type { DiffHighlightSeg, DiffOp } from "@/lib/api";
import { buildSourceHighlight, buildUserHighlight } from "@/lib/buildDiffHighlight";
import { t, type Lang } from "@/lib/i18n";

type Props = {
  lang?: Lang;
  status: string;
  userText?: string | null;
  sourceText?: string | null;
  diffHighlight?: DiffHighlightSeg[];
  userDiffHighlight?: DiffHighlightSeg[];
  diff?: DiffOp[];
};

function HighlightSpans({ segments }: { segments: DiffHighlightSeg[] }) {
  return (
    <>
      {segments.map((seg, i) => (
        <span key={i} className={`hl-${seg.op || "equal"}`}>
          {seg.text || (seg.op === "insert_marker" ? "‸" : "")}
        </span>
      ))}
    </>
  );
}

function hasNonEqual(segments: DiffHighlightSeg[]): boolean {
  return segments.some((s) => s.op && s.op !== "equal");
}

export function DiffAnalysis({
  lang = "ar",
  status,
  userText,
  sourceText,
  diffHighlight = [],
  userDiffHighlight = [],
  diff = [],
}: Props) {
  const m = t(lang);
  const user = (userText || "").trim();
  const source = (sourceText || "").trim();

  const { sourceSegs, userSegs } = useMemo(() => {
    const apiSource = diffHighlight.filter((s) => s.text || s.op === "insert_marker");
    const apiUser = userDiffHighlight.filter((s) => s.text || s.op === "insert_marker");
    const sourceSegs =
      apiSource.length > 0
        ? apiSource
        : user && source
          ? buildSourceHighlight(user, source)
          : source
            ? [{ op: "equal", text: source }]
            : [];
    const userSegs =
      apiUser.length > 0
        ? apiUser
        : user && source
          ? buildUserHighlight(user, source)
          : user
            ? [{ op: "equal", text: user }]
            : [];
    return { sourceSegs, userSegs };
  }, [diffHighlight, userDiffHighlight, user, source]);

  const hasDiffOps = diff.length > 0;
  const useful =
    (user && source) || sourceSegs.length > 0 || hasDiffOps || status === "CLOSE_WITH_DIFF";

  if (status === "UNDETERMINED" && !useful) return null;
  if (!useful) return null;

  const openByDefault =
    status === "CLOSE_WITH_DIFF" || hasNonEqual(sourceSegs) || hasNonEqual(userSegs);

  return (
    <details className="diff-details" open={openByDefault}>
      <summary>
        <span className="diff-summary-label">
          <span className="material-symbols-outlined" aria-hidden="true">
            difference
          </span>
          {m.diffAnalysisTitle}
        </span>
        <span className="material-symbols-outlined diff-chevron" aria-hidden="true">
          expand_more
        </span>
      </summary>
      <div className="diff-body">
        <p className="meta" style={{ marginTop: "1rem" }}>
          {m.diffAnalysisLead}
        </p>

        <div className="diff-grid">
          <div className="diff-panel">
            <div className="diff-panel-head">
              <span>{m.diffUserLabel}</span>
            </div>
            <div className="diff-panel-body highlight-verse" dir="auto">
              {userSegs.length ? <HighlightSpans segments={userSegs} /> : "—"}
            </div>
          </div>
          <div className="diff-panel">
            <div className="diff-panel-head">
              <span>{m.diffSourceLabel}</span>
            </div>
            <div className="diff-panel-body highlight-verse" dir="auto">
              {sourceSegs.length ? <HighlightSpans segments={sourceSegs} /> : "—"}
            </div>
          </div>
        </div>

        {!sourceSegs.length && hasDiffOps ? (
          <ul className="meta" style={{ marginTop: "1rem" }}>
            {diff.map((d, i) => {
              const op = String(d.op ?? "");
              const u = d.user_span?.text ?? "";
              const orig = d.original_span?.text ?? "";
              return (
                <li key={i}>
                  {op}: «{u}» → «{orig}»
                </li>
              );
            })}
          </ul>
        ) : null}

        <div className="diff-legend">
          <span className="diff-legend-item">
            <span className="diff-swatch equal" aria-hidden="true" />
            {m.diffLegendEqual}
          </span>
          <span className="diff-legend-item">
            <span className="diff-swatch insert" aria-hidden="true" />
            {m.diffLegendInsert}
          </span>
          <span className="diff-legend-item">
            <span className="diff-swatch replace" aria-hidden="true" />
            {m.diffLegendReplace}
          </span>
        </div>
      </div>
    </details>
  );
}
