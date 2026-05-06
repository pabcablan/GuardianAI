import { useEffect, useRef, useState } from "react";

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

  function handleDragOver(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
    if (isInteractionLocked) {
      return;
    }
    setIsDragOver(true);
  }

  function handleDragLeave(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
    setIsDragOver(false);
  }

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
        {!modelReadiness.ready ? (
          <section className="model-readiness-card" aria-live="polite" aria-atomic="true">
            <p className="model-readiness-card__eyebrow">Inicializando modelos</p>
            <h2 className="model-readiness-card__title">GuardianAI se esta preparando</h2>
            <p className="model-readiness-card__copy">{modelReadiness.message}</p>
            <div className="model-readiness-card__bar" role="progressbar">
              <span />
            </div>
          </section>
        ) : null}

        {documentProcessingStatus || responseProcessingStatus ? (
          <div className="conversation__progress-stack">
            {documentProcessingStatus ? (
              <section className="processing-card" aria-live="polite" aria-atomic="true">
                <div className="processing-card__header">
                  <div>
                    <p className="processing-card__eyebrow">Procesando documento</p>
                    <h2 className="processing-card__title">{documentProcessingStatus.filename}</h2>
                  </div>
                  <span className="processing-card__stage">{documentProcessingStatus.stage}</span>
                </div>
                <p className="processing-card__message">{documentProcessingStatus.message}</p>
                <div
                  className={`processing-card__bar ${documentProcessingStatus.progress === null ? "processing-card__bar--indeterminate" : ""}`.trim()}
                  role="progressbar"
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-valuenow={
                    documentProcessingStatus.progress === null
                      ? undefined
                      : Math.round(documentProcessingStatus.progress * 100)
                  }
                >
                  <span
                    className="processing-card__bar-fill"
                    style={
                      documentProcessingStatus.progress === null
                        ? undefined
                        : { width: `${Math.max(8, documentProcessingStatus.progress * 100)}%` }
                    }
                  />
                </div>
                <p className="processing-card__meta">
                  {documentProcessingStatus.progress === null
                    ? "Esperando actualizaciones del backend..."
                    : `${documentProcessingStatus.current} de ${documentProcessingStatus.total}`}
                </p>
              </section>
            ) : null}

            {responseProcessingStatus ? (
              <section className="processing-card" aria-live="polite" aria-atomic="true">
                <div className="processing-card__header">
                  <div>
                    <p className="processing-card__eyebrow">Protegiendo contenido</p>
                    <h2 className="processing-card__title">{responseProcessingStatus.title}</h2>
                  </div>
                  <span className="processing-card__stage">{responseProcessingStatus.stage}</span>
                </div>
                <p className="processing-card__message">{responseProcessingStatus.message}</p>
                <div
                  className="processing-card__bar processing-card__bar--indeterminate"
                  role="progressbar"
                >
                  <span className="processing-card__bar-fill" />
                </div>
                <p className="processing-card__meta">
                  Esperando los primeros fragmentos de la respuesta segura...
                </p>
              </section>
            ) : null}
          </div>
        ) : null}

        {errorMessage ? (
          <div className="conversation__welcome">
            <p className="conversation__welcome-title">No se pudo cargar el chat</p>
            <p className="conversation__welcome-copy">{errorMessage}</p>
          </div>
        ) : isLoadingChats ? (
          <div className="conversation__welcome">
            <p className="conversation__welcome-title">Cargando conversaciones</p>
            <p className="conversation__welcome-copy">
              Espera un momento mientras se prepara la sesion.
            </p>
          </div>
        ) : chat?.messages.length ? (
          chat.messages.map((message) => (
            <article
              key={message.id}
              className={`message message--${message.role}`}
            >
              <div className="message__meta">
                <span className="message__author">
                  {message.role === "assistant" ? (
                    <span className="message__ai-badge" aria-label="Asistente de IA" title="Asistente de IA">
                      <img className="icon-image" src="/icons/ai-robot.svg" alt="" aria-hidden="true" />
                    </span>
                  ) : (
                    "Tú"
                  )}
                </span>
              </div>
              <p>{message.content}</p>
              {message.role === "user" && message.anonymizedContent ? (
                <div className="message__anonymized">
                  <span className="message__anonymized-label">
                    Texto anonimizado
                  </span>
                  <p>{message.anonymizedContent}</p>
                  {message.pendingApproval ? (
                    <div className="message__anonymized-actions">
                      {message.pendingApproval.documentId ? (
                        <button
                          className="message__secondary-button"
                          type="button"
                          disabled={isResponding}
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
              ) : null}
            </article>
          ))
        ) : (
          <div className="conversation__welcome">
            <p className="conversation__welcome-title">Empieza una nueva conversacion</p>
            <p className="conversation__welcome-copy">
              Escribe un mensaje o adjunta un PDF para comenzar a usar Guardian AI.
            </p>
          </div>
        )}
        <div ref={messageEndRef} className="conversation__scroll-anchor" />
      </div>

      <footer className="composer">
        {pendingFile ? (
          <div className="file-banner">
            <div className="file-banner__copy">
              <span className="file-banner__label">Documento listo para subir</span>
              <strong>{pendingFile.name}</strong>
            </div>
            <button
              className="file-banner__clear tooltip-target"
              type="button"
              onClick={onClearFile}
              disabled={isInteractionLocked}
              aria-label="Quitar documento seleccionado"
              title="Quitar el PDF seleccionado antes de enviarlo"
              data-tooltip="Quitar PDF"
            >
              x
            </button>
          </div>
        ) : null}

        <div className="composer__box">
          <textarea
            id="chat-message"
            className="composer__input"
            rows={3}
            placeholder="Pregunta lo que quieras"
            value={draft}
            disabled={isInteractionLocked}
            onChange={(event) => onDraftChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey && !isInteractionLocked) {
                event.preventDefault();
                onSubmit();
              }
            }}
          />
          <div className="composer__toolbar">
            <input
              ref={fileInputRef}
              className="composer__file-input"
              type="file"
              accept=".pdf,application/pdf"
              disabled={isInteractionLocked}
              onChange={(event) => onFileSelect(event.target.files?.[0] ?? null)}
            />
            <button
              className="composer__upload tooltip-target"
              type="button"
              disabled={isInteractionLocked}
              onClick={() => fileInputRef.current?.click()}
              aria-label="Subir archivo PDF"
              title="Adjuntar un documento PDF al chat"
              data-tooltip="Adjuntar PDF"
            >
              <img className="icon-image" src="/icons/upload-document.svg" alt="" aria-hidden="true" />
            </button>
            <div className="composer__actions">
              <label
                className="preview-switch tooltip-target"
                title="Activar para revisar el texto anonimizado antes de enviarlo"
                data-tooltip={
                  shouldPreviewAnonymizedText
                    ? "Previsualizacion activada"
                    : "Enviar sin revisar"
                }
              >
                <input
                  className="preview-switch__input"
                  type="checkbox"
                  checked={shouldPreviewAnonymizedText}
                  disabled={isInteractionLocked}
                  onChange={(event) =>
                    onPreviewAnonymizedTextChange(event.target.checked)
                  }
                />
                <span className="preview-switch__track">
                  <span className="preview-switch__thumb" />
                </span>
                <span className="preview-switch__text">
                  {shouldPreviewAnonymizedText ? "Revisar" : "Sin revisar"}
                </span>
              </label>
              <button
                className="composer__button tooltip-target"
                type="button"
                onClick={onSubmit}
                disabled={(!draft.trim() && !pendingFile) || isInteractionLocked}
                aria-label="Enviar mensaje"
                title="Enviar mensaje al asistente"
                data-tooltip="Enviar mensaje"
              >
                <img className="icon-image" src="/icons/send-message.svg" alt="" aria-hidden="true" />
              </button>
            </div>
          </div>
        </div>
        <span className="conversation__status">
          {documentProcessingStatus?.message
            ?? responseProcessingStatus?.message
            ?? (!modelReadiness.ready
              ? modelReadiness.message
              : isResponding
                ? "Generando respuesta..."
                : chat?.title || "Listo para empezar")}
        </span>
      </footer>
    </section>
  );
}
