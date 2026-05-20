import type { ReactNode, Ref } from "react";

import { renderAssistantMarkdown } from "./assistantMarkdown";
import type { ChatMessage, ChatThread } from "../types";

interface ConversationMessageListProps {
  chat: ChatThread | null;
  errorMessage: string | null;
  isLoadingChats: boolean;
  isResponding: boolean;
  messageEndRef: Ref<HTMLDivElement>;
  onApproveAnonymizedMessage: (message: ChatMessage) => void;
  onOpenAnonymizedPdfPreview: (message: ChatMessage) => void;
}

interface HighlightedSegment {
  content: string;
  anonymizationId?: string;
}

const ANONYMIZATION_PLACEHOLDER_PATTERN = /\[[A-Z0-9_]+\]/g;

function buildHighlightedSegments(
  originalContent: string,
  anonymizedContent?: string,
): HighlightedSegment[] {
  if (!anonymizedContent) {
    return [{ content: originalContent }];
  }

  const matches = Array.from(
    anonymizedContent.matchAll(ANONYMIZATION_PLACEHOLDER_PATTERN),
  );

  if (!matches.length) {
    return [{ content: originalContent }];
  }

  const segments: HighlightedSegment[] = [];
  let originalCursor = 0;
  let anonymizedCursor = 0;

  for (const [index, match] of matches.entries()) {
    const anonymizationId = match[0];
    const placeholderStart = match.index ?? 0;
    const placeholderEnd = placeholderStart + anonymizationId.length;
    const literalBefore = anonymizedContent.slice(
      anonymizedCursor,
      placeholderStart,
    );
    const beforeIndex = originalContent.indexOf(literalBefore, originalCursor);

    if (beforeIndex === -1) {
      return [{ content: originalContent }];
    }

    const normalStart = beforeIndex;
    const normalEnd = beforeIndex + literalBefore.length;

    if (normalStart > originalCursor) {
      segments.push({
        content: originalContent.slice(originalCursor, normalStart),
      });
    }

    if (literalBefore) {
      segments.push({ content: literalBefore });
    }

    const nextMatch = matches[index + 1];
    const nextLiteral = anonymizedContent.slice(
      placeholderEnd,
      nextMatch?.index ?? anonymizedContent.length,
    );
    const sensitiveStart = normalEnd;
    const sensitiveEnd = nextLiteral
      ? originalContent.indexOf(nextLiteral, sensitiveStart)
      : originalContent.length;

    if (sensitiveEnd === -1 || sensitiveEnd < sensitiveStart) {
      return [{ content: originalContent }];
    }

    const sensitiveContent = originalContent.slice(
      sensitiveStart,
      sensitiveEnd,
    );

    if (sensitiveContent) {
      segments.push({
        content: sensitiveContent,
        anonymizationId,
      });
    }

    originalCursor = sensitiveEnd;
    anonymizedCursor = placeholderEnd;
  }

  if (originalCursor < originalContent.length) {
    segments.push({ content: originalContent.slice(originalCursor) });
  }

  return segments.filter((segment) => segment.content.length > 0);
}

function renderMessageContent(message: ChatMessage): ReactNode {
  if (message.role !== "user" || !message.anonymizedContent) {
    return message.content;
  }

  if (
    message.pendingApproval?.documentId &&
    message.pendingApproval.extractionMethod !== "model"
  ) {
    return message.content;
  }

  const originalContent =
    message.pendingApproval?.originalContent ?? message.content;

  return buildHighlightedSegments(
    originalContent,
    message.anonymizedContent,
  ).map((segment, index) => {
    if (!segment.anonymizationId) {
      return <span key={`${index}-${segment.content}`}>{segment.content}</span>;
    }

    return (
      <mark
        key={`${index}-${segment.anonymizationId}`}
        className="message__anonymized-highlight"
        data-anonymization-id={segment.anonymizationId}
      >
        {segment.content}
      </mark>
    );
  });
}

export function ConversationMessageList({
  chat,
  errorMessage,
  isLoadingChats,
  isResponding,
  messageEndRef,
  onApproveAnonymizedMessage,
  onOpenAnonymizedPdfPreview,
}: ConversationMessageListProps) {
  if (errorMessage) {
    return (
      <>
        <div className="conversation__welcome">
          <p className="conversation__welcome-title">No se pudo cargar el chat</p>
          <p className="conversation__welcome-copy">{errorMessage}</p>
        </div>
        <div ref={messageEndRef} className="conversation__scroll-anchor" />
      </>
    );
  }

  if (isLoadingChats) {
    return (
      <>
        <div className="conversation__welcome">
          <p className="conversation__welcome-title">Cargando conversaciones</p>
          <p className="conversation__welcome-copy">
            Espera un momento mientras se prepara la sesión.
          </p>
        </div>
        <div ref={messageEndRef} className="conversation__scroll-anchor" />
      </>
    );
  }

  if (!chat?.messages.length) {
    return (
      <>
        <div className="conversation__welcome">
          <p className="conversation__welcome-title">
            Empieza una nueva conversación
          </p>
          <p className="conversation__welcome-copy">
            Escribe un mensaje o adjunta un PDF para comenzar a usar GuardianAI.
          </p>
        </div>
        <div ref={messageEndRef} className="conversation__scroll-anchor" />
      </>
    );
  }

  return (
    <>
      {chat.messages.map((message) => (
        <article
          key={message.id}
          className={`message message--${message.role}`}
        >
          <div className="message__body">
            <div className="message__meta">
              <span className="message__author">
                {message.role === "assistant" ? (
                  <span
                    className="message__ai-badge"
                    aria-label="Asistente de IA"
                    title="Asistente de IA"
                  >
                    <img
                      className="icon-image"
                      src="/icons/ai-robot.svg"
                      alt=""
                      aria-hidden="true"
                    />
                  </span>
                ) : (
                  "Tú"
                )}
              </span>
            </div>
            {message.role === "assistant" ? (
              <div className="message__content message__content--rich">
                {renderAssistantMarkdown(message.content)}
              </div>
            ) : (
              <p className="message__content">{renderMessageContent(message)}</p>
            )}
            {message.role === "user" &&
            message.anonymizedContent &&
            message.pendingApproval ? (
              <div className="message__anonymized-actions">
                {message.pendingApproval.documentId &&
                message.pendingApproval.extractionMethod !== "model" &&
                (message.pendingApproval.replacementCount ?? 0) > 0 ? (
                  <button
                    className="message__secondary-button"
                    type="button"
                    onClick={() => onOpenAnonymizedPdfPreview(message)}
                  >
                    Ver PDF anonimizado
                  </button>
                ) : null}
                <button
                  className="message__approve-button"
                  type="button"
                  disabled={isResponding}
                  onClick={() => onApproveAnonymizedMessage(message)}
                >
                  Enviar a la IA
                </button>
              </div>
            ) : null}
          </div>
        </article>
      ))}
      <div ref={messageEndRef} className="conversation__scroll-anchor" />
    </>
  );
}
