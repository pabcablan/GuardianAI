import { useRef, useState } from "react";

import { createChatApplicationService } from "../application/chatApplicationService";
import { DEFAULT_AI_MODEL } from "../types";
import type {
  AiModel,
  AnonymizationSettings,
  ChatMessage,
  DocumentProcessingStatus,
  ResponseProcessingStatus,
} from "../types";
import { createAssistantMessage, getErrorMessage } from "./chatWorkspaceUtils";
import {
  sendDocumentMessage,
  sendTextMessage,
} from "./chatWorkspaceActions";
import { useChatCollection } from "./useChatCollection";
import { useModelReadiness } from "./useModelReadiness";

// Orchestrate the full chat workspace state and high-level user actions.
export function useChatWorkspace() {
  const serviceRef = useRef(createChatApplicationService());
  const [isResponding, setIsResponding] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [documentProcessingStatus, setDocumentProcessingStatus] =
    useState<DocumentProcessingStatus | null>(null);
  const [responseProcessingStatus, setResponseProcessingStatus] =
    useState<ResponseProcessingStatus | null>(null);

  const modelReadiness = useModelReadiness(serviceRef.current);
  const {
    chats,
    selectedChat,
    selectedChatId,
    isLoadingChats,
    appendAssistantMessage,
    appendChatMessage,
    appendAssistantChunk,
    updateUserAnonymizedContent,
    clearMessageApproval,
    selectChat,
    createChat: createChatInternal,
    ensureActiveChat,
    renameChat,
    deleteChat,
  } = useChatCollection({
    service: serviceRef.current,
    onError: setErrorMessage,
  });
  const isSendLocked =
    !modelReadiness.ready || isResponding || documentProcessingStatus !== null;

  // Create a new chat from the workspace toolbar or sidebar.
  async function createChat(): Promise<void> {
    await createChatInternal();
  }

  // Send one text message or one document through the main chat workflow.
  async function sendMessage(
    content: string,
    pendingFile: File | null = null,
    shouldPreviewAnonymizedText = false,
    model: AiModel = DEFAULT_AI_MODEL,
    settings: AnonymizationSettings,
  ): Promise<boolean> {
    const normalizedContent = content.trim();
    if (!normalizedContent && !pendingFile) {
      return false;
    }

    setIsResponding(true);
    setErrorMessage(null);

    try {
      const activeChatId = await ensureActiveChat();

      if (!activeChatId) {
        throw new Error("No hay ningún chat activo disponible.");
      }

      const actions = {
        appendAssistantChunk,
        appendAssistantMessage,
        appendChatMessage,
        updateUserAnonymizedContent,
      };

      if (pendingFile) {
        await sendDocumentMessage({
          actions,
          activeChatId,
          model,
          normalizedContent,
          pendingFile,
          service: serviceRef.current,
          settings,
          setDocumentProcessingStatus,
          shouldPreviewAnonymizedText,
        });
      } else {
        await sendTextMessage({
          actions,
          activeChatId,
          model,
          normalizedContent,
          service: serviceRef.current,
          settings,
          setResponseProcessingStatus,
          shouldPreviewAnonymizedText,
        });
      }

      setDocumentProcessingStatus(null);
      setResponseProcessingStatus(null);
      return true;
    } catch (error) {
      setDocumentProcessingStatus(null);
      setResponseProcessingStatus(null);
      setErrorMessage(getErrorMessage(error));
      return false;
    } finally {
      setIsResponding(false);
    }
  }

  // Continue the chat after the user approves one anonymized message preview.
  async function approveAnonymizedMessage(
    message: ChatMessage,
    model: AiModel,
  ): Promise<void> {
    if (!selectedChatId || !message.pendingApproval) {
      return;
    }

    setIsResponding(true);
    setErrorMessage(null);
    setResponseProcessingStatus(null);
    clearMessageApproval(selectedChatId, message.id);

    const assistantMessage = createAssistantMessage();
    appendChatMessage(selectedChatId, assistantMessage);

    try {
      await serviceRef.current.streamApprovedAnonymizedResponse(
        selectedChatId,
        message.pendingApproval.anonymizedContent,
        message.pendingApproval.anonymizationId,
        model,
        (chunk) => {
          appendAssistantChunk(selectedChatId, assistantMessage.id, chunk);
        },
      );
      setResponseProcessingStatus(null);
    } catch (error) {
      setResponseProcessingStatus(null);
      setErrorMessage(getErrorMessage(error));
    } finally {
      setIsResponding(false);
    }
  }

  // Open the anonymized PDF preview linked to one pending document message.
  async function openAnonymizedPdfPreview(message: ChatMessage): Promise<void> {
    if (!selectedChatId || !message.pendingApproval?.documentId) {
      return;
    }

    setErrorMessage(null);

    try {
      await serviceRef.current.openAnonymizedPdfPreview(
        selectedChatId,
        message.pendingApproval.documentId,
        message.pendingApproval.anonymizationId,
      );
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    }
  }

  return {
    chats,
    selectedChat,
    selectedChatId,
    errorMessage,
    isLoadingChats,
    isResponding,
    documentProcessingStatus,
    responseProcessingStatus,
    modelReadiness,
    isSendLocked,
    selectChat,
    createChat,
    renameChat,
    deleteChat,
    sendMessage,
    approveAnonymizedMessage,
    openAnonymizedPdfPreview,
  };
}
