import { useEffect, useState } from "react";
import { api } from "../api";
import { formatMs } from "../format";
import type { Stats } from "../types";

export function AdminPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [error, setError] = useState<string | null>(null);

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
    </section>
  );
}
