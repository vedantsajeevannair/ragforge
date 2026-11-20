import { useEffect, useState } from "react";
import { api } from "../api";
import { useAuth } from "../auth";
import { UserTable } from "../components/UserTable";
import { formatMs } from "../format";
import type { Stats } from "../types";

export function AdminPage() {
  const { user } = useAuth();
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [reindexing, setReindexing] = useState(false);
  const [reindexMsg, setReindexMsg] = useState<string | null>(null);

  async function reindex() {
    if (!window.confirm("Re-chunk and re-embed every document with the current settings?")) return;
    setReindexing(true);
    setReindexMsg(null);
    try {
      const r = await api.reindex();
      setReindexMsg(`Re-indexed ${r.reindexed} documents` +
        (r.skipped.length ? `; skipped ${r.skipped.join(", ")} (no original file)` : ""));
      setStats(await api.stats());
    } catch (e) {
      setReindexMsg((e as Error).message);
    } finally {
      setReindexing(false);
    }
  }

  useEffect(() => {
    api.stats().then(setStats).catch((e: Error) => setError(e.message));
  }, []);

  if (error) return <p className="error" role="alert">{error}</p>;
  if (!stats) return <p className="muted">Loading…</p>;

  const rated = stats.thumbs_up + stats.thumbs_down;
  const tiles: Array<[string, string]> = [
    ["Documents", String(stats.documents)],
    ["Chunks", String(stats.chunks)],
    ["Collections", String(stats.collections)],
    ["Users", String(stats.users)],
    ["Questions asked", String(stats.queries)],
    ["Grounded answers", `${Math.round(stats.grounded_rate * 100)}%`],
    ["Avg retrieval", formatMs(stats.avg_retrieval_ms)],
    ["Avg generation", formatMs(stats.avg_generation_ms)],
    ["Helpful votes", rated ? `${Math.round((stats.thumbs_up / rated) * 100)}% of ${rated}` : "—"],
  ];

  return (
    <section>
      <h2>Admin overview</h2>
      <div className="stats">
        {tiles.map(([label, value]) => (
          <div key={label} className="stat">
            <div className="value">{value}</div>
            <div className="label">{label}</div>
          </div>
        ))}
      </div>
      <div className="panel row" style={{ marginTop: 16, justifyContent: "space-between" }}>
        <span className="muted">
          Re-index after changing chunk size, overlap or the embedding model.
        </span>
        <button type="button" className="btn ghost" disabled={reindexing} onClick={reindex}>
          {reindexing ? "Re-indexing…" : "Re-index all documents"}
        </button>
        {reindexMsg && <p className="muted" role="status">{reindexMsg}</p>}
      </div>
      {user && <UserTable currentUserId={user.id} />}
    </section>
  );
}
