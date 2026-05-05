import { useEffect, useRef, useState } from "react";

import { createChatApplicationService } from "../application/chatApplicationService";
import type {
  ChatMessage,
  ChatSummary,
  ChatThread,
  DocumentProcessingStatus,
  ModelReadinessStatus,
  ResponseProcessingStatus,
} from "../types";


function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected error.";
}


function createAssistantMessage(): ChatMessage {
  return {
    id: `assistant-stream-${crypto.randomUUID()}`,
    role: "assistant",
    content: "",
    createdAt: "Ahora",
  };
}


function createUserMessage(content: string): ChatMessage {
  return {
    id: `user-stream-${crypto.randomUUID()}`,
    role: "user",
    content,
    createdAt: "Ahora",
  };
}


function createEmptyChat(chatId: string): ChatThread {
  return {
    id: chatId,
    title: "Nuevo chat",
    lastMessagePreview: "",
    updatedAt: "Ahora",
    messages: [],
  };
}


const MODEL_READINESS_POLL_INTERVAL_MS = 3000;


export function useChatWorkspace() {
  const serviceRef = useRef(createChatApplicationService());
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [selectedChatId, setSelectedChatId] = useState("");
  const [selectedChat, setSelectedChat] = useState<ChatThread | null>(null);
  const [isResponding, setIsResponding] = useState(false);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [documentProcessingStatus, setDocumentProcessingStatus] =
    useState<DocumentProcessingStatus | null>(null);
  const [responseProcessingStatus, setResponseProcessingStatus] =
    useState<ResponseProcessingStatus | null>(null);
  const [modelReadiness, setModelReadiness] = useState<ModelReadinessStatus>({
    ready: false,
    message: "Comprobando si el modelo esta cargado...",
  });

  useEffect(() => {
    void loadChats();
  }, []);

  useEffect(() => {
    let isActive = true;
    let timeoutId: number | null = null;

    async function refreshModelReadiness(): Promise<void> {
      try {
        const readiness = await serviceRef.current.getModelReadiness();
        if (!isActive) {
          return;
        }

        setModelReadiness(readiness);

        if (!readiness.ready) {
          timeoutId = window.setTimeout(
            refreshModelReadiness,
            MODEL_READINESS_POLL_INTERVAL_MS,
          );
        }
      } catch {
        if (!isActive) {
          return;
        }

        setModelReadiness({
          ready: false,
          message: "Esperando a que arranque el proveedor de modelos...",
        });
        timeoutId = window.setTimeout(
          refreshModelReadiness,
          MODEL_READINESS_POLL_INTERVAL_MS,
        );
      }
    }

    void refreshModelReadiness();

    return () => {
      isActive = false;
      if (timeoutId !== null) {
        window.clearTimeout(timeoutId);
      }
    };
  }, []);

  useEffect(() => {
    if (!selectedChatId) {
      setSelectedChat(null);
      return;
    }

    void loadChatDetail(selectedChatId);
  }, [selectedChatId]);

  async function loadChats(preferredChatId?: string): Promise<string | null> {
    setIsLoadingChats(true);
    setErrorMessage(null);

    try {
      const summaries = await serviceRef.current.listChats();
      setChats(summaries);

      if (!summaries.length) {
        return null;
      }

      const nextSelectedChatId =
        (preferredChatId ?? selectedChatId) || summaries[0].id;

      if (nextSelectedChatId !== selectedChatId) {
        setSelectedChatId(nextSelectedChatId);
      }

      return nextSelectedChatId;
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      return null;
    } finally {
      setIsLoadingChats(false);
    }
  }

  async function loadChatDetail(chatId: string): Promise<void> {
    setErrorMessage(null);

    try {
      const chat = await serviceRef.current.loadChat(chatId);
      setSelectedChat(chat);
      syncChatSummary(chat);
    } catch (error) {
      setSelectedChat(null);
      setErrorMessage(getErrorMessage(error));
    }
  }

  function syncChatSummary(chat: ChatThread): void {
    setChats((currentChats) => {
      const nextSummary: ChatSummary = {
        id: chat.id,
        title: chat.title,
        lastMessagePreview:
          chat.messages[chat.messages.length - 1]?.content ?? "",
        updatedAt:
          chat.messages[chat.messages.length - 1]?.createdAt ?? "Ahora",
      };

      const currentIndex = currentChats.findIndex(
        (currentChat) => currentChat.id === chat.id,
      );

      if (currentIndex === -1) {
        return [nextSummary, ...currentChats];
      }

      const nextChats = [...currentChats];
      nextChats[currentIndex] = nextSummary;
      return nextChats;
    });
  }

  function appendAssistantMessage(chatId: string, message: ChatMessage): void {
    setChats((currentChats) =>
      currentChats.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              lastMessagePreview: message.content,
              updatedAt: message.createdAt,
            }
          : chat,
      ),
    );

    setSelectedChat((currentChat) => {
      const targetChat = currentChat?.id === chatId
        ? currentChat
        : createEmptyChat(chatId);

      if (targetChat.id !== chatId) {
        return currentChat;
      }

      return {
        ...targetChat,
        lastMessagePreview: message.content,
        updatedAt: message.createdAt,
        messages: [...targetChat.messages, message],
      };
    });
  }

  function appendChatMessage(chatId: string, message: ChatMessage): void {
    setChats((currentChats) =>
      currentChats.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              lastMessagePreview: message.content,
              updatedAt: message.createdAt,
            }
          : chat,
      ),
    );

    setSelectedChat((currentChat) => {
      const targetChat = currentChat?.id === chatId
        ? currentChat
        : createEmptyChat(chatId);

      return {
        ...targetChat,
        lastMessagePreview: message.content,
        updatedAt: message.createdAt,
        messages: [...targetChat.messages, message],
      };
    });
  }

  function appendAssistantChunk(
    chatId: string,
    messageId: string,
    chunk: string,
  ): void {
    setChats((currentChats) =>
      currentChats.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              lastMessagePreview: `${chat.lastMessagePreview}${chunk}`,
              updatedAt: "Ahora",
            }
          : chat,
      ),
    );

    setSelectedChat((currentChat) => {
      if (!currentChat || currentChat.id !== chatId) {
        return currentChat;
      }

      const messages = currentChat.messages.map((message) => {
        if (message.id !== messageId) {
          return message;
        }

        return {
          ...message,
          content: `${message.content}${chunk}`,
        };
      });
      const streamedMessage = messages.find(
        (message) => message.id === messageId,
      );

      const nextPreview = streamedMessage?.content ?? currentChat.lastMessagePreview;

      return {
        ...currentChat,
        lastMessagePreview: nextPreview,
        updatedAt: "Ahora",
        messages,
      };
    });
  }

  function selectChat(chatId: string): void {
    setSelectedChatId(chatId);
  }

  async function createChat(): Promise<void> {
    setErrorMessage(null);

    try {
      const chatId = await serviceRef.current.createChat();
      await loadChats(chatId);
      setSelectedChatId(chatId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
    }
  }

  async function renameChat(chatId: string, title: string): Promise<boolean> {
    const normalizedTitle = title.trim();
    if (!normalizedTitle) {
      setErrorMessage("El nombre del chat no puede estar vacio.");
      return false;
    }

    setErrorMessage(null);

    try {
      await serviceRef.current.renameChat(chatId, normalizedTitle);

      setChats((currentChats) =>
        currentChats.map((chat) =>
          chat.id === chatId
            ? {
                ...chat,
                title: normalizedTitle,
              }
            : chat,
        ),
      );

      setSelectedChat((currentChat) =>
        currentChat?.id === chatId
          ? {
              ...currentChat,
              title: normalizedTitle,
            }
          : currentChat,
      );

      return true;
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      return false;
    }
  }

  async function deleteChat(chatId: string): Promise<boolean> {
    setErrorMessage(null);

    try {
      await serviceRef.current.deleteChat(chatId);

      const remainingChats = chats.filter((chat) => chat.id !== chatId);
      setChats(remainingChats);

      if (selectedChatId === chatId) {
        const nextChatId = remainingChats[0]?.id ?? "";
        setSelectedChatId(nextChatId);

        if (!nextChatId) {
          setSelectedChat(null);
        }
      }

      return true;
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
      return false;
    }
  }

  async function sendMessage(
    content: string,
    pendingFile: File | null = null,
  ): Promise<boolean> {
    const normalizedContent = content.trim();
    if (!normalizedContent && !pendingFile) {
      return false;
    }

    setIsResponding(true);
    setErrorMessage(null);

    try {
      let activeChatId = selectedChatId;

      if (!activeChatId) {
        activeChatId = await serviceRef.current.createChat();
        setSelectedChatId(activeChatId);
        setSelectedChat(createEmptyChat(activeChatId));
        syncChatSummary(createEmptyChat(activeChatId));
        void loadChats(activeChatId);
      }

      if (!activeChatId) {
        throw new Error("No active chat is available.");
      }

      if (pendingFile) {
        if (normalizedContent) {
          const userMessage = createUserMessage(normalizedContent);
          appendChatMessage(activeChatId, userMessage);
        }

        setDocumentProcessingStatus({
          filename: pendingFile.name,
          stage: "uploading",
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
          stage: "Anonimizando",
          message: "Anonimizando el contenido antes de consultar al asistente...",
          current: 1,
          total: 1,
          progress: null,
        });

        const assistantMessage = createAssistantMessage();
        appendAssistantMessage(activeChatId, assistantMessage);

        let didReceiveFirstChunk = false;
        await serviceRef.current.streamSafeResponse(
          activeChatId,
          documentId,
          (chunk) => {
            if (!didReceiveFirstChunk) {
              didReceiveFirstChunk = true;
              setDocumentProcessingStatus(null);
            }
            appendAssistantChunk(activeChatId, assistantMessage.id, chunk);
          },
        );
      }

      if (!pendingFile) {
        const userMessage = createUserMessage(normalizedContent);
        appendChatMessage(activeChatId, userMessage);

        const assistantMessage = createAssistantMessage();
        appendChatMessage(activeChatId, assistantMessage);

        setResponseProcessingStatus({
          title: "Mensaje del chat",
          stage: "Anonimizando",
          message: "Anonimizando el mensaje antes de consultar al asistente...",
        });

        let didReceiveFirstChunk = false;
        await serviceRef.current.streamMessage(
          activeChatId,
          normalizedContent,
          (chunk) => {
            if (!didReceiveFirstChunk) {
              didReceiveFirstChunk = true;
              setResponseProcessingStatus(null);
            }
            appendAssistantChunk(activeChatId, assistantMessage.id, chunk);
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
  };
}
