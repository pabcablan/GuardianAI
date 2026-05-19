export interface CreateChatResponse {
  chat_id: string;
  title: string;
}

export interface ChatSummaryResponse {
  chat_id: string;
  title: string;
  last_message_preview: string;
  updated_at: string;
}

export interface ChatMessageResponse {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  anonymized_content?: string | null;
  created_at: string;
}

export interface ChatDetailResponse {
  chat_id: string;
  title: string;
  messages: ChatMessageResponse[];
}

export interface AnonymizedPreviewResponse {
  message_id: string;
  anonymized_content: string;
  anonymization_id: string;
  replacement_count: number;
  extraction_method?: string | null;
  original_content?: string | null;
}

export interface AttachDocumentProgressResponse {
  event: "progress";
  stage: string;
  current: number;
  total: number;
  message: string;
}

export interface AttachDocumentCompletedResponse {
  event: "completed";
  document_id: string;
  filename: string;
}

export interface AttachDocumentErrorResponse {
  event: "error";
  detail: string;
}

export type AttachDocumentStreamResponse =
  | AttachDocumentProgressResponse
  | AttachDocumentCompletedResponse
  | AttachDocumentErrorResponse;

export interface SafeStreamChunkResponse {
  event: "chunk";
  content: string;
}

export interface SafeStreamAnonymizedPromptResponse {
  event: "anonymized_prompt";
  content: string;
}

export interface SafeStreamCompletedResponse {
  event: "completed";
}

export interface SafeStreamErrorResponse {
  event: "error";
  detail: string;
}

export type SafeStreamResponse =
  | SafeStreamChunkResponse
  | SafeStreamAnonymizedPromptResponse
  | SafeStreamCompletedResponse
  | SafeStreamErrorResponse;

export interface ModelReadinessResponse {
  ready: boolean;
  message: string;
}
