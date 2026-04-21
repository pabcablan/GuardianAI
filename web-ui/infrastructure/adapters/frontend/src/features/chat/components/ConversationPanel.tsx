import { useRef, useState } from "react";
import type { ChatThread } from "../types";

interface ConversationPanelProps {
  chat: ChatThread | null;
  draft: string;
  errorMessage: string | null;
  isLoadingChats: boolean;
  isResponding: boolean;
  pendingFile: File | null;
  onDraftChange: (value: string) => void;
  onFileSelect: (file: File | null) => void;
  onClearFile: () => void;
  onSubmit: () => void;
}

export function ConversationPanel({
  chat,
  draft,
  errorMessage,
  isLoadingChats,
  isResponding,
  pendingFile,
  onDraftChange,
  onFileSelect,
  onClearFile,
  onSubmit,
}: ConversationPanelProps) {
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);

  function handleDragOver(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
    setIsDragOver(true);
  }

  function handleDragLeave(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
    setIsDragOver(false);
  }

  function handleDrop(event: React.DragEvent<HTMLElement>) {
    event.preventDefault();
    setIsDragOver(false);
    onFileSelect(event.dataTransfer.files[0] ?? null);
  }

  return (
    <section
      className={`conversation ${isDragOver ? "conversation--drag-over" : ""}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
    >
      <div className="conversation__canvas">
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
                    "Tu"
                  )}
                </span>
              </div>
              <p>{message.content}</p>
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
      </div>

      <footer className="composer">
        {pendingFile ? (
          <div className="file-banner">
            <div className="file-banner__copy">
              <span className="file-banner__label">Documento listo para subir</span>
              <strong>{pendingFile.name}</strong>
            </div>
            <button
              className="file-banner__clear"
              type="button"
              onClick={onClearFile}
              aria-label="Quitar documento seleccionado"
            >
              ×
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
            onChange={(event) => onDraftChange(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
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
              onChange={(event) => onFileSelect(event.target.files?.[0] ?? null)}
            />
            <button
              className="composer__upload"
              type="button"
              onClick={() => fileInputRef.current?.click()}
              aria-label="Subir archivo PDF"
            >
              <img className="icon-image" src="/icons/upload-document.svg" alt="" aria-hidden="true" />
            </button>
            <button
              className="composer__button"
              type="button"
              onClick={onSubmit}
              disabled={(!draft.trim() && !pendingFile) || isResponding}
              aria-label="Enviar mensaje"
            >
              <img className="icon-image" src="/icons/send-message.svg" alt="" aria-hidden="true" />
            </button>
          </div>
        </div>
        <span className="conversation__status">
          {isResponding ? "Generando respuesta..." : chat?.title || "Listo para empezar"}
        </span>
      </footer>
    </section>
  );
}
