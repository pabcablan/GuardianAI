import { useEffect, useRef, useState } from "react";

import { ConversationComposer } from "./ConversationComposer";
import { ConversationMessageList } from "./ConversationMessageList";
import { ConversationProgressStack } from "./ConversationProgressStack";
import type {
  ChatMessage,
  ChatThread,
  DocumentProcessingStatus,
  ModelReadinessStatus,
  ResponseProcessingStatus,
} from "../types";

interface ConversationPanelProps {
  chat: ChatThread | null;
  draft: string;
  errorMessage: string | null;
  isLoadingChats: boolean;
  isResponding: boolean;
  isInteractionLocked: boolean;
  modelReadiness: ModelReadinessStatus;
  documentProcessingStatus: DocumentProcessingStatus | null;
  responseProcessingStatus: ResponseProcessingStatus | null;
  pendingFile: File | null;
  shouldPreviewAnonymizedText: boolean;
  onDraftChange: (value: string) => void;
  onPreviewAnonymizedTextChange: (value: boolean) => void;
  onFileSelect: (file: File | null) => void;
  onClearFile: () => void;
  onApproveAnonymizedMessage: (message: ChatMessage) => void;
  onOpenAnonymizedPdfPreview: (message: ChatMessage) => void;
  onSubmit: () => void;
}

// Render the full conversation area with progress cards, messages, and composer.
export function ConversationPanel({
  chat,
  draft,
  errorMessage,
  isLoadingChats,
  isResponding,
  isInteractionLocked,
  modelReadiness,
  documentProcessingStatus,
  responseProcessingStatus,
  pendingFile,
  shouldPreviewAnonymizedText,
  onDraftChange,
  onPreviewAnonymizedTextChange,
  onFileSelect,
  onClearFile,
  onApproveAnonymizedMessage,
  onOpenAnonymizedPdfPreview,
  onSubmit,
}: ConversationPanelProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const messageEndRef = useRef<HTMLDivElement | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const lastMessage = chat?.messages[chat.messages.length - 1];

  useEffect(() => {
    messageEndRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "end",
    });
  }, [
    chat?.id,
    chat?.messages.length,
    lastMessage?.content,
    lastMessage?.anonymizedContent,
    lastMessage?.pendingApproval,
    documentProcessingStatus?.message,
    documentProcessingStatus?.progress,
    responseProcessingStatus?.message,
    isResponding,
  ]);

  // Mark the conversation as a valid drop target while dragging a PDF over it.
  function handleDragOver(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
    if (isInteractionLocked) {
      return;
    }
    setIsDragOver(true);
  }

  // Clear the drag state when the pointer leaves the conversation area.
  function handleDragLeave(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
    setIsDragOver(false);
  }

  // Accept one dropped PDF file and forward it to the workspace.
  function handleDrop(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
    setIsDragOver(false);
    if (isInteractionLocked) {
      return;
    }
    onFileSelect(event.dataTransfer.files[0] ?? null);
  }

  return (
    <section
      className={`conversation ${isDragOver ? "conversation--drag-over" : ""}`.trim()}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="conversation__canvas">
        <ConversationProgressStack
          modelReadiness={modelReadiness}
          documentProcessingStatus={documentProcessingStatus}
          responseProcessingStatus={responseProcessingStatus}
        />
        <ConversationMessageList
          chat={chat}
          errorMessage={errorMessage}
          isLoadingChats={isLoadingChats}
          isResponding={isResponding}
          messageEndRef={messageEndRef}
          onApproveAnonymizedMessage={onApproveAnonymizedMessage}
          onOpenAnonymizedPdfPreview={onOpenAnonymizedPdfPreview}
        />
      </div>

      <ConversationComposer
        draft={draft}
        fileInputRef={fileInputRef}
        isInteractionLocked={isInteractionLocked}
        onClearFile={onClearFile}
        onDraftChange={onDraftChange}
        onFileSelect={onFileSelect}
        onPreviewAnonymizedTextChange={onPreviewAnonymizedTextChange}
        onSubmit={onSubmit}
        pendingFile={pendingFile}
        shouldPreviewAnonymizedText={shouldPreviewAnonymizedText}
        statusMessage={
          documentProcessingStatus?.message ??
          responseProcessingStatus?.message ??
          (!modelReadiness.ready
            ? modelReadiness.message
            : isResponding
              ? "Generando respuesta..."
              : chat?.title || "Listo para empezar")
        }
      />
    </section>
  );
}
