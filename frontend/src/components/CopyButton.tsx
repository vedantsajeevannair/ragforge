import { useState } from "react";

export function CopyButton({ text, label = "Copy answer" }: { text: string; label?: string }) {
  const [copied, setCopied] = useState(false);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      setCopied(false);
    }
  }

  return (
    <button type="button" className="btn ghost" onClick={copy} aria-live="polite">
      {copied ? "Copied" : label}
    </button>
  );
}
