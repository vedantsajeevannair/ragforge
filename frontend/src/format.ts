export function formatBytes(n: number): string {
  if (n < 1024) return `${n} B`;
  const units = ["KB", "MB", "GB"];
  let value = n / 1024;
  let i = 0;
  while (value >= 1024 && i < units.length - 1) {
    value /= 1024;
    i++;
  }
  return `${value.toFixed(value < 10 ? 1 : 0)} ${units[i]}`;
}

export function formatMs(ms: number): string {
  return ms < 1000 ? `${Math.round(ms)} ms` : `${(ms / 1000).toFixed(1)} s`;
}

export function formatDate(sqliteUtc: string): string {
  if (!sqliteUtc) return "";
  const d = new Date(sqliteUtc.replace(" ", "T") + "Z");
  return Number.isNaN(d.getTime())
    ? sqliteUtc
    : d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export type AnswerPart = { kind: "text"; text: string } | { kind: "cite"; n: number };

/** Split "foo [1] bar [2][3]" into text and citation parts for rendering. */
export function splitCitations(answer: string): AnswerPart[] {
  const parts: AnswerPart[] = [];
  const re = /\[(\d{1,3})\]/g;
  let last = 0;
  for (let m = re.exec(answer); m; m = re.exec(answer)) {
    if (m.index > last) parts.push({ kind: "text", text: answer.slice(last, m.index) });
    parts.push({ kind: "cite", n: Number(m[1]) });
    last = m.index + m[0].length;
  }
  if (last < answer.length) parts.push({ kind: "text", text: answer.slice(last) });
  return parts;
}
