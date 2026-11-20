import { useEffect, useState } from "react";
import { api } from "../api";
import type { Collection } from "../types";
import { useToast } from "./Toasts";

export function CollectionTable() {
  const [collections, setCollections] = useState<Collection[]>([]);
  const toast = useToast();

  useEffect(() => {
    api.collections().then(setCollections).catch(() => setCollections([]));
  }, []);

  async function remove(c: Collection) {
    if (!window.confirm(`Delete collection "${c.name}" and its ${c.documents} documents? ` +
      "This cannot be undone.")) return;
    try {
      const r = await api.deleteCollection(c.name);
      setCollections((list) => list.filter((x) => x.name !== c.name));
      toast(`Deleted ${r.deleted} documents from ${c.name}`);
    } catch (e) {
      toast((e as Error).message, "error");
    }
  }

  return (
    <div className="panel">
      <h3>Collections</h3>
      {collections.length === 0 ? <p className="muted">No collections yet.</p> : (
        <table>
          <thead><tr><th>Name</th><th className="num">Documents</th><th /></tr></thead>
          <tbody>
            {collections.map((c) => (
              <tr key={c.name}>
                <td>{c.name}</td>
                <td className="num">{c.documents}</td>
                <td>
                  <button type="button" className="btn danger"
                    aria-label={`Delete collection ${c.name}`} onClick={() => remove(c)}>
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
