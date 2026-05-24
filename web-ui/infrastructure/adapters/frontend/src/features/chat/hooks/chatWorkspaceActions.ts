import type { ChatApplicationService } from "../application/chatApplicationService";
import type {
  AiModel,
  AnonymizationSettings,
  ChatMessage,
  DocumentProcessingStatus,
  ResponseProcessingStatus,
} from "../types";
import { createAssistantMessage, createUserMessage } from "./chatWorkspaceUtils";

interface CollectionActions {
  appendAssistantChunk: (chatId: string, messageId: string, chunk: string) => void;
  appendAssistantMessage: (chatId: string, message: ChatMessage) => void;
  appendChatMessage: (chatId: string, message: ChatMessage) => void;
  updateUserAnonymizedContent: (
    chatId: string,
    messageId: string,
    anonymizedContent: string,
    anonymizationId?: string,
    replacementCount?: number,
    documentId?: string,
    extractionMethod?: string,
    originalContent?: string,
  ) => void;
}

interface SendDocumentMessageArgs {
  actions: CollectionActions;
  activeChatId: string;
  model: AiModel;
  normalizedContent: string;
  pendingFile: File;
  service: ChatApplicationService;
  settings: AnonymizationSettings;
  setDocumentProcessingStatus: (
    status: DocumentProcessingStatus | null,
  ) => void;
  shouldPreviewAnonymizedText: boolean;
}

interface SendTextMessageArgs {
  actions: CollectionActions;
  activeChatId: string;
  model: AiModel;
  normalizedContent: string;
  service: ChatApplicationService;
  settings: AnonymizationSettings;
  setResponseProcessingStatus: (
    status: ResponseProcessingStatus | null,
  ) => void;
  shouldPreviewAnonymizedText: boolean;
}

// Set the temporary document progress status shown while processing an upload.
function setDocumentStatus(
  filename: string,
  current: number,
  setDocumentProcessingStatus: (
    status: DocumentProcessingStatus | null,
  ) => void,
) {
  setDocumentProcessingStatus({
    filename,
    stage: "Extrayendo texto",
    message: "Extrayendo texto",
    current,
    total: 1,
    progress: null,
  });
}

// Send one document message and drive either preview or safe-response streaming.
export async function sendDocumentMessage({
  actions,
  activeChatId,
  model,
  normalizedContent,
  pendingFile,
  service,
  settings,
  setDocumentProcessingStatus,
  shouldPreviewAnonymizedText,
}: SendDocumentMessageArgs): Promise<void> {
  const documentUserMessage = createUserMessage(
    normalizedContent || `Documento: ${pendingFile.name}`,
  );
  actions.appendChatMessage(activeChatId, documentUserMessage);

  setDocumentStatus(pendingFile.name, 0, setDocumentProcessingStatus);

  const documentId = await service.attachDocumentWithProgress(
    activeChatId,
    pendingFile,
    normalizedContent,
    (status) => {
      setDocumentProcessingStatus(status);
    },
  );

  setDocumentStatus(pendingFile.name, 1, setDocumentProcessingStatus);

  if (shouldPreviewAnonymizedText) {
    const preview = await service.previewDocumentAnonymization(
      activeChatId,
      documentId,
      settings,
    );
    actions.updateUserAnonymizedContent(
      activeChatId,
      documentUserMessage.id,
      preview.anonymized_content,
      preview.anonymization_id,
      preview.replacement_count,
      documentId,
      preview.extraction_method ?? undefined,
      preview.original_content ?? undefined,
    );
    setDocumentProcessingStatus(null);
    return;
  }

  const assistantMessage = createAssistantMessage();
  actions.appendAssistantMessage(activeChatId, assistantMessage);

  setDocumentStatus(pendingFile.name, 1, setDocumentProcessingStatus);

  let didReceiveFirstChunk = false;
  await service.streamSafeResponse(
    activeChatId,
    documentId,
    model,
    settings,
    (chunk) => {
      if (!didReceiveFirstChunk) {
        didReceiveFirstChunk = true;
        setDocumentProcessingStatus(null);
      }
      actions.appendAssistantChunk(activeChatId, assistantMessage.id, chunk);
    },
    (anonymizedContent) => {
      setDocumentProcessingStatus(null);
      actions.updateUserAnonymizedContent(
        activeChatId,
        documentUserMessage.id,
        anonymizedContent,
        undefined,
      );
    },
  );
}

// Send one text message and drive either preview or safe-response streaming.
export async function sendTextMessage({
  actions,
  activeChatId,
  model,
  normalizedContent,
  service,
  settings,
  setResponseProcessingStatus,
  shouldPreviewAnonymizedText,
}: SendTextMessageArgs): Promise<void> {
  const userMessage = createUserMessage(normalizedContent);
  actions.appendChatMessage(activeChatId, userMessage);

  if (shouldPreviewAnonymizedText) {
    setResponseProcessingStatus({
      title: "Mensaje del chat",
      stage: "Anonimizando",
      message: "Anonimizando",
    });
    const preview = await service.previewMessageAnonymization(
      activeChatId,
      normalizedContent,
      model,
      settings,
    );
    actions.updateUserAnonymizedContent(
      activeChatId,
      userMessage.id,
      preview.anonymized_content,
      preview.anonymization_id,
      preview.replacement_count,
    );
    setResponseProcessingStatus(null);
    return;
  }

  const assistantMessage = createAssistantMessage();
  actions.appendChatMessage(activeChatId, assistantMessage);

  setResponseProcessingStatus({
    title: "Mensaje del chat",
    stage: "Anonimizando",
    message: "Anonimizando",
  });

  let didReceiveFirstChunk = false;
  await service.streamMessage(
    activeChatId,
    normalizedContent,
    model,
    settings,
    (chunk) => {
      if (!didReceiveFirstChunk) {
        didReceiveFirstChunk = true;
        setResponseProcessingStatus(null);
      }
      actions.appendAssistantChunk(activeChatId, assistantMessage.id, chunk);
    },
    (anonymizedContent) => {
      setResponseProcessingStatus(null);
      actions.updateUserAnonymizedContent(
        activeChatId,
        userMessage.id,
        anonymizedContent,
        undefined,
      );
    },
  );
}
