import type { DocumentProcessingStatus } from "../types";
import type {
  AttachDocumentStreamResponse,
  SafeStreamResponse,
} from "./chatApiTypes";

export const SAFE_STREAM_CHUNK_DELAY_MS = 180;

export async function consumeNdjsonStream(
  response: Response,
  onLine: (rawLine: string) => Promise<void> | void,
): Promise<void> {
  if (!response.body) {
    throw new Error("El flujo de respuesta no está disponible.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder("utf-8");
  let buffer = "";

  while (true) {
    const { value, done } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });

    let lineBreakIndex = buffer.indexOf("\n");
    while (lineBreakIndex >= 0) {
      const rawLine = buffer.slice(0, lineBreakIndex).trim();
      buffer = buffer.slice(lineBreakIndex + 1);

      if (rawLine) {
        await onLine(rawLine);
      }

      lineBreakIndex = buffer.indexOf("\n");
    }

    if (done) {
      break;
    }
  }

  const lastLine = buffer.trim();
  if (lastLine) {
    await onLine(lastLine);
  }
}

export function handleDocumentStreamLine(
  rawLine: string,
  filename: string,
  onProgress: (status: DocumentProcessingStatus) => void,
): string | null {
  const payload = JSON.parse(rawLine) as AttachDocumentStreamResponse;

  if (payload.event === "progress") {
    const progress =
      payload.total > 0
        ? Math.max(0, Math.min(1, payload.current / payload.total))
        : null;

    onProgress({
      filename,
      stage: payload.stage,
      message: payload.message,
      current: payload.current,
      total: payload.total,
      progress,
    });
    return null;
  }

  if (payload.event === "completed") {
    onProgress({
      filename,
      stage: "Completado",
      message: "Documento procesado. Generando respuesta segura...",
      current: 1,
      total: 1,
      progress: 1,
    });
    return payload.document_id;
  }

  if (payload.event === "error") {
    throw new Error(payload.detail);
  }

  return null;
}

export async function handleSafeStreamLine(
  rawLine: string,
  onChunk: (chunk: string) => void,
  onAnonymizedPrompt?: (content: string) => void,
): Promise<void> {
  const payload = JSON.parse(rawLine) as SafeStreamResponse;

  if (payload.event === "anonymized_prompt") {
    onAnonymizedPrompt?.(payload.content);
    return;
  }

  if (payload.event === "chunk") {
    onChunk(payload.content);
    await wait(SAFE_STREAM_CHUNK_DELAY_MS);
    return;
  }

  if (payload.event === "error") {
    throw new Error(payload.detail);
  }
}

function wait(milliseconds: number): Promise<void> {
  return new Promise((resolve) => {
    window.setTimeout(resolve, milliseconds);
  });
}
