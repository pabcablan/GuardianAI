export type MessageRole = "user" | "assistant";

export const AI_MODEL_OPTIONS = [
  "gpt-5-nano",
  "gpt-4.1-nano",
  "gpt-5.4-nano",
  "gpt-5-mini",
  "gpt-4.1-mini",
  "gpt-5.4-mini",
 ] as const;

export type AiModel = (typeof AI_MODEL_OPTIONS)[number];

export const AI_MODEL_PRICING: Record<
  AiModel,
  { input: string; output: string }
> = {
  "gpt-5-nano": { input: "$0.05/1M", output: "$0.40/1M" },
  "gpt-4.1-nano": { input: "$0.10/1M", output: "$0.40/1M" },
  "gpt-5.4-nano": { input: "$0.20/1M", output: "$1.25/1M" },
  "gpt-5-mini": { input: "$0.25/1M", output: "$2.00/1M" },
  "gpt-4.1-mini": { input: "$0.40/1M", output: "$1.60/1M" },
  "gpt-5.4-mini": { input: "$0.75/1M", output: "$4.50/1M" },
};

export const DEFAULT_AI_MODEL: AiModel = "gpt-4.1-mini";

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
  replacementCount?: number;
  documentId?: string;
  extractionMethod?: string;
  originalContent?: string;
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
  | "licensePlates"
  | "organizations"
  | "relevantCodes";

export type AnonymizationMode = "anonymize" | "keep";

export type AnonymizationSettings = Record<
  AnonymizationOption,
  AnonymizationMode
>;
