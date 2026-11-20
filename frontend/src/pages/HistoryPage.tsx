import { useEffect, useState } from "react";
import { api } from "../api";
import { AnswerView } from "../components/AnswerView";
import { Feedback } from "../components/Feedback";
import { formatDate } from "../format";
import type { HistoryItem } from "../types";

export function HistoryPage() {
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
      <h2>History</h2>
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
              <Feedback queryId={item.id} initial={item.feedback} />
            </>
          )}
        </div>
      ))}
    </section>
  );
}
