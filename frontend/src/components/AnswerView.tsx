import { useState } from "react";
import { splitCitations } from "../format";
import type { Citation } from "../types";

interface Props {
  answer: string;
  citations: Citation[];
  streaming?: boolean;
}

export function AnswerView({ answer, citations, streaming = false }: Props) {
  const [active, setActive] = useState<number | null>(null);
  const byNumber = new Map(citations.map((c) => [c.number, c]));

  return (
    <div>
      <p className="answer" aria-live="polite">
        {splitCitations(answer).map((part, i) =>
          part.kind === "text" ? (
            <span key={i}>{part.text}</span>
          ) : (
            <button key={i} type="button" className="cite"
              aria-label={`Show source ${part.n}`}
              onClick={() => setActive(active === part.n ? null : part.n)}>
              {part.n}
            </button>
          ),
        )}
        {streaming && <span className="muted"> ▍</span>}
      </p>
      {citations.length > 0 && (
        <div className="sources">
          {citations.map((c) => (
            <article key={c.number}
              className={`source${active === c.number ? " active" : ""}`}
              data-testid={`source-${c.number}`}>
              <header>[{c.number}] {c.source}</header>
              <div className="muted">{c.snippet}</div>
            </article>
          ))}
        </div>
      )}
      {active !== null && !byNumber.has(active) && (
        <p className="muted">Source {active} is not available.</p>
      )}
    </div>
  );
}
