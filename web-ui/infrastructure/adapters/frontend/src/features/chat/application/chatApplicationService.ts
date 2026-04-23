import type {
  ChatSummary,
  ChatThread,
  DocumentProcessingStatus,
} from "../types";

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

interface AttachDocumentProgressResponse {
  event: "progress";
  stage: string;
  current: number;
  total: number;
  message: string;
}

interface AttachDocumentCompletedResponse {
  event: "completed";
  document_id: string;
  filename: string;
}

interface AttachDocumentErrorResponse {
  event: "error";
  detail: string;
}

type AttachDocumentStreamResponse =
  | AttachDocumentProgressResponse
  | AttachDocumentCompletedResponse
  | AttachDocumentErrorResponse;

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

  async attachDocumentWithProgress(
    chatId: string,
    file: File,
    onProgress: (status: DocumentProcessingStatus) => void,
  ): Promise<void> {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch(`${this.apiBaseUrl}/api/chats/${chatId}/documents/stream`, {
      method: "POST",
      body: formData,
    });
    await this.ensure_success(response);

    if (!response.body) {
      throw new Error("Document progress stream is unavailable.");
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder("utf-8");
    let buffer = "";

    while (true) {
      const { value, done } = await reader.read();
      buffer += decoder.decode(value, { stream: !done });

      let lineBreakIndex = buffer.indexOf("\n");
      while (lineBreakIndex >= 0) {
        const rawLine = buffer.slice(0, lineBreakIndex).trim();
        buffer = buffer.slice(lineBreakIndex + 1);

        if (rawLine) {
          this.handleDocumentStreamLine(rawLine, file.name, onProgress);
        }

        lineBreakIndex = buffer.indexOf("\n");
      }

      if (done) {
        break;
      }
    }

    const lastLine = buffer.trim();
    if (lastLine) {
      this.handleDocumentStreamLine(lastLine, file.name, onProgress);
    }
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

  private handleDocumentStreamLine(
    rawLine: string,
    filename: string,
    onProgress: (status: DocumentProcessingStatus) => void,
  ): void {
    const payload = JSON.parse(rawLine) as AttachDocumentStreamResponse;

    if (payload.event === "progress") {
      const progress =
        payload.total > 0
          ? Math.max(0, Math.min(1, payload.current / payload.total))
          : null;

      onProgress({
        filename,
        stage: payload.stage,
        message: payload.message,
        current: payload.current,
        total: payload.total,
        progress,
      });
      return;
    }

    if (payload.event === "error") {
      throw new Error(payload.detail);
    }
  }
}

export function createChatApplicationService(): ChatApplicationService {
  return new ChatApplicationService();
}
