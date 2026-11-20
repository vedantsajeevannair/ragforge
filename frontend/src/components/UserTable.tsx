import { useEffect, useState } from "react";
import { api } from "../api";
import type { User } from "../types";

export function UserTable({ currentUserId }: { currentUserId: number }) {
  const [users, setUsers] = useState<User[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.users().then(setUsers).catch((e: Error) => setError(e.message));
  }, []);

  async function toggleRole(u: User) {
    setError(null);
    try {
      const updated = await api.setRole(u.id, u.role === "admin" ? "user" : "admin");
      setUsers((list) => list.map((x) => (x.id === u.id ? updated : x)));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  async function remove(u: User) {
    if (!window.confirm(`Delete user ${u.username}? Their history is deleted too.`)) return;
    setError(null);
    try {
      await api.deleteUser(u.id);
      setUsers((list) => list.filter((x) => x.id !== u.id));
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="panel">
      <h3>Users</h3>
      {error && <p className="error" role="alert">{error}</p>}
      <table>
        <thead><tr><th>Username</th><th>Role</th><th /></tr></thead>
        <tbody>
          {users.map((u) => (
            <tr key={u.id}>
              <td>{u.username}{u.id === currentUserId && <span className="muted"> (you)</span>}</td>
              <td>{u.role}</td>
              <td className="row">
                <button type="button" className="btn ghost" onClick={() => toggleRole(u)}>
                  {u.role === "admin" ? "Make user" : "Make admin"}
                </button>
                <button type="button" className="btn danger" disabled={u.id === currentUserId}
                  aria-label={`Delete user ${u.username}`} onClick={() => remove(u)}>
                  Delete
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
