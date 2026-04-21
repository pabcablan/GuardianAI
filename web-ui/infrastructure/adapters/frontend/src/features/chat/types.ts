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
