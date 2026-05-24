import type {
  AiModel,
  AnonymizationSettings,
  ChatSummary,
  ChatThread,
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

  // Create one service instance bound to the frontend API base URL.
  constructor(private readonly apiBaseUrl: string = DEFAULT_API_BASE_URL) {
    this.httpClient = new ChatHttpClient(apiBaseUrl);
  }

  // Fetch the current model readiness status for the workspace.
  async getModelReadiness(): Promise<ModelReadinessStatus> {
    const payload = await this.httpClient.getJson<ModelReadinessResponse>(
      "/api/system/model-readiness",
    );
    return mapModelReadinessResponse(payload);
  }

  // Fetch the chat summaries shown in the sidebar.
  async listChats(): Promise<ChatSummary[]> {
    const payload = await this.httpClient.getJson<ChatSummaryResponse[]>(
      "/api/chats",
    );
    return payload.map(mapChatSummaryResponse);
  }

  // Create one new chat and return its backend identifier.
  async createChat(title: string | null = null): Promise<string> {
    const payload = await this.httpClient.postJson<CreateChatResponse>(
      "/api/chats",
      { title },
    );
    return payload.chat_id;
  }

  // Fetch one full chat thread with all of its messages.
  async loadChat(chatId: string): Promise<ChatThread> {
    const payload = await this.httpClient.getJson<ChatDetailResponse>(
      `/api/chats/${chatId}`,
    );
    return mapChatDetailResponse(payload);
  }

  // Rename one existing chat from the sidebar actions.
  async renameChat(chatId: string, title: string): Promise<void> {
    await this.httpClient.patchJson(`/api/chats/${chatId}`, { title });
  }

  // Delete one chat from the current collection.
  async deleteChat(chatId: string): Promise<void> {
    await this.httpClient.delete(`/api/chats/${chatId}`);
  }

  // Stream one normal chat response and forward each chunk to the UI.
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

  // Preview the anonymized version of one plain text message.
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

  // Preview the anonymized version of one processed document.
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

  // Open the anonymized PDF preview in a new browser tab.
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

  // Stream a response after the user approves one anonymized prompt.
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

  // Upload one document and report progress until the document ID arrives.
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

    throw new Error(
      "El procesamiento del documento finalizó sin un identificador.",
    );
  }

  // Stream the safe response generated from one attached document.
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

  // Consume one safe NDJSON stream and route each event to the right callback.
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

// Create the default chat service used by the workspace hooks.
export function createChatApplicationService(): ChatApplicationService {
  return new ChatApplicationService();
}
