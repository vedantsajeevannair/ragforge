import type {
  AskOptions,
  AskResult,
  Citation,
  Collection,
  DocumentInfo,
  Hit,
  HistoryItem,
  Stats,
  TokenResponse,
  User,
} from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "/api";
const TOKEN_KEY = "ragforge.token";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

/** Called when the server rejects the token, so the app can sign the user out. */
let onUnauthorized: () => void = () => {};
export function setUnauthorizedHandler(fn: () => void) {
  onUnauthorized = fn;
}

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  const token = tokenStore.get();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const resp = await fetch(`${BASE}${path}`, { ...init, headers });
  if (resp.status === 401 && token && !path.startsWith("/auth/")) {
    tokenStore.clear();
    onUnauthorized();
  }
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      /* body was not JSON */
    }
    throw new ApiError(resp.status, detail);
  }
  return resp.status === 204 ? (undefined as T) : resp.json();
}

export const api = {
  register: (username: string, password: string) =>
    request<TokenResponse>("/auth/register", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  login: (username: string, password: string) =>
    request<TokenResponse>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username, password }),
    }),
  me: () => request<User>("/auth/me"),
  documents: (collection?: string) =>
    request<DocumentInfo[]>(
      collection ? `/documents?collection=${encodeURIComponent(collection)}` : "/documents",
    ),
  upload: async (file: File, collection: string,
    visibility: "shared" | "private" = "shared"): Promise<DocumentInfo> => {
    const form = new FormData();
    form.append("file", file);
    form.append("collection", collection);
    form.append("visibility", visibility);
    const resp = await request<DocumentInfo | { job_id: number }>("/documents",
      { method: "POST", body: form });
    return "job_id" in resp ? waitForJob<DocumentInfo>(resp.job_id) : resp;
  },
  job: (id: number) => request<Job>(`/jobs/${id}`),
  updateDocument: (docId: string,
    changes: Partial<Pick<DocumentInfo, "collection" | "visibility" | "title">>) =>
    request<DocumentInfo>(`/documents/${docId}`, {
      method: "PATCH",
      body: JSON.stringify(changes),
    }),
  deleteDocument: (docId: string) =>
    request<void>(`/documents/${docId}`, { method: "DELETE" }),
  chunks: (docId: string) => request<Hit[]>(`/documents/${docId}/chunks`),
  reindex: () =>
    request<{ reindexed: number; skipped: string[] }>("/documents/reindex", { method: "POST" }),
  download: async (docId: string, filename: string) => {
    const token = tokenStore.get();
    const resp = await fetch(`${BASE}/documents/${docId}/download`, {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    });
    if (!resp.ok) throw new ApiError(resp.status, "original file not available");
    const url = URL.createObjectURL(await resp.blob());
    const a = Object.assign(document.createElement("a"), { href: url, download: filename });
    a.click();
    URL.revokeObjectURL(url);
  },
  collections: () => request<Collection[]>("/collections"),
  ask: (query: string, opts: AskOptions) =>
    request<AskResult>("/ask", { method: "POST", body: JSON.stringify({ query, ...opts }) }),
  history: () => request<HistoryItem[]>("/history"),
  feedback: (id: number, value: 1 | -1) =>
    request<void>(`/history/${id}/feedback`, {
      method: "POST",
      body: JSON.stringify({ value }),
    }),
  stats: () => request<Stats>("/stats"),
  users: () => request<User[]>("/users"),
  setRole: (id: number, role: "admin" | "user") =>
    request<User>(`/users/${id}`, { method: "PATCH", body: JSON.stringify({ role }) }),
  deleteUser: (id: number) => request<void>(`/users/${id}`, { method: "DELETE" }),
  changePassword: (current_password: string, new_password: string) =>
    request<void>("/auth/password", {
      method: "POST",
      body: JSON.stringify({ current_password, new_password }),
    }),
};

export interface Job {
  id: number;
  kind: string;
  status: "queued" | "running" | "done" | "failed";
  result: unknown;
  error: string | null;
}

/** Poll a background job until it finishes, backing off up to 2 s between checks. */
export async function waitForJob<T>(id: number, sleep = (ms: number) =>
  new Promise((r) => setTimeout(r, ms))): Promise<T> {
  let delay = 250;
  for (;;) {
    const job = await api.job(id);
    if (job.status === "done") return job.result as T;
    if (job.status === "failed") throw new ApiError(422, job.error ?? "indexing failed");
    await sleep(delay);
    delay = Math.min(delay * 2, 2000);
  }
}

export type StreamEvent =
  | { event: "sources"; data: { hits: Hit[] } }
  | { event: "token"; data: { text: string } }
  | {
      event: "done";
      data: {
        query_id: number;
        answer: string;
        grounded: boolean;
        confidence: number;
        citations: Citation[];
        timings_ms: Record<string, number>;
      };
    }
  | { event: "error"; data: { detail: string } };

export function parseSSE(buffer: string): { events: StreamEvent[]; rest: string } {
  const blocks = buffer.split("\n\n");
  const rest = blocks.pop() ?? "";
  const events: StreamEvent[] = [];
  for (const block of blocks) {
    let event = "";
    let data = "";
    for (const line of block.split("\n")) {
      if (line.startsWith("event: ")) event = line.slice(7);
      else if (line.startsWith("data: ")) data += line.slice(6);
    }
    if (event && data) events.push({ event, data: JSON.parse(data) } as StreamEvent);
  }
  return { events, rest };
}

export async function askStream(
  query: string,
  opts: AskOptions,
  onEvent: (e: StreamEvent) => void,
  signal?: AbortSignal,
): Promise<void> {
  const token = tokenStore.get();
  const resp = await fetch(`${BASE}/ask/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ query, ...opts }),
    signal,
  });
  if (!resp.ok || !resp.body) {
    throw new ApiError(resp.status, `stream failed (${resp.status})`);
  }
  const reader = resp.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  for (;;) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const parsed = parseSSE(buffer);
    buffer = parsed.rest;
    parsed.events.forEach(onEvent);
  }
}
