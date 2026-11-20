import { useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import type { DocumentInfo } from "../types";

interface Props {
  doc: DocumentInfo;
  onSaved: (doc: DocumentInfo) => void;
  onCancel: () => void;
}

export function EditDocument({ doc, onSaved, onCancel }: Props) {
  const [title, setTitle] = useState(doc.title ?? "");
  const [collection, setCollection] = useState(doc.collection);
  const [visibility, setVisibility] = useState(doc.visibility);
  const [error, setError] = useState<string | null>(null);

  async function save(e: FormEvent) {
    e.preventDefault();
    const changes: Parameters<typeof api.updateDocument>[1] = {};
    if (title !== (doc.title ?? "")) changes.title = title;
    if (collection !== doc.collection) changes.collection = collection;
    if (visibility !== doc.visibility) changes.visibility = visibility;
    if (Object.keys(changes).length === 0) return onCancel();
    try {
      onSaved(await api.updateDocument(doc.doc_id, changes));
    } catch (err) {
      setError((err as Error).message);
    }
  }

  return (
    <form className="panel" onSubmit={save} aria-label={`Edit ${doc.filename}`}>
      <h3>Edit {doc.filename}</h3>
      <div className="row">
        <label>Title <input type="text" value={title} maxLength={200}
          onChange={(e) => setTitle(e.target.value)} /></label>
        <label>Collection <input type="text" value={collection} required pattern="[\w.-]+"
          onChange={(e) => setCollection(e.target.value)} /></label>
        <label>Visible to{" "}
          <select value={visibility}
            onChange={(e) => setVisibility(e.target.value as DocumentInfo["visibility"])}>
            <option value="shared">Everyone</option>
            <option value="private">Only owner and admins</option>
          </select>
        </label>
      </div>
      {error && <p className="error" role="alert">{error}</p>}
      <div className="row" style={{ marginTop: 10 }}>
        <button className="btn" type="submit">Save</button>
        <button className="btn ghost" type="button" onClick={onCancel}>Cancel</button>
      </div>
    </form>
  );
}
