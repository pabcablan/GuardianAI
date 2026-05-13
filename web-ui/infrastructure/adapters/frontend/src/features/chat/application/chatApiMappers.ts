import type { ChatSummary, ChatThread, ModelReadinessStatus } from "../types";
import type {
  ChatDetailResponse,
  ChatSummaryResponse,
  ModelReadinessResponse,
} from "./chatApiTypes";

export function mapModelReadinessResponse(
  payload: ModelReadinessResponse,
): ModelReadinessStatus {
  return {
    ready: payload.ready,
    message: payload.message,
  };
}

export function mapChatSummaryResponse(
  chat: ChatSummaryResponse,
): ChatSummary {
  return {
    id: chat.chat_id,
    title: chat.title,
    lastMessagePreview: chat.last_message_preview,
    updatedAt: chat.updated_at,
  };
}

export function mapChatDetailResponse(payload: ChatDetailResponse): ChatThread {
  return {
    id: payload.chat_id,
    title: payload.title,
    lastMessagePreview:
      payload.messages[payload.messages.length - 1]?.content ?? "",
    updatedAt:
      payload.messages[payload.messages.length - 1]?.created_at ?? "Ahora",
    messages: payload.messages.map((message) => ({
      id: message.message_id,
      role: message.role,
      content: message.content,
      anonymizedContent: message.anonymized_content ?? undefined,
      createdAt: message.created_at,
    })),
  };
}
