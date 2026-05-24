import { useEffect, useState } from "react";

import type { ChatApplicationService } from "../application/chatApplicationService";
import type { ChatMessage, ChatSummary, ChatThread } from "../types";
import {
  createChatSummary,
  createEmptyChat,
  getErrorMessage,
} from "./chatWorkspaceUtils";

interface UseChatCollectionOptions {
  onError: (message: string | null) => void;
  service: ChatApplicationService;
}

// Manage the chat list, the selected chat, and local message updates.
export function useChatCollection({
  onError,
  service,
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

  // Load all chat summaries and keep the current selection in sync.
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

  // Load one full chat thread when the selected chat changes.
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

  // Sync one full chat thread back into the sidebar summary list.
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

  // Patch one existing chat summary in the local sidebar state.
  function updateChatSummary(
    chatId: string,
    updates: Partial<ChatSummary>,
  ): void {
    setChats((currentChats) =>
      currentChats.map((chat) =>
        chat.id === chatId
          ? {
              ...chat,
              ...updates,
            }
          : chat,
      ),
    );
  }

  // Update the selected chat in place and optionally create it if missing.
  function updateSelectedChat(
    chatId: string,
    updater: (chat: ChatThread) => ChatThread,
    createIfMissing = false,
  ): void {
    setSelectedChat((currentChat) => {
      const targetChat =
        currentChat?.id === chatId
          ? currentChat
          : createIfMissing
            ? createEmptyChat(chatId)
            : null;

      if (!targetChat || targetChat.id !== chatId) {
        return currentChat;
      }

      return updater(targetChat);
    });
  }

  // Append one full message to both the sidebar summary and the selected chat.
  function appendMessage(chatId: string, message: ChatMessage): void {
    updateChatSummary(chatId, {
      lastMessagePreview: message.content,
      updatedAt: message.createdAt,
    });

    updateSelectedChat(
      chatId,
      (chat) => ({
        ...chat,
        lastMessagePreview: message.content,
        updatedAt: message.createdAt,
        messages: [...chat.messages, message],
      }),
      true,
    );
  }

  // Append one assistant message after it is first created.
  function appendAssistantMessage(chatId: string, message: ChatMessage): void {
    appendMessage(chatId, message);
  }

  // Append one user-facing chat message to the current thread.
  function appendChatMessage(chatId: string, message: ChatMessage): void {
    appendMessage(chatId, message);
  }

  // Append one streamed assistant chunk to the existing assistant message.
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

    updateSelectedChat(chatId, (chat) => {
      const messages = chat.messages.map((message) => {
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

      return {
        ...chat,
        lastMessagePreview: streamedMessage?.content ?? chat.lastMessagePreview,
        updatedAt: "Ahora",
        messages,
      };
    });
  }

  // Store anonymized content and approval metadata on one user message.
  function updateUserAnonymizedContent(
    chatId: string,
    messageId: string,
    anonymizedContent: string,
    anonymizationId?: string,
    replacementCount?: number,
    documentId?: string,
    extractionMethod?: string,
    originalContent?: string,
  ): void {
    updateSelectedChat(chatId, (chat) => ({
      ...chat,
      messages: chat.messages.map((message) =>
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
                    originalContent,
                  }
                : message.pendingApproval,
            }
          : message,
      ),
    }));
  }

  // Clear the pending approval state from one message after confirmation.
  function clearMessageApproval(chatId: string, messageId: string): void {
    updateSelectedChat(chatId, (chat) => ({
      ...chat,
      messages: chat.messages.map((message) =>
        message.id === messageId
          ? {
              ...message,
              pendingApproval: undefined,
            }
          : message,
      ),
    }));
  }

  // Create a new chat from the UI and select it.
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

  // Ensure there is an active chat before sending a new message.
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

  // Rename one chat and mirror the change in local state.
  async function renameChat(chatId: string, title: string): Promise<boolean> {
    const normalizedTitle = title.trim();
    if (!normalizedTitle) {
      onError("El nombre del chat no puede estar vacío.");
      return false;
    }

    onError(null);

    try {
      await service.renameChat(chatId, normalizedTitle);

      updateChatSummary(chatId, { title: normalizedTitle });
      updateSelectedChat(chatId, (chat) => ({
        ...chat,
        title: normalizedTitle,
      }));

      return true;
    } catch (error) {
      onError(getErrorMessage(error));
      return false;
    }
  }

  // Delete one chat and move the selection if needed.
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

  // Switch the current chat selection from the sidebar.
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
