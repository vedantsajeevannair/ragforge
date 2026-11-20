import { useEffect, useState } from "react";
import { useAuth } from "./auth";
import { ErrorBoundary } from "./components/ErrorBoundary";
import { AccountPage } from "./pages/AccountPage";
import { AdminPage } from "./pages/AdminPage";
import { AskPage } from "./pages/AskPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LoginPage } from "./pages/LoginPage";
import { applyTheme, loadTheme, nextTheme } from "./theme";
import type { Theme } from "./theme";

type Page = "ask" | "documents" | "history" | "account" | "admin";

const PAGES: Array<{ id: Page; label: string; admin?: boolean }> = [
  { id: "ask", label: "Ask" },
  { id: "documents", label: "Documents" },
  { id: "history", label: "History" },
  { id: "account", label: "Account" },
  { id: "admin", label: "Admin", admin: true },
];

export function App() {
  const { user, loading, logout } = useAuth();
  const [page, setPage] = useState<Page>("ask");
  const [theme, setTheme] = useState<Theme>(loadTheme);
  const [prefill, setPrefill] = useState("");

  useEffect(() => applyTheme(theme), [theme]);

  if (loading) return <p className="muted" style={{ padding: 32 }}>Loading…</p>;
  if (!user) return <LoginPage />;

  return (
    <div className="app">
      <aside className="sidebar">
        <h1>RAGForge</h1>
        <nav className="nav">
          {PAGES.filter((p) => !p.admin || user.role === "admin").map((p) => (
            <button key={p.id} type="button" aria-current={page === p.id ? "page" : undefined}
              onClick={() => setPage(p.id)}>
              {p.label}
            </button>
          ))}
        </nav>
        <div className="who">
          Signed in as <strong>{user.username}</strong> ({user.role})
          <br />
          <div className="row" style={{ marginTop: 8 }}>
            <button type="button" className="btn ghost" onClick={logout}>Sign out</button>
            <button type="button" className="btn ghost" aria-label="Change theme"
              onClick={() => setTheme(nextTheme(theme))}>
              Theme: {theme}
            </button>
          </div>
        </div>
      </aside>
      <main>
        <ErrorBoundary key={page}>
        {page === "ask" && <AskPage key={prefill} initialQuestion={prefill} />}
        {page === "documents" && <DocumentsPage />}
        {page === "history" && (
          <HistoryPage onAskAgain={(q) => { setPrefill(q); setPage("ask"); }} />
        )}
        {page === "account" && <AccountPage />}
        {page === "admin" && <AdminPage />}
        </ErrorBoundary>
      </main>
    </div>
  );
}
