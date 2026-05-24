// Response payload returned after creating one chat.
export interface CreateChatResponse {
  chat_id: string;
  title: string;
}

// Response payload used to render one chat row in the sidebar.
export interface ChatSummaryResponse {
  chat_id: string;
  title: string;
  last_message_preview: string;
  updated_at: string;
}

// Response payload for one persisted chat message.
export interface ChatMessageResponse {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  anonymized_content?: string | null;
  created_at: string;
}

// Response payload for one full chat thread.
export interface ChatDetailResponse {
  chat_id: string;
  title: string;
  messages: ChatMessageResponse[];
}

// Response payload for one anonymization preview request.
export interface AnonymizedPreviewResponse {
  message_id: string;
  anonymized_content: string;
  anonymization_id: string;
  replacement_count: number;
  extraction_method?: string | null;
  original_content?: string | null;
}

// Stream event emitted while one document is being processed.
export interface AttachDocumentProgressResponse {
  event: "progress";
  stage: string;
  current: number;
  total: number;
  message: string;
}

// Stream event emitted when one document finishes processing.
export interface AttachDocumentCompletedResponse {
  event: "completed";
  document_id: string;
  filename: string;
}

// Stream event emitted when document processing fails.
export interface AttachDocumentErrorResponse {
  event: "error";
  detail: string;
}

// All stream events that can arrive while attaching one document.
export type AttachDocumentStreamResponse =
  | AttachDocumentProgressResponse
  | AttachDocumentCompletedResponse
  | AttachDocumentErrorResponse;

// Stream event emitted for one assistant text chunk.
export interface SafeStreamChunkResponse {
  event: "chunk";
  content: string;
}

// Stream event emitted for the anonymized version of one prompt.
export interface SafeStreamAnonymizedPromptResponse {
  event: "anonymized_prompt";
  content: string;
}

// Stream event emitted when one safe response finishes.
export interface SafeStreamCompletedResponse {
  event: "completed";
}

// Stream event emitted when one safe response fails.
export interface SafeStreamErrorResponse {
  event: "error";
  detail: string;
}

// All stream events that can arrive from one safe response.
export type SafeStreamResponse =
  | SafeStreamChunkResponse
  | SafeStreamAnonymizedPromptResponse
  | SafeStreamCompletedResponse
  | SafeStreamErrorResponse;

// Response payload for the backend model readiness check.
export interface ModelReadinessResponse {
  ready: boolean;
  message: string;
}
