export interface ChatAction {
  type: string;
  label: string;
  payload: Record<string, unknown>;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string | null;
}

export interface ChatResponse {
  response: string;
  recommendations: string[];
  actions: ChatAction[];
  conversation_id: string;
}

export interface ChatHistoryItem {
  id: string;
  conversation_id: string;
  user_message: string;
  assistant_message: string;
  recommendations: string[];
  actions: ChatAction[];
  created_at: string;
}

export interface ChatHistoryResponse {
  items: ChatHistoryItem[];
}
