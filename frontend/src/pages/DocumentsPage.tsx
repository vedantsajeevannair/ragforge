import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import { UploadPanel } from "../components/UploadPanel";
import { formatBytes, formatDate } from "../format";
import type { DocumentInfo, Hit } from "../types";

export function DocumentsPage() {
  const [docs, setDocs] = useState<DocumentInfo[]>([]);
  const [filter, setFilter] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [preview, setPreview] = useState<{ doc: DocumentInfo; chunks: Hit[] } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      setDocs(await api.documents());
      setError(null);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function remove(doc: DocumentInfo) {
    if (!window.confirm(`Delete ${doc.filename} and its ${doc.chunk_count} chunks?`)) return;
    try {
      await api.deleteDocument(doc.doc_id);
      setDocs((d) => d.filter((x) => x.doc_id !== doc.doc_id));
      if (preview?.doc.doc_id === doc.doc_id) setPreview(null);
    } catch (err) {
      setError((err as Error).message);
    }
  }

  async function showChunks(doc: DocumentInfo) {
    setPreview({ doc, chunks: await api.chunks(doc.doc_id) });
  }

  const shown = docs.filter((d) =>
    `${d.filename} ${d.collection} ${d.title ?? ""}`.toLowerCase().includes(filter.toLowerCase()),
  );

  return (
    <section>
      <h2>Documents</h2>
      <UploadPanel onUploaded={(doc) =>
        setDocs((d) => [doc, ...d.filter((x) => x.doc_id !== doc.doc_id)])} />
      {error && <p className="error" role="alert">{error}</p>}
      <div className="panel">
        <div className="row" style={{ justifyContent: "space-between", marginBottom: 8 }}>
          <input type="text" placeholder="Filter documents" aria-label="Filter documents"
            value={filter} onChange={(e) => setFilter(e.target.value)} />
          <span className="muted">{shown.length} of {docs.length}</span>
        </div>
        {loading ? <p className="muted">Loading…</p> : shown.length === 0 ? (
          <p className="muted">No documents yet. Upload some to start asking questions.</p>
        ) : (
          <table>
            <thead>
              <tr>
                <th>File</th><th>Collection</th><th className="num">Chunks</th>
                <th className="num">Size</th><th>Added</th><th />
              </tr>
            </thead>
            <tbody>
              {shown.map((d) => (
                <tr key={d.doc_id}>
                  <td>
                    <button type="button" className="btn ghost" onClick={() => showChunks(d)}>
                      {d.title || d.filename}
                    </button>
                  </td>
                  <td>{d.collection}</td>
                  <td className="num">{d.chunk_count}</td>
                  <td className="num">{formatBytes(d.size_bytes)}</td>
                  <td>{formatDate(d.created_at)}</td>
                  <td className="row">
                    <button type="button" className="btn ghost"
                      aria-label={`Download ${d.filename}`}
                      onClick={() => api.download(d.doc_id, d.filename)
                        .catch((e: Error) => setError(e.message))}>
                      Download
                    </button>
                    <button type="button" className="btn danger"
                      aria-label={`Delete ${d.filename}`} onClick={() => remove(d)}>
                      Delete
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
      {preview && (
        <div className="panel">
          <div className="row" style={{ justifyContent: "space-between" }}>
            <h3>{preview.doc.filename}: {preview.chunks.length} chunks</h3>
            <button type="button" className="btn ghost" onClick={() => setPreview(null)}>
              Close
            </button>
          </div>
          <ol>
            {preview.chunks.map((c) => (
              <li key={c.chunk_id}>
                {"section" in c.metadata && (
                  <strong>{String(c.metadata.section)} </strong>
                )}
                {"page" in c.metadata && (
                  <span className="muted">p. {String(c.metadata.page)} </span>
                )}
                <p className="muted">{c.text}</p>
              </li>
            ))}
          </ol>
        </div>
      )}
    </section>
  );
}
