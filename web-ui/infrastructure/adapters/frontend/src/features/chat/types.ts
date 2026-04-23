export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  createdAt: string;
}

export interface ChatSummary {
  id: string;
  title: string;
  lastMessagePreview: string;
  updatedAt: string;
}

export interface ChatThread extends ChatSummary {
  messages: ChatMessage[];
}

export interface DocumentProcessingStatus {
  filename: string;
  stage: string;
  message: string;
  current: number;
  total: number;
  progress: number | null;
}

export type AnonymizationOption =
  | "personNames"
  | "identityDocuments"
  | "emails"
  | "addresses"
  | "phones"
  | "organizations"
  | "relevantCodes";

export type AnonymizationMode = "anonymize" | "keep";

export type AnonymizationSettings = Record<
  AnonymizationOption,
  AnonymizationMode
>;
