import { useState } from "react";
import { api } from "../api";

export function Feedback({ queryId, initial = null }: { queryId: number; initial?: number | null }) {
  const [value, setValue] = useState<number | null>(initial);
  const [error, setError] = useState(false);

  async function send(v: 1 | -1) {
    setError(false);
    try {
      await api.feedback(queryId, v);
      setValue(v);
    } catch {
      setError(true);
    }
  }

  return (
    <span className="row" aria-label="Rate this answer">
      <button type="button" className="btn ghost" aria-pressed={value === 1}
        onClick={() => send(1)}>👍 Helpful</button>
      <button type="button" className="btn ghost" aria-pressed={value === -1}
        onClick={() => send(-1)}>👎 Not helpful</button>
      {error && <span className="error">Could not save feedback</span>}
    </span>
  );
}
