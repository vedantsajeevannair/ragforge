import { useEffect, useState } from "react";
import { api } from "../api";
import { AnswerView } from "../components/AnswerView";
import { Feedback } from "../components/Feedback";
import { formatDate } from "../format";
import type { HistoryItem } from "../types";

function csvCell(value: string): string {
  return /[",\n]/.test(value) ? `"${value.replace(/"/g, '""')}"` : value;
}

export function historyToCsv(items: HistoryItem[]): string {
  const header = ["id", "created_at", "mode", "grounded", "feedback", "question", "answer",
    "sources"];
  const rows = items.map((i) => [String(i.id), i.created_at, i.mode, String(i.grounded),
    i.feedback === null ? "" : String(i.feedback), i.question, i.answer,
    i.citations.map((c) => c.source).join("; ")].map(csvCell).join(","));
  return [header.join(","), ...rows].join("\n");
}

function downloadCsv(items: HistoryItem[]) {
  const blob = new Blob([historyToCsv(items)], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = Object.assign(document.createElement("a"), { href: url,
    download: "ragforge-history.csv" });
  a.click();
  URL.revokeObjectURL(url);
}

export function HistoryPage({ onAskAgain }: { onAskAgain?: (question: string) => void }) {
  const [items, setItems] = useState<HistoryItem[] | null>(null);
  const [open, setOpen] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.history().then(setItems).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="error" role="alert">{error}</p>;
  if (items === null) return <p className="muted">Loading…</p>;

  return (
    <section>
      <div className="row" style={{ justifyContent: "space-between" }}>
        <h2>History</h2>
        <button type="button" className="btn ghost" disabled={!items.length}
          onClick={() => downloadCsv(items)}>
          Export CSV
        </button>
      </div>
      {items.length === 0 && <p className="muted">You have not asked anything yet.</p>}
      {items.map((item) => (
        <div key={item.id} className="panel">
          <button type="button" className="btn ghost" aria-expanded={open === item.id}
            onClick={() => setOpen(open === item.id ? null : item.id)}>
            {item.question}
          </button>
          <span className="muted"> · {item.mode} · {formatDate(item.created_at)} </span>
          <span className={`badge ${item.grounded ? "ok" : "warn"}`}>
            {item.grounded ? "grounded" : "not grounded"}
          </span>
          {open === item.id && (
            <>
              <AnswerView answer={item.answer} citations={item.citations} />
              <div className="row">
                <Feedback queryId={item.id} initial={item.feedback} />
                {onAskAgain && (
                  <button type="button" className="btn ghost"
                    onClick={() => onAskAgain(item.question)}>
                    Ask again
                  </button>
                )}
              </div>
            </>
          )}
        </div>
      ))}
    </section>
  );
}
