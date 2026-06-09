import type { ChangeEvent, KeyboardEvent, MutableRefObject } from "react";

interface ConversationComposerProps {
  draft: string;
  fileInputRef: MutableRefObject<HTMLInputElement | null>;
  isInteractionLocked: boolean;
  onClearFile: () => void;
  onDraftChange: (value: string) => void;
  onFileSelect: (file: File | null) => void;
  onPreviewAnonymizedTextChange: (value: boolean) => void;
  onSubmit: () => void;
  pendingFile: File | null;
  shouldPreviewAnonymizedText: boolean;
  statusMessage: string;
}

// Render the chat composer with draft, upload, preview, and send controls.
export function ConversationComposer({
  draft,
  fileInputRef,
  isInteractionLocked,
  onClearFile,
  onDraftChange,
  onFileSelect,
  onPreviewAnonymizedTextChange,
  onSubmit,
  pendingFile,
  shouldPreviewAnonymizedText,
  statusMessage,
}: ConversationComposerProps) {
  // Forward the currently selected file from the hidden input.
  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    onFileSelect(event.target.files?.[0] ?? null);
    event.target.value = "";
  }

  // Submit the current draft when the user presses Enter without Shift.
  function handleKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (
      event.key === "Enter" &&
      !event.shiftKey &&
      !isInteractionLocked
    ) {
      event.preventDefault();
      onSubmit();
    }
  }

  return (
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
          onKeyDown={handleKeyDown}
        />
        <div className="composer__toolbar">
          <input
            ref={fileInputRef}
            className="composer__file-input"
            type="file"
            accept=".pdf,application/pdf"
            disabled={isInteractionLocked}
            onChange={handleFileChange}
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
            <img
              className="icon-image"
              src="/icons/upload-document.svg"
              alt=""
              aria-hidden="true"
            />
          </button>
          <div className="composer__actions">
            <label
              className="preview-switch tooltip-target"
              title="Activar para revisar el texto anonimizado antes de enviarlo"
              data-tooltip={
                shouldPreviewAnonymizedText
                  ? "Previsualización activada"
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
              <img
                className="icon-image"
                src="/icons/send-message.svg"
                alt=""
                aria-hidden="true"
              />
            </button>
          </div>
        </div>
      </div>
      <span className="conversation__status">{statusMessage}</span>
    </footer>
  );
}
