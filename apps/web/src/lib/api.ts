/** Resolve API base at call time so localhost vs 127.0.0.1 matches the page. */
export function getApiUrl(): string {
  const fromEnv = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "");
  if (fromEnv) return fromEnv;
  if (typeof window !== "undefined") {
    const host = window.location.hostname;
    if (host === "localhost" || host === "127.0.0.1") {
      return `http://${host}:8000`;
    }
  }
  return "http://127.0.0.1:8000";
}

/** @deprecated Prefer getApiUrl() — kept for existing imports. */
export const API_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export type Grading = {
  grader?: string;
  grade?: string;
  ruling?: string;
  reference?: string;
  url?: string;
  source?: string;
};

export type MatchRef = {
  kind: string;
  text?: string;
  score?: number;
  ref?: Record<string, unknown>;
  proof_url?: string;
  correct_text?: string;
  translations?: Array<{ lang: string; text: string }>;
  grading?: Grading;
  gradings?: Grading[];
};

export type DiffSpan = {
  start?: number;
  end?: number;
  text?: string;
};

export type DiffOp = {
  op: string;
  user_span?: DiffSpan;
  original_span?: DiffSpan;
};

export type DiffHighlightSeg = {
  op?: string;
  text?: string;
};

export type VerifyResult = {
  card_id: string;
  status: string;
  status_ar: string;
  matches: MatchRef[];
  diff: DiffOp[];
  diff_highlight?: DiffHighlightSeg[];
  user_diff_highlight?: DiffHighlightSeg[];
  correct_text?: string | null;
  /** Best contiguous source span for CLOSE (may be shorter than full matn). */
  matched_span?: string | null;
  gradings?: Grading[];
  score: number | null;
  card_url: string;
  data_version: string;
  ai_disclosure: string;
  supported_means: string;
  reply_template_key?: string | null;
};

export async function verifyText(text: string): Promise<VerifyResult> {
  const res = await fetch(`${getApiUrl()}/v1/verify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export async function ocrImage(file: File): Promise<{
  extracted_text: string;
  confidence: number;
  provider: string;
}> {
  const form = new FormData();
  form.append("image", file);
  const res = await fetch(`${getApiUrl()}/v1/verify`, { method: "POST", body: form });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}

export async function fetchCard(id: string) {
  const res = await fetch(`${getApiUrl()}/v1/cards/${id}`, { cache: "no-store" });
  if (!res.ok) return null;
  return res.json();
}

export async function fetchSources() {
  const res = await fetch(`${getApiUrl()}/v1/sources`, { next: { revalidate: 3600 } });
  if (!res.ok) throw new Error("sources failed");
  return res.json();
}

export async function submitFeedback(body: {
  card_id?: string;
  kind: "useful" | "wrong" | "other";
  comment?: string;
}): Promise<{ ok: string; id: string }> {
  const res = await fetch(`${getApiUrl()}/v1/feedback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    throw new Error(await res.text());
  }
  return res.json();
}
