import type { ReactNode } from "react";

interface Props {
  text: string;
  spans?: Array<[number, number]>;
  maxLength?: number;
}

/** Render text with <mark> around the given spans, optionally truncated. */
export function Highlighted({ text, spans = [], maxLength }: Props) {
  const limit = maxLength ?? text.length;
  const out: ReactNode[] = [];
  let pos = 0;
  for (const [start, end] of [...spans].sort((a, b) => a[0] - b[0])) {
    if (start >= limit) break;
    if (start < pos) continue;
    if (start > pos) out.push(text.slice(pos, start));
    out.push(<mark key={start}>{text.slice(start, Math.min(end, limit))}</mark>);
    pos = Math.min(end, limit);
  }
  if (pos < limit) out.push(text.slice(pos, limit));
  if (limit < text.length) out.push("…");
  return <>{out}</>;
}
