import { useEffect, useState } from "react";

import type { ChatApplicationService } from "../application/chatApplicationService";
import type { ChatMessage, ChatSummary, ChatThread } from "../types";
import {
  createChatSummary,
  createEmptyChat,
  getErrorMessage,
} from "./chatWorkspaceUtils";

interface UseChatCollectionOptions {
  service: ChatApplicationService;
  onError: (message: string | null) => void;
}

export function useChatCollection({
  service,
  onError,
}: UseChatCollectionOptions) {
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [selectedChatId, setSelectedChatId] = useState("");
  const [selectedChat, setSelectedChat] = useState<ChatThread | null>(null);
  const [isLoadingChats, setIsLoadingChats] = useState(true);

  useEffect(() => {
    void loadChats();
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
    onError(null);

    try {
      const summaries = await service.listChats();
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
      onError(getErrorMessage(error));
      return null;
    } finally {
      setIsLoadingChats(false);
    }
  }

  async function loadChatDetail(chatId: string): Promise<void> {
    onError(null);

    try {
      const chat = await service.loadChat(chatId);
      setSelectedChat(chat);
      syncChatSummary(chat);
    } catch (error) {
      setSelectedChat(null);
      onError(getErrorMessage(error));
    }
  }

  function syncChatSummary(chat: ChatThread): void {
    setChats((currentChats) => {
      const nextSummary = createChatSummary(chat);
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
      const targetChat =
        currentChat?.id === chatId ? currentChat : createEmptyChat(chatId);

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
      const targetChat =
        currentChat?.id === chatId ? currentChat : createEmptyChat(chatId);

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

      const nextPreview =
        streamedMessage?.content ?? currentChat.lastMessagePreview;

      return {
        ...currentChat,
        lastMessagePreview: nextPreview,
        updatedAt: "Ahora",
        messages,
      };
    });
  }

  function updateUserAnonymizedContent(
    chatId: string,
    messageId: string,
    anonymizedContent: string,
    anonymizationId?: string,
    replacementCount?: number,
    documentId?: string,
    extractionMethod?: string,
  ): void {
    setSelectedChat((currentChat) => {
      if (!currentChat || currentChat.id !== chatId) {
        return currentChat;
      }

      return {
        ...currentChat,
        messages: currentChat.messages.map((message) =>
          message.id === messageId
            ? {
                ...message,
                anonymizedContent,
                pendingApproval: anonymizationId
                  ? {
                      anonymizationId,
                      anonymizedContent,
                      replacementCount,
                      documentId,
                      extractionMethod,
                    }
                  : message.pendingApproval,
              }
            : message,
        ),
      };
    });
  }

  function clearMessageApproval(chatId: string, messageId: string): void {
    setSelectedChat((currentChat) => {
      if (!currentChat || currentChat.id !== chatId) {
        return currentChat;
      }

      return {
        ...currentChat,
        messages: currentChat.messages.map((message) =>
          message.id === messageId
            ? {
                ...message,
                pendingApproval: undefined,
              }
            : message,
        ),
      };
    });
  }

  async function createChat(): Promise<string | null> {
    onError(null);

    try {
      const chatId = await service.createChat();
      await loadChats(chatId);
      setSelectedChatId(chatId);
      return chatId;
    } catch (error) {
      onError(getErrorMessage(error));
      return null;
    }
  }

  async function ensureActiveChat(): Promise<string | null> {
    if (selectedChatId) {
      return selectedChatId;
    }

    const chatId = await service.createChat();
    const emptyChat = createEmptyChat(chatId);

    setSelectedChatId(chatId);
    setSelectedChat(emptyChat);
    syncChatSummary(emptyChat);
    void loadChats(chatId);

    return chatId;
  }

  async function renameChat(chatId: string, title: string): Promise<boolean> {
    const normalizedTitle = title.trim();
    if (!normalizedTitle) {
      onError("El nombre del chat no puede estar vacío.");
      return false;
    }

    onError(null);

    try {
      await service.renameChat(chatId, normalizedTitle);

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
      onError(getErrorMessage(error));
      return false;
    }
  }

  async function deleteChat(chatId: string): Promise<boolean> {
    onError(null);

    try {
      await service.deleteChat(chatId);

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
      onError(getErrorMessage(error));
      return false;
    }
  }

  function selectChat(chatId: string): void {
    setSelectedChatId(chatId);
  }

  return {
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
    createChat,
    ensureActiveChat,
    renameChat,
    deleteChat,
  };
}
