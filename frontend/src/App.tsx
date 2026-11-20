import { useState } from "react";
import { useAuth } from "./auth";
import { AdminPage } from "./pages/AdminPage";
import { AskPage } from "./pages/AskPage";
import { DocumentsPage } from "./pages/DocumentsPage";
import { HistoryPage } from "./pages/HistoryPage";
import { LoginPage } from "./pages/LoginPage";

type Page = "ask" | "documents" | "history" | "admin";

const PAGES: Array<{ id: Page; label: string; admin?: boolean }> = [
  { id: "ask", label: "Ask" },
  { id: "documents", label: "Documents" },
  { id: "history", label: "History" },
  { id: "admin", label: "Admin", admin: true },
];

export function App() {
  const { user, loading, logout } = useAuth();
  const [page, setPage] = useState<Page>("ask");

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
          <button type="button" className="btn ghost" style={{ marginTop: 8 }} onClick={logout}>
            Sign out
          </button>
        </div>
      </aside>
      <main>
        {page === "ask" && <AskPage />}
        {page === "documents" && <DocumentsPage />}
        {page === "history" && <HistoryPage />}
        {page === "admin" && <AdminPage />}
      </main>
    </div>
  );
}
