/**
 * Knowledge / RAG feature — TypeScript type definitions.
 * Mirrors the backend Pydantic schemas in app/features/knowledge/schemas.py
 */

export type DocumentStatus = "uploaded" | "processing" | "ready" | "failed";

export interface Document {
  id: string;
  user_id: string;
  filename: string;
  original_filename: string;
  file_size: number;
  mime_type: string;
  status: DocumentStatus;
  chunk_count: number | null;
  error_message: string | null;
  storage_path: string | null;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  documents: Document[];
  total: number;
}

export interface DocumentStatusResponse {
  id: string;
  status: DocumentStatus;
  chunk_count: number | null;
  error_message: string | null;
  updated_at: string;
}

export interface UploadResponse {
  message: string;
  data: Document;
}
