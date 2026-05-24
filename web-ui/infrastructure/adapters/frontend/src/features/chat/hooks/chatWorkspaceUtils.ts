import type {
  ChatMessage,
  ChatSummary,
  ChatThread,
  ModelReadinessStatus,
} from "../types";

export const MODEL_READINESS_POLL_INTERVAL_MS = 3000;

export const INITIAL_MODEL_READINESS_STATUS: ModelReadinessStatus = {
  ready: false,
  message: "Comprobando si el modelo está cargado...",
};

// Normalize unknown failures into one user-facing error message.
export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Error inesperado.";
}

// Create the empty assistant message used as the initial stream target.
export function createAssistantMessage(): ChatMessage {
  return {
    id: `assistant-stream-${crypto.randomUUID()}`,
    role: "assistant",
    content: "",
    createdAt: "Ahora",
  };
}

// Create one local user message before it is sent to the backend.
export function createUserMessage(content: string): ChatMessage {
  return {
    id: `user-stream-${crypto.randomUUID()}`,
    role: "user",
    content,
    createdAt: "Ahora",
  };
}

// Create one empty chat shell before the full thread is loaded.
export function createEmptyChat(chatId: string): ChatThread {
  return {
    id: chatId,
    title: "Nuevo chat",
    lastMessagePreview: "",
    updatedAt: "Ahora",
    messages: [],
  };
}

// Build one sidebar summary from the current state of a full chat thread.
export function createChatSummary(chat: ChatThread): ChatSummary {
  return {
    id: chat.id,
    title: chat.title,
    lastMessagePreview: chat.messages[chat.messages.length - 1]?.content ?? "",
    updatedAt: chat.messages[chat.messages.length - 1]?.createdAt ?? "Ahora",
  };
}
