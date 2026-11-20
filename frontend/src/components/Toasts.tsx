import { createContext, useCallback, useContext, useState } from "react";
import type { ReactNode } from "react";

type Kind = "info" | "error";
interface Toast {
  id: number;
  text: string;
  kind: Kind;
}

const ToastContext = createContext<(text: string, kind?: Kind) => void>(() => {});

let nextId = 1;

export function ToastProvider({ children, timeoutMs = 4000 }:
  { children: ReactNode; timeoutMs?: number }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const push = useCallback((text: string, kind: Kind = "info") => {
    const id = nextId++;
    setToasts((t) => [...t, { id, text, kind }]);
    setTimeout(() => setToasts((t) => t.filter((x) => x.id !== id)), timeoutMs);
  }, [timeoutMs]);

  return (
    <ToastContext.Provider value={push}>
      {children}
      <div className="toasts" aria-live="polite">
        {toasts.map((t) => (
          <div key={t.id} className={`toast ${t.kind}`} role="status">{t.text}</div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export const useToast = () => useContext(ToastContext);
