import { useRef, useState } from "react";

import { createChatApplicationService } from "../application/chatApplicationService";
import { DEFAULT_AI_MODEL } from "../types";
import type {
  AnonymizationSettings,
  ChatMessage,
  AiModel,
  DocumentProcessingStatus,
  ResponseProcessingStatus,
} from "../types";
import {
  createAssistantMessage,
  createUserMessage,
  getErrorMessage,
} from "./chatWorkspaceUtils";
import { useChatCollection } from "./useChatCollection";
import { useModelReadiness } from "./useModelReadiness";

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

  async function createChat(): Promise<void> {
    await createChatInternal();
  }

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

      if (pendingFile) {
        const documentUserMessage = createUserMessage(
          normalizedContent || `Documento: ${pendingFile.name}`,
        );
        appendChatMessage(activeChatId, documentUserMessage);

        setDocumentProcessingStatus({
          filename: pendingFile.name,
          stage: "Subiendo documento",
          message: "Subiendo PDF al backend...",
          current: 0,
          total: 1,
          progress: null,
        });

        const documentId = await serviceRef.current.attachDocumentWithProgress(
          activeChatId,
          pendingFile,
          normalizedContent,
          (status) => {
            setDocumentProcessingStatus(status);
          },
        );

        setDocumentProcessingStatus({
          filename: pendingFile.name,
          stage: "Evaluando privacidad",
          message:
            "Comprobando si el contenido del documento necesita anonimizarse...",
          current: 1,
          total: 1,
          progress: null,
        });

        if (shouldPreviewAnonymizedText) {
          const preview =
            await serviceRef.current.previewDocumentAnonymization(
              activeChatId,
              documentId,
              settings,
            );
          updateUserAnonymizedContent(
            activeChatId,
            documentUserMessage.id,
            preview.anonymized_content,
            preview.anonymization_id,
            preview.replacement_count,
            documentId,
            preview.extraction_method ?? undefined,
          );
          setDocumentProcessingStatus(null);
          return true;
        }

        const assistantMessage = createAssistantMessage();
        appendAssistantMessage(activeChatId, assistantMessage);

        setDocumentProcessingStatus({
          filename: pendingFile.name,
          stage: "Evaluando privacidad",
          message:
            "Comprobando si el contenido del documento necesita anonimizarse...",
          current: 1,
          total: 1,
          progress: null,
        });

        let didReceiveFirstChunk = false;
        await serviceRef.current.streamSafeResponse(
          activeChatId,
          documentId,
          model,
          settings,
          (chunk) => {
            if (!didReceiveFirstChunk) {
              didReceiveFirstChunk = true;
              setDocumentProcessingStatus({
                filename: pendingFile.name,
                stage: "Desanonimizando respuesta",
                message:
                  "Restaurando los campos protegidos en la respuesta...",
                current: 1,
                total: 1,
                progress: null,
              });
              window.setTimeout(() => {
                setDocumentProcessingStatus(null);
              }, 600);
            }
            appendAssistantChunk(activeChatId, assistantMessage.id, chunk);
          },
          (anonymizedContent) => {
            setDocumentProcessingStatus({
              filename: pendingFile.name,
              stage: "Consultando IA",
              message:
                "Contenido anonimizado. Enviando la consulta al asistente...",
              current: 1,
              total: 1,
              progress: null,
            });
            updateUserAnonymizedContent(
              activeChatId,
              documentUserMessage.id,
              anonymizedContent,
              undefined,
            );
          },
        );
      }

      if (!pendingFile) {
        const userMessage = createUserMessage(normalizedContent);
        appendChatMessage(activeChatId, userMessage);

        if (shouldPreviewAnonymizedText) {
          setResponseProcessingStatus({
            title: "Mensaje del chat",
            stage: "Evaluando privacidad",
            message: "Comprobando si el mensaje necesita anonimizarse...",
          });
          const preview = await serviceRef.current.previewMessageAnonymization(
            activeChatId,
            normalizedContent,
            model,
            settings,
          );
          updateUserAnonymizedContent(
            activeChatId,
            userMessage.id,
            preview.anonymized_content,
            preview.anonymization_id,
            preview.replacement_count,
          );
          setResponseProcessingStatus(null);
          return true;
        }

        const assistantMessage = createAssistantMessage();
        appendChatMessage(activeChatId, assistantMessage);

        setResponseProcessingStatus({
          title: "Mensaje del chat",
          stage: "Evaluando privacidad",
          message: "Comprobando si el mensaje necesita anonimizarse...",
        });

        let didReceiveFirstChunk = false;
        await serviceRef.current.streamMessage(
          activeChatId,
          normalizedContent,
          model,
          settings,
          (chunk) => {
            if (!didReceiveFirstChunk) {
              didReceiveFirstChunk = true;
              setResponseProcessingStatus({
                title: "Respuesta del asistente",
                stage: "Desanonimizando respuesta",
                message:
                  "Restaurando los campos protegidos en la respuesta...",
              });
              window.setTimeout(() => {
                setResponseProcessingStatus(null);
              }, 600);
            }
            appendAssistantChunk(activeChatId, assistantMessage.id, chunk);
          },
          (anonymizedContent) => {
            setResponseProcessingStatus({
              title: "Mensaje del chat",
              stage: "Consultando IA",
              message:
                "Mensaje anonimizado. Enviando la consulta al asistente...",
            });
            updateUserAnonymizedContent(
              activeChatId,
              userMessage.id,
              anonymizedContent,
              undefined,
            );
          },
        );
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

  async function approveAnonymizedMessage(
    message: ChatMessage,
    model: AiModel,
  ): Promise<void> {
    if (!selectedChatId || !message.pendingApproval) {
      return;
    }

    setIsResponding(true);
    setErrorMessage(null);
    setResponseProcessingStatus({
      title: "Texto anonimizado",
      stage: "Consultando IA",
      message: "Enviando el texto anonimizado al asistente...",
    });
    clearMessageApproval(selectedChatId, message.id);

    const assistantMessage = createAssistantMessage();
    appendChatMessage(selectedChatId, assistantMessage);

    try {
      let didReceiveFirstChunk = false;
      await serviceRef.current.streamApprovedAnonymizedResponse(
        selectedChatId,
        message.pendingApproval.anonymizedContent,
        message.pendingApproval.anonymizationId,
        model,
        (chunk) => {
          if (!didReceiveFirstChunk) {
            didReceiveFirstChunk = true;
            setResponseProcessingStatus({
              title: "Respuesta del asistente",
              stage: "Desanonimizando respuesta",
              message:
                "Restaurando los campos protegidos en la respuesta...",
            });
            window.setTimeout(() => {
              setResponseProcessingStatus(null);
            }, 600);
          }
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
    isInteractionLocked:
      !modelReadiness.ready || isResponding || documentProcessingStatus !== null,
    selectChat,
    createChat,
    renameChat,
    deleteChat,
    sendMessage,
    approveAnonymizedMessage,
    openAnonymizedPdfPreview,
  };
}
