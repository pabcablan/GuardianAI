import { useEffect, useRef, useState } from "react";

import { createChatApplicationService } from "../application/chatApplicationService";
import type { ChatSummary, ChatThread } from "../types";


function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : "Unexpected error.";
}


export function useChatWorkspace() {
  const serviceRef = useRef(createChatApplicationService());
  const [chats, setChats] = useState<ChatSummary[]>([]);
  const [selectedChatId, setSelectedChatId] = useState("");
  const [selectedChat, setSelectedChat] = useState<ChatThread | null>(null);
  const [isResponding, setIsResponding] = useState(false);
  const [isLoadingChats, setIsLoadingChats] = useState(true);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

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
    setErrorMessage(null);

    try {
      const summaries = await serviceRef.current.listChats();
      setChats(summaries);

      if (!summaries.length) {
        return null;
      }

      const nextSelectedChatId =
        preferredChatId
        ?? selectedChatId
        ?? summaries[0].id;

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

  async function sendMessage(
    content: string,
    pendingFile: File | null = null,
  ): Promise<void> {
    const normalizedContent = content.trim();
    if (!normalizedContent && !pendingFile) {
      return;
    }

    setIsResponding(true);
    setErrorMessage(null);

    try {
      let activeChatId = selectedChatId;

      if (!activeChatId) {
        activeChatId = await serviceRef.current.createChat();
        await loadChats(activeChatId);
        setSelectedChatId(activeChatId);
      }

      if (!activeChatId) {
        throw new Error("No active chat is available.");
      }

      if (pendingFile) {
        await serviceRef.current.attachDocument(activeChatId, pendingFile);
      }

      if (normalizedContent) {
        await serviceRef.current.sendMessage(activeChatId, normalizedContent);
      }

      await loadChats(activeChatId);
      await loadChatDetail(activeChatId);
    } catch (error) {
      setErrorMessage(getErrorMessage(error));
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
    selectChat,
    createChat,
    sendMessage,
  };
}
