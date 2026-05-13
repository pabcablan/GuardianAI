import type {
  AnonymizationSettings,
  ChatSummary,
  ChatThread,
  AiModel,
  DocumentProcessingStatus,
  ModelReadinessStatus,
} from "../types";
import {
  mapChatDetailResponse,
  mapChatSummaryResponse,
  mapModelReadinessResponse,
} from "./chatApiMappers";
import type {
  AnonymizedPreviewResponse,
  ChatDetailResponse,
  ChatSummaryResponse,
  CreateChatResponse,
  ModelReadinessResponse,
} from "./chatApiTypes";
import { ChatHttpClient } from "./chatHttpClient";
import {
  consumeNdjsonStream,
  handleDocumentStreamLine,
  handleSafeStreamLine,
} from "./chatStreamUtils";

const DEFAULT_API_BASE_URL = "http://127.0.0.1:8000";

export class ChatApplicationService {
  private readonly httpClient: ChatHttpClient;

  constructor(private readonly apiBaseUrl: string = DEFAULT_API_BASE_URL) {
    this.httpClient = new ChatHttpClient(apiBaseUrl);
  }

  async getModelReadiness(): Promise<ModelReadinessStatus> {
    const payload = await this.httpClient.getJson<ModelReadinessResponse>(
      "/api/system/model-readiness",
    );
    return mapModelReadinessResponse(payload);
  }

  async listChats(): Promise<ChatSummary[]> {
    const payload = await this.httpClient.getJson<ChatSummaryResponse[]>(
      "/api/chats",
    );
    return payload.map(mapChatSummaryResponse);
  }

  async createChat(title: string | null = null): Promise<string> {
    const payload = await this.httpClient.postJson<CreateChatResponse>(
      "/api/chats",
      { title },
    );
    return payload.chat_id;
  }

  async loadChat(chatId: string): Promise<ChatThread> {
    const payload = await this.httpClient.getJson<ChatDetailResponse>(
      `/api/chats/${chatId}`,
    );
    return mapChatDetailResponse(payload);
  }

  async renameChat(chatId: string, title: string): Promise<void> {
    await this.httpClient.patchJson(`/api/chats/${chatId}`, { title });
  }

  async deleteChat(chatId: string): Promise<void> {
    await this.httpClient.delete(`/api/chats/${chatId}`);
  }

  async streamMessage(
    chatId: string,
    content: string,
    model: AiModel,
    settings: AnonymizationSettings,
    onChunk: (chunk: string) => void,
    onAnonymizedPrompt: (content: string) => void,
  ): Promise<void> {
    const response = await this.httpClient.postJsonForResponse(
      `/api/chats/${chatId}/messages/stream`,
      { content, model, settings },
    );
    await this.consumeSafeStream(response, onChunk, onAnonymizedPrompt);
  }

  async previewMessageAnonymization(
    chatId: string,
    content: string,
    model: AiModel,
    settings: AnonymizationSettings,
  ): Promise<AnonymizedPreviewResponse> {
    return await this.httpClient.postJson<AnonymizedPreviewResponse>(
      `/api/chats/${chatId}/messages/anonymize-preview`,
      { content, model, settings },
    );
  }

  async previewDocumentAnonymization(
    chatId: string,
    documentId: string,
    settings: AnonymizationSettings,
  ): Promise<AnonymizedPreviewResponse> {
    return await this.httpClient.postJson<AnonymizedPreviewResponse>(
      `/api/chats/${chatId}/documents/${documentId}/anonymize-preview`,
      { settings },
    );
  }

  async openAnonymizedPdfPreview(
    chatId: string,
    documentId: string,
    anonymizationId: string,
  ): Promise<void> {
    const query = new URLSearchParams({ anonymization_id: anonymizationId });
    const blob = await this.httpClient.getBlob(
      `/api/chats/${chatId}/documents/${documentId}/anonymized-pdf-preview?${query.toString()}`,
    );
    const fileUrl = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = fileUrl;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.click();
    window.setTimeout(() => URL.revokeObjectURL(fileUrl), 60_000);
  }

  async streamApprovedAnonymizedResponse(
    chatId: string,
    anonymizedContent: string,
    anonymizationId: string,
    model: AiModel,
    onChunk: (chunk: string) => void,
  ): Promise<void> {
    const response = await this.httpClient.postJsonForResponse(
      `/api/chats/${chatId}/anonymized/stream`,
      {
        anonymized_content: anonymizedContent,
        anonymization_id: anonymizationId,
        model,
      },
    );
    await this.consumeSafeStream(response, onChunk);
  }

  async attachDocumentWithProgress(
    chatId: string,
    file: File,
    prompt: string,
    onProgress: (status: DocumentProcessingStatus) => void,
  ): Promise<string> {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("prompt", prompt);

    const response = await this.httpClient.postFormForResponse(
      `/api/chats/${chatId}/documents/stream`,
      formData,
    );

    let completedDocumentId: string | null = null;
    await consumeNdjsonStream(response, (rawLine) => {
      const documentId = handleDocumentStreamLine(
        rawLine,
        file.name,
        onProgress,
      );
      if (documentId) {
        completedDocumentId = documentId;
      }
    });

    if (completedDocumentId) {
      return completedDocumentId;
    }

    throw new Error("El procesamiento del documento finalizó sin un identificador.");
  }

  async streamSafeResponse(
    chatId: string,
    documentId: string,
    model: AiModel,
    settings: AnonymizationSettings,
    onChunk: (chunk: string) => void,
    onAnonymizedPrompt?: (content: string) => void,
  ): Promise<void> {
    const response = await this.httpClient.postJsonForResponse(
      `/api/chats/${chatId}/documents/${documentId}/safe-stream`,
      { model, settings },
    );
    await this.consumeSafeStream(response, onChunk, onAnonymizedPrompt);
  }

  private async consumeSafeStream(
    response: Response,
    onChunk: (chunk: string) => void,
    onAnonymizedPrompt?: (content: string) => void,
  ): Promise<void> {
    await consumeNdjsonStream(response, async (rawLine) => {
      await handleSafeStreamLine(rawLine, onChunk, onAnonymizedPrompt);
    });
  }
}

export function createChatApplicationService(): ChatApplicationService {
  return new ChatApplicationService();
}
