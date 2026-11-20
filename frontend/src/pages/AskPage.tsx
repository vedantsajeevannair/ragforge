import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { api, askStream } from "../api";
import { AnswerView } from "../components/AnswerView";
import { Feedback } from "../components/Feedback";
import { formatMs } from "../format";
import type { AskOptions, Citation, Collection, Hit, SearchMode } from "../types";

interface Turn {
  question: string;
  answer: string;
  citations: Citation[];
  grounded: boolean | null;
  queryId: number | null;
}

interface Result {
  answer: string;
  citations: Citation[];
  hits: Hit[];
  grounded: boolean | null;
  queryId: number | null;
  timings: Record<string, number>;
}

const EMPTY: Result = { answer: "", citations: [], hits: [], grounded: null, queryId: null,
  timings: {} };

export function AskPage() {
  const [question, setQuestion] = useState("");
  const [mode, setMode] = useState<SearchMode>("hybrid");
  const [k, setK] = useState(5);
  const [collection, setCollection] = useState("");
  const [useMmr, setUseMmr] = useState(false);
  const [collections, setCollections] = useState<Collection[]>([]);
  const [result, setResult] = useState<Result>(EMPTY);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [asked, setAsked] = useState("");
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  useEffect(() => {
    api.collections().then(setCollections).catch(() => setCollections([]));
    return () => abortRef.current?.abort();
  }, []);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (!question.trim()) return;
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;
    if (result.answer && asked) {
      setTurns((t) => [...t, { question: asked, answer: result.answer,
        citations: result.citations, grounded: result.grounded, queryId: result.queryId }]);
    }
    const previous = [...turns.map((t) => t.question), ...(asked ? [asked] : [])].slice(-5);
    setAsked(question);
    setQuestion("");
    setResult(EMPTY);
    setError(null);
    setStreaming(true);
    const opts: AskOptions = { k, mode, use_mmr: useMmr, use_rerank: true,
      previous_questions: previous, ...(collection ? { collection } : {}) };
    try {
      await askStream(question, opts, (ev) => {
        if (ev.event === "sources") setResult((r) => ({ ...r, hits: ev.data.hits }));
        else if (ev.event === "token")
          setResult((r) => ({ ...r, answer: r.answer + ev.data.text }));
        else if (ev.event === "done")
          setResult((r) => ({ ...r, answer: ev.data.answer, citations: ev.data.citations,
            grounded: ev.data.grounded, queryId: ev.data.query_id,
            timings: ev.data.timings_ms }));
        else if (ev.event === "error") setError(ev.data.detail);
      }, controller.signal);
    } catch (err) {
      if ((err as Error).name !== "AbortError") setError((err as Error).message);
    } finally {
      setStreaming(false);
    }
  }

  return (
    <section>
      <h2>Ask your documents</h2>
      <form className="panel" onSubmit={submit}>
        <textarea aria-label="Question" placeholder="e.g. How does reciprocal rank fusion work?"
          value={question} onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) submit(e);
          }} />
        <div className="row" style={{ marginTop: 10 }}>
          <label>Mode{" "}
            <select value={mode} onChange={(e) => setMode(e.target.value as SearchMode)}>
              <option value="hybrid">Hybrid</option>
              <option value="dense">Dense</option>
              <option value="bm25">BM25</option>
            </select>
          </label>
          <label>Passages{" "}
            <select value={k} onChange={(e) => setK(Number(e.target.value))}>
              {[3, 5, 8, 10].map((n) => <option key={n} value={n}>{n}</option>)}
            </select>
          </label>
          <label>Collection{" "}
            <select value={collection} onChange={(e) => setCollection(e.target.value)}>
              <option value="">All</option>
              {collections.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
            </select>
          </label>
          <label>
            <input type="checkbox" checked={useMmr} onChange={(e) => setUseMmr(e.target.checked)} />
            {" "}Diversify (MMR)
          </label>
          <button className="btn" type="submit" disabled={streaming || !question.trim()}>
            {streaming ? "Answering…" : "Ask"}
          </button>
        </div>
      </form>
      {(turns.length > 0 || asked) && (
        <div className="row" style={{ justifyContent: "space-between" }}>
          <span className="muted">
            Conversation: follow-up questions use the earlier ones for context.
          </span>
          <button type="button" className="btn ghost" disabled={streaming}
            onClick={() => { setTurns([]); setAsked(""); setResult(EMPTY); }}>
            New conversation
          </button>
        </div>
      )}
      {turns.map((t, i) => (
        <div key={i} className="panel turn">
          <p><strong>{t.question}</strong></p>
          <AnswerView answer={t.answer} citations={t.citations} />
        </div>
      ))}
      {error && <p className="error" role="alert">{error}</p>}
      {(result.answer || streaming) && (
        <div className="panel">
          {asked && <p><strong>{asked}</strong></p>}
          <div className="row" style={{ justifyContent: "space-between" }}>
            {result.grounded === null ? <span className="muted">Generating…</span> : (
              <span className={`badge ${result.grounded ? "ok" : "warn"}`}>
                {result.grounded ? "Grounded in sources" : "Not grounded"}
              </span>
            )}
            {result.timings.retrieval !== undefined && (
              <span className="muted">
                retrieval {formatMs(result.timings.retrieval)} · generation{" "}
                {formatMs(result.timings.generation ?? 0)}
              </span>
            )}
          </div>
          <AnswerView answer={result.answer} citations={result.citations} streaming={streaming} />
          {result.queryId !== null && <Feedback queryId={result.queryId} />}
        </div>
      )}
      {result.hits.length > 0 && (
        <details className="panel">
          <summary>Retrieved passages ({result.hits.length})</summary>
          <ol>
            {result.hits.map((h) => (
              <li key={h.chunk_id}>
                <strong>{String(h.metadata.source ?? h.doc_id)}</strong>{" "}
                <span className="muted">score {h.score.toFixed(3)}</span>
                <p className="muted">{h.text.slice(0, 280)}{h.text.length > 280 ? "…" : ""}</p>
              </li>
            ))}
          </ol>
        </details>
      )}
    </section>
  );
}
