export type SearchMode = "dense" | "bm25" | "hybrid";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
}

export interface User {
  id: number;
  username: string;
  role: string;
}

export interface DocumentInfo {
  doc_id: string;
  filename: string;
  collection: string;
  doc_type: string | null;
  size_bytes: number;
  chunk_count: number;
  title: string | null;
  created_at: string;
  visibility: "shared" | "private";
  owner_id: number | null;
}

export interface Hit {
  chunk_id: string;
  doc_id: string;
  text: string;
  score: number;
  metadata: Record<string, unknown>;
  highlights?: Array<[number, number]>;
}

export interface Citation {
  number: number;
  chunk_id: string;
  doc_id: string;
  source: string;
  snippet: string;
}

export interface AskResult {
  query_id: number;
  question: string;
  answer: string;
  grounded: boolean;
  citations: Citation[];
  hits: Hit[];
  timings_ms: Record<string, number>;
}

export interface HistoryItem {
  id: number;
  question: string;
  answer: string;
  grounded: boolean;
  mode: string;
  citations: Citation[];
  feedback: number | null;
  created_at: string;
}

export interface Collection {
  name: string;
  documents: number;
}

export interface Stats {
  documents: number;
  chunks: number;
  collections: number;
  users: number;
  queries: number;
  grounded_rate: number;
  avg_retrieval_ms: number;
  avg_generation_ms: number;
  thumbs_up: number;
  thumbs_down: number;
}

export interface AskOptions {
  k: number;
  mode: SearchMode;
  collection?: string;
  use_mmr: boolean;
  use_rerank: boolean;
  previous_questions?: string[];
}
