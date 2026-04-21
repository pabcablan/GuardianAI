import type { ChatSummary, ChatThread } from "../types";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

interface CreateChatResponse {
  chat_id: string;
  title: string;
}

interface ChatSummaryResponse {
  chat_id: string;
  title: string;
  last_message_preview: string;
  updated_at: string;
}

interface ChatMessageResponse {
  message_id: string;
  role: "user" | "assistant";
  content: string;
  created_at: string;
}

interface ChatDetailResponse {
  chat_id: string;
  title: string;
  messages: ChatMessageResponse[];
}

export class ChatApplicationService {
  constructor(private readonly apiBaseUrl: string = DEFAULT_API_BASE_URL) {}

  async listChats(): Promise<ChatSummary[]> {
    const response = await fetch(`${this.apiBaseUrl}/api/chats`);
    await this.ensure_success(response);

    const payload = (await response.json()) as ChatSummaryResponse[];
    return payload.map((chat) => ({
      id: chat.chat_id,
      title: chat.title,
      lastMessagePreview: chat.last_message_preview,
      updatedAt: chat.updated_at,
    }));
  }

  async createChat(title: string | null = null): Promise<string> {
    const response = await fetch(`${this.apiBaseUrl}/api/chats`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ title }),
    });
    await this.ensure_success(response);

    const payload = (await response.json()) as CreateChatResponse;
    return payload.chat_id;
  }

  async loadChat(chatId: string): Promise<ChatThread> {
    const response = await fetch(`${this.apiBaseUrl}/api/chats/${chatId}`);
    await this.ensure_success(response);

    const payload = (await response.json()) as ChatDetailResponse;
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
        createdAt: message.created_at,
      })),
    };
  }

  async sendMessage(chatId: string, content: string): Promise<void> {
    const response = await fetch(`${this.apiBaseUrl}/api/chats/${chatId}/messages`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ content }),
    });
    await this.ensure_success(response);
  }

  async attachDocument(chatId: string, file: File): Promise<void> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.apiBaseUrl}/api/chats/${chatId}/documents`, {
      method: "POST",
      body: formData,
    });
    await this.ensure_success(response);
  }

  private async ensure_success(response: Response): Promise<void> {
    if (response.ok) {
      return;
    }

    const fallbackMessage = `Request failed with status ${response.status}.`;
    let detailMessage = fallbackMessage;

    try {
      const payload = (await response.json()) as { detail?: string };
      detailMessage = payload.detail ?? fallbackMessage;
    } catch {
      detailMessage = fallbackMessage;
    }

    throw new Error(detailMessage);
  }
}

export function createChatApplicationService(): ChatApplicationService {
  return new ChatApplicationService();
}
