import { useState } from "react";
import type { FormEvent } from "react";
import { useAuth } from "../auth";

export function LoginPage() {
  const { login } = useAuth();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await login(username, password, mode === "register");
    } catch (err) {
      setError(err instanceof Error ? err.message : "something went wrong");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login panel">
      <h2>{mode === "login" ? "Sign in to RAGForge" : "Create an account"}</h2>
      <form onSubmit={submit}>
        <label>
          Username
          <input type="text" value={username} autoComplete="username"
            onChange={(e) => setUsername(e.target.value)} required minLength={3} />
        </label>
        <label>
          Password
          <input type="password" value={password}
            autoComplete={mode === "login" ? "current-password" : "new-password"}
            onChange={(e) => setPassword(e.target.value)} required minLength={8} />
        </label>
        {error && <p className="error" role="alert">{error}</p>}
        <button className="btn" type="submit" disabled={busy}>
          {mode === "login" ? "Sign in" : "Create account"}
        </button>
      </form>
      <p className="muted">
        {mode === "login" ? "No account yet? " : "Already registered? "}
        <button className="btn ghost" type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}>
          {mode === "login" ? "Create one" : "Sign in"}
        </button>
      </p>
    </div>
  );
}
