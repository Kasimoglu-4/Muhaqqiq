import type { DiffHighlightSeg } from "@/lib/api";

/** Strip tashkeel / tatweel and unify common Arabic letter variants for alignment. */
export function arabicAlignKey(ch: string): string {
  if (/[\u064B-\u065F\u0670\u06D6-\u06ED\u08D4-\u08FF\u0640]/.test(ch)) return "";
  if (/\s/.test(ch)) return "";
  let c = ch.normalize("NFKC");
  c = c.replace(/[أإآٱ]/g, "ا").replace(/ى/g, "ي").replace(/[ؤئ]/g, "ي").replace(/ء/g, "");
  c = c.replace(/ة/g, "ه");
  if (!/\w/u.test(c)) return "";
  return c;
}

type Point = { start: number; end: number; key: string };

function letterPoints(text: string): Point[] {
  const points: Point[] = [];
  let i = 0;
  while (i < text.length) {
    const key = arabicAlignKey(text[i]!);
    if (!key) {
      i += 1;
      continue;
    }
    const start = i;
    i += 1;
    while (i < text.length && /[\u064B-\u065F\u0670\u06D6-\u06ED\u08D4-\u08FF\u0640]/.test(text[i]!)) {
      i += 1;
    }
    points.push({ start, end: i, key });
  }
  return points;
}

/** Myers-style LCS opcodes on letter keys (equal / insert / delete / replace). */
function opcodes(a: string[], b: string[]): Array<{ tag: string; a1: number; a2: number; b1: number; b2: number }> {
  const n = a.length;
  const m = b.length;
  const dp: number[][] = Array.from({ length: n + 1 }, () => Array(m + 1).fill(0));
  for (let i = n - 1; i >= 0; i--) {
    for (let j = m - 1; j >= 0; j--) {
      dp[i]![j] = a[i] === b[j] ? (dp[i + 1]![j + 1]! + 1) : Math.max(dp[i + 1]![j]!, dp[i]![j + 1]!);
    }
  }
  const ops: Array<{ tag: string; a1: number; a2: number; b1: number; b2: number }> = [];
  let i = 0;
  let j = 0;
  while (i < n || j < m) {
    if (i < n && j < m && a[i] === b[j]) {
      const a1 = i;
      const b1 = j;
      while (i < n && j < m && a[i] === b[j]) {
        i += 1;
        j += 1;
      }
      ops.push({ tag: "equal", a1, a2: i, b1, b2: j });
    } else if (j < m && (i >= n || dp[i]![j + 1]! >= dp[i + 1]![j]!)) {
      const b1 = j;
      while (j < m && (i >= n || (a[i] !== b[j] && dp[i]![j + 1]! >= dp[i + 1]![j]!))) {
        j += 1;
        if (i < n && a[i] === b[j - 1]) break;
      }
      // regroup: prefer replace when both sides advance
      ops.push({ tag: "insert", a1: i, a2: i, b1, b2: j });
    } else if (i < n) {
      const a1 = i;
      while (i < n && (j >= m || (a[i] !== b[j] && dp[i + 1]![j]! >= dp[i]![j + 1]!))) {
        i += 1;
        if (j < m && a[i - 1] === b[j]) break;
      }
      ops.push({ tag: "delete", a1, a2: i, b1: j, b2: j });
    } else {
      break;
    }
  }
  // Merge adjacent delete+insert into replace
  const merged: typeof ops = [];
  for (let k = 0; k < ops.length; k++) {
    const cur = ops[k]!;
    const next = ops[k + 1];
    if (cur.tag === "delete" && next?.tag === "insert" && cur.a2 === next.a1 && cur.b2 === next.b1) {
      merged.push({ tag: "replace", a1: cur.a1, a2: cur.a2, b1: next.b1, b2: next.b2 });
      k += 1;
    } else if (cur.tag === "insert" && next?.tag === "delete" && cur.a2 === next.a1 && cur.b2 === next.b1) {
      merged.push({ tag: "replace", a1: next.a1, a2: next.a2, b1: cur.b1, b2: cur.b2 });
      k += 1;
    } else {
      merged.push(cur);
    }
  }
  return merged;
}

function slicePoints(text: string, points: Point[], from: number, to: number): string {
  if (from >= to || !points.length) return "";
  let start = points[from]!.start;
  let end = points[to - 1]!.end;
  while (end < text.length && (/\s/.test(text[end]!) || /[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]/.test(text[end]!))) {
    end += 1;
  }
  return text.slice(start, end);
}

/**
 * Client fallback: paint source (and optionally user) when API highlight is empty.
 * Uses letter-level LCS after Arabic alignment keys — same idea as SequenceMatcher.
 */
export function buildSourceHighlight(userText: string, sourceText: string): DiffHighlightSeg[] {
  const userPts = letterPoints(userText);
  const sourcePts = letterPoints(sourceText);
  if (!userPts.length || !sourcePts.length) {
    return sourceText ? [{ op: "equal", text: sourceText }] : [];
  }
  const a = userPts.map((p) => p.key);
  const b = sourcePts.map((p) => p.key);
  const ops = opcodes(a, b);
  const segs: DiffHighlightSeg[] = [];
  for (const op of ops) {
    if (op.tag === "equal") {
      const text = slicePoints(sourceText, sourcePts, op.b1, op.b2);
      if (text) segs.push({ op: "equal", text });
    } else if (op.tag === "insert" || op.tag === "replace") {
      const text = slicePoints(sourceText, sourcePts, op.b1, op.b2);
      if (text) segs.push({ op: op.tag === "insert" ? "insert" : "replace", text });
    } else if (op.tag === "delete") {
      segs.push({ op: "insert_marker", text: "" });
    }
  }
  return segs.length ? segs : [{ op: "equal", text: sourceText }];
}

export function buildUserHighlight(userText: string, sourceText: string): DiffHighlightSeg[] {
  const userPts = letterPoints(userText);
  const sourcePts = letterPoints(sourceText);
  if (!userPts.length) {
    return userText ? [{ op: "equal", text: userText }] : [];
  }
  if (!sourcePts.length) {
    return [{ op: "replace", text: userText }];
  }
  const a = userPts.map((p) => p.key);
  const b = sourcePts.map((p) => p.key);
  const ops = opcodes(a, b);
  const segs: DiffHighlightSeg[] = [];
  for (const op of ops) {
    if (op.tag === "equal") {
      const text = slicePoints(userText, userPts, op.a1, op.a2);
      if (text) segs.push({ op: "equal", text });
    } else if (op.tag === "delete" || op.tag === "replace") {
      const text = slicePoints(userText, userPts, op.a1, op.a2);
      if (text) segs.push({ op: "replace", text });
    }
  }
  return segs.length ? segs : [{ op: "equal", text: userText }];
}
