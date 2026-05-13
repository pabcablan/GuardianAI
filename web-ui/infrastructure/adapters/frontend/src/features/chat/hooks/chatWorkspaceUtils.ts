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

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Error inesperado.";
}

export function createAssistantMessage(): ChatMessage {
  return {
    id: `assistant-stream-${crypto.randomUUID()}`,
    role: "assistant",
    content: "",
    createdAt: "Ahora",
  };
}

export function createUserMessage(content: string): ChatMessage {
  return {
    id: `user-stream-${crypto.randomUUID()}`,
    role: "user",
    content,
    createdAt: "Ahora",
  };
}

export function createEmptyChat(chatId: string): ChatThread {
  return {
    id: chatId,
    title: "Nuevo chat",
    lastMessagePreview: "",
    updatedAt: "Ahora",
    messages: [],
  };
}

export function createChatSummary(chat: ChatThread): ChatSummary {
  return {
    id: chat.id,
    title: chat.title,
    lastMessagePreview: chat.messages[chat.messages.length - 1]?.content ?? "",
    updatedAt: chat.messages[chat.messages.length - 1]?.createdAt ?? "Ahora",
  };
}
