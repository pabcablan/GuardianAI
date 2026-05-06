export type MessageRole = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  anonymizedContent?: string;
  pendingApproval?: AnonymizedContentApproval;
  createdAt: string;
}

export interface AnonymizedContentApproval {
  anonymizationId: string;
  anonymizedContent: string;
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

export interface ModelReadinessStatus {
  ready: boolean;
  message: string;
}

export interface ResponseProcessingStatus {
  title: string;
  stage: string;
  message: string;
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
