import { useRef, useState } from "react";
import type { DragEvent } from "react";
import { api } from "../api";
import type { DocumentInfo } from "../types";

const ACCEPT = ".pdf,.md,.markdown,.txt,.html,.htm";

interface Props {
  onUploaded: (doc: DocumentInfo) => void;
}

export function UploadPanel({ onUploaded }: Props) {
  const [collection, setCollection] = useState("default");
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [errors, setErrors] = useState<string[]>([]);
  const inputRef = useRef<HTMLInputElement>(null);

  async function upload(files: FileList | File[]) {
    const list = Array.from(files);
    setErrors([]);
    for (const file of list) {
      setBusy(file.name);
      try {
        onUploaded(await api.upload(file, collection.trim() || "default"));
      } catch (err) {
        setErrors((e) => [...e, `${file.name}: ${(err as Error).message}`]);
      }
    }
    setBusy(null);
    if (inputRef.current) inputRef.current.value = "";
  }

  function onDrop(e: DragEvent) {
    e.preventDefault();
    setOver(false);
    if (e.dataTransfer.files.length) upload(e.dataTransfer.files);
  }

  return (
    <div className="panel">
      <div className="row" style={{ marginBottom: 12 }}>
        <label>Collection{" "}
          <input type="text" value={collection} pattern="[\w.-]+"
            onChange={(e) => setCollection(e.target.value)} />
        </label>
      </div>
      <div className={`dropzone${over ? " over" : ""}`}
        onDragOver={(e) => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)} onDrop={onDrop}>
        <p>{busy ? `Indexing ${busy}…` : "Drop PDF, Markdown, HTML or text files here"}</p>
        <label className="btn ghost">
          Choose files
          <input ref={inputRef} type="file" multiple accept={ACCEPT} hidden
            aria-label="Choose files" disabled={!!busy}
            onChange={(e) => e.target.files && upload(e.target.files)} />
        </label>
      </div>
      {errors.map((e) => <p key={e} className="error" role="alert">{e}</p>)}
    </div>
  );
}
