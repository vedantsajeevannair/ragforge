import { useState } from "react";
import type { FormEvent } from "react";
import { api } from "../api";
import { useAuth } from "../auth";

export function AccountPage() {
  const { user } = useAuth();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [message, setMessage] = useState<{ ok: boolean; text: string } | null>(null);

  async function submit(e: FormEvent) {
    e.preventDefault();
    if (next !== confirm) {
      setMessage({ ok: false, text: "New passwords do not match" });
      return;
    }
    try {
      await api.changePassword(current, next);
      setMessage({ ok: true, text: "Password updated" });
      setCurrent("");
      setNext("");
      setConfirm("");
    } catch (err) {
      setMessage({ ok: false, text: (err as Error).message });
    }
  }

  return (
    <section>
      <h2>Account</h2>
      <p className="muted">Signed in as {user?.username} ({user?.role})</p>
      <form className="panel login" style={{ margin: 0 }} onSubmit={submit}>
        <h3>Change password</h3>
        <label>Current password
          <input type="password" value={current} autoComplete="current-password"
            onChange={(e) => setCurrent(e.target.value)} required />
        </label>
        <label>New password
          <input type="password" value={next} minLength={8} autoComplete="new-password"
            onChange={(e) => setNext(e.target.value)} required />
        </label>
        <label>Confirm new password
          <input type="password" value={confirm} minLength={8} autoComplete="new-password"
            onChange={(e) => setConfirm(e.target.value)} required />
        </label>
        {message && (
          <p className={message.ok ? "muted" : "error"} role="status">{message.text}</p>
        )}
        <button className="btn" type="submit">Update password</button>
      </form>
    </section>
  );
}
