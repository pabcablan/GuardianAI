"""Application service that coordinates GuardianAI module calls."""
from __future__ import annotations

import re
import time
from collections.abc import Iterator
from typing import Any

from application.services.anonymization_registry import AnonymizationRegistry
from application.services.document_registry import DocumentRegistry
from domain.anonymized_pdf_preview import AnonymizedPdfPreview
from domain.processed_document import ProcessedDocumentContext
from infrastructure.dependency_container import OrchestratorContainer
from infrastructure.ports.ai_gateway_port import (
    AssistantMessage,
    AssistantStreamRequest,
)
from infrastructure.ports.document_processor_port import DocumentUploadRequest
from infrastructure.ports.privacy_shield_port import AnonymizedPrompt


class OrchestrationService:
    """Coordinate document processing, anonymization, assistant, and restore."""

    _partial_placeholder_pattern = re.compile(r"\[[A-Z_0-9]*$")

    def __init__(self, container: OrchestratorContainer) -> None:
        """Initialize the service.

        Args:
            container (OrchestratorContainer): The orchestrator dependencies.
        """
        self._container = container
        self._document_registry = DocumentRegistry()
        self._anonymization_registry = AnonymizationRegistry()

    def stream_message_response(
        self,
        chat_id: str,
        text: str,
        model: str,
        settings: dict[str, str] | None = None,
        history: list[AssistantMessage] | None = None,
        persisted_replacements: dict[str, str] | None = None,
    ) -> tuple[AnonymizedPrompt, Iterator[dict[str, Any]]]:
        """Anonymize a user prompt and stream a safe assistant response.

        Args:
            chat_id (str): The chat that owns the request.
            text (str): The user prompt.
            model (str): The AI model selected by the user.

        Returns:
            tuple[AnonymizedPrompt, Iterator[dict[str, Any]]]: The anonymized
            prompt metadata and safe stream events.
        """
        started_at = time.perf_counter()
        print(
            "ORCHESTRATOR /api/messages/stream "
            f"chat_id={chat_id} text_len={len(text)}",
            flush=True,
        )
        anonymized_prompt, events = self.stream_safe_response_for_text(
            chat_id=chat_id,
            text=text,
            model=model,
            settings=settings,
            history=history or [],
            persisted_replacements=persisted_replacements or {},
            log_prefix="ORCHESTRATOR",
        )
        print(
            "ORCHESTRATOR message total_before_stream="
            f"{time.perf_counter() - started_at:.3f}s",
            flush=True,
        )
        return anonymized_prompt, events

    def preview_message_anonymization(
        self,
        chat_id: str,
        text: str,
        settings: dict[str, str] | None = None,
    ) -> AnonymizedPrompt:
        """Anonymize a message without calling the assistant.

        Args:
            chat_id (str): The chat that owns the text.
            text (str): The text to anonymize.

        Returns:
            AnonymizedPrompt: The anonymized text metadata.
        """
        anonymized_prompt = self._container.privacy_shield.anonymize(
            chat_id=chat_id,
            text=text,
            settings=settings,
        )
        self._anonymization_registry.store(anonymized_prompt, chat_id)
        return anonymized_prompt

    def preview_document_anonymization(
        self,
        chat_id: str,
        document_id: str,
        settings: dict[str, str] | None = None,
    ) -> tuple[AnonymizedPrompt, str]:
        """Anonymize a processed document without calling the assistant.

        Args:
            chat_id (str): The chat that owns the document.
            document_id (str): The processed document identifier.

        Returns:
            AnonymizedPrompt: The anonymized document text metadata.

        Raises:
            KeyError: If the processed document is unknown.
            ValueError: If the stored document has no usable text.
        """
        text = self.build_document_text(document_id)
        anonymized_prompt = self._container.privacy_shield.anonymize(
            chat_id=chat_id,
            text=text,
            settings=settings,
        )
        self._anonymization_registry.store(anonymized_prompt, chat_id)
        return anonymized_prompt, self._document_registry.get(
            document_id,
        ).extraction_method

    def stream_anonymized_response(
        self,
        chat_id: str,
        anonymized_text: str,
        anonymization_id: str,
        model: str,
        history: list[AssistantMessage] | None = None,
        persisted_replacements: dict[str, str] | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Generate and restore an answer from already anonymized text.

        Args:
            chat_id (str): The chat that owns the request.
            anonymized_text (str): The anonymized text sent to the assistant.
            anonymization_id (str): The privacy-shield session identifier.
            model (str): The AI model selected by the user.

        Returns:
            Iterator[dict[str, Any]]: Safe response stream events.
        """
        return self._stream_response_from_ai_gateway(
            chat_id=chat_id,
            anonymized_prompt=anonymized_text,
            model=model,
            history=history or [],
            replacements=self._build_response_replacements(
                chat_id=chat_id,
                persisted_replacements=persisted_replacements or {},
                current_replacements=self._anonymization_registry.get(
                    anonymization_id,
                ),
            ),
        )

    def stream_extract_document(
        self,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> Iterator[dict[str, Any]]:
        """Send a document to document-processor.

        Args:
            filename (str): The uploaded filename.
            content_type (str): The uploaded content type.
            content (bytes): The uploaded document bytes.

        Returns:
            Iterator[dict[str, Any]]: Document processing events.
        """
        return self._container.document_processor.stream_extract_document(
            DocumentUploadRequest(
                filename=filename,
                content_type=content_type,
                content=content,
            )
        )

    def store_document_if_completed(
        self,
        event: dict[str, Any],
        prompt: str,
        filename: str,
        content_type: str,
        content: bytes,
    ) -> None:
        """Store completed document extraction data.

        Args:
            event (dict[str, Any]): One document processing event.
            prompt (str): The prompt sent with the uploaded document.
            filename (str): The original uploaded filename.
            content_type (str): The original uploaded content type.
            content (bytes): The original uploaded PDF bytes.
        """
        if event.get("event") != "completed":
            return

        document_id = str(event.get("document_id", ""))
        extracted_text = str(event.get("extracted_text", ""))
        if not document_id:
            return

        self._document_registry.store(
            document_id=document_id,
            document=ProcessedDocumentContext(
                extracted_text=extracted_text,
                prompt=prompt.strip(),
                filename=filename,
                content_type=content_type,
                content=content,
                extraction_method=str(
                    event.get("extraction_method", "library"),
                ),
            ),
        )

    def build_anonymized_pdf_preview(
        self,
        document_id: str,
        anonymization_id: str,
    ) -> AnonymizedPdfPreview:
        """Build a PDF preview with original values replaced by placeholders.

        Args:
            document_id (str): The processed document identifier.
            anonymization_id (str): The anonymization session identifier.

        Returns:
            AnonymizedPdfPreview: The preview filename and PDF bytes.

        Raises:
            KeyError: If the document is unknown.
            ValueError: If no visual replacement can be applied.
        """
        document_context = self._document_registry.get(document_id)
        replacements = self._anonymization_registry.get(anonymization_id)
        if not replacements:
            raise ValueError("No hay campos anonimizados para pintar en el PDF.")
        if document_context.extraction_method == "model":
            raise ValueError(
                "No se puede reconstruir una vista visual del PDF cuando el "
                "texto se extrajo mediante OCR/modelo."
            )
        if not document_context.content:
            raise ValueError("No se conserva el PDF original para esta vista.")

        output = self._container.anonymized_pdf_builder.build(
            pdf_content=document_context.content,
            replacements=replacements,
        )
        filename = self._build_anonymized_pdf_filename(
            document_context.filename,
        )
        return AnonymizedPdfPreview(filename=filename, content=output)

    def stream_document_response(
        self,
        chat_id: str,
        document_id: str,
        model: str,
        settings: dict[str, str] | None = None,
        persisted_replacements: dict[str, str] | None = None,
    ) -> tuple[AnonymizedPrompt, Iterator[dict[str, Any]]]:
        """Generate a safe response for a processed document.

        Args:
            chat_id (str): The chat that owns the request.
            document_id (str): The processed document identifier.
            model (str): The AI model selected by the user.

        Returns:
            tuple[AnonymizedPrompt, Iterator[dict[str, Any]]]: The anonymized
            text metadata and safe stream events.
        """
        return self.stream_safe_response_for_text(
            chat_id=chat_id,
            text=self.build_document_text(document_id),
            model=model,
            settings=settings,
            persisted_replacements=persisted_replacements or {},
            log_prefix="ORCHESTRATOR document",
        )

    def build_document_text(self, document_id: str) -> str:
        """Build the text that enters the safe response pipeline.

        Args:
            document_id (str): The processed document identifier.

        Returns:
            str: The prompt-only, document-only, or combined prompt text.

        Raises:
            KeyError: If the processed document is unknown.
            ValueError: If both prompt and extracted text are empty.
        """
        document_context = self._document_registry.get(document_id)

        text = self._build_document_prompt(document_context)
        if not text.strip():
            raise ValueError("Document processor returned empty text.")

        return text

    def stream_safe_response_for_text(
        self,
        chat_id: str,
        text: str,
        model: str,
        log_prefix: str,
        settings: dict[str, str] | None = None,
        history: list[AssistantMessage] | None = None,
        persisted_replacements: dict[str, str] | None = None,
    ) -> tuple[AnonymizedPrompt, Iterator[dict[str, Any]]]:
        """Run text through privacy-shield, assistant, and restoration.

        Args:
            chat_id (str): The chat that owns the request.
            text (str): The original text to protect and answer.
            model (str): The AI model selected by the user.
            log_prefix (str): The prefix used in diagnostic logs.

        Returns:
            tuple[AnonymizedPrompt, Iterator[dict[str, Any]]]: The anonymized
            text metadata and safe stream events.
        """
        started_at = time.perf_counter()
        anonymized_prompt = self._container.privacy_shield.anonymize(
            chat_id=chat_id,
            text=text,
            settings=settings,
        )
        self._anonymization_registry.store(anonymized_prompt, chat_id)
        print(
            f"{log_prefix} anonymize done "
            f"elapsed={time.perf_counter() - started_at:.3f}s "
            f"replacement_count={anonymized_prompt.replacement_count}",
            flush=True,
        )
        return (
            anonymized_prompt,
            self._stream_response_from_ai_gateway(
                chat_id=chat_id,
                anonymized_prompt=anonymized_prompt.text,
                model=model,
                history=history or [],
                replacements=self._build_response_replacements(
                    chat_id=chat_id,
                    persisted_replacements=persisted_replacements or {},
                    current_replacements=anonymized_prompt.replacements,
                ),
            ),
        )

    def _build_response_replacements(
        self,
        chat_id: str,
        persisted_replacements: dict[str, str],
        current_replacements: dict[str, str],
    ) -> dict[str, str]:
        """Build replacements for deanonymizing a response.

        Args:
            chat_id (str): The chat that owns the response.
            current_replacements (dict[str, str]): Replacements from the
                current anonymization.

        Returns:
            dict[str, str]: Accumulated chat replacements plus current ones.
        """
        replacements = dict(persisted_replacements)
        replacements.update(self._anonymization_registry.get_for_chat(chat_id))
        replacements.update(current_replacements)
        return replacements

    def _stream_response_from_ai_gateway(
        self,
        chat_id: str,
        anonymized_prompt: str,
        model: str,
        history: list[AssistantMessage],
        replacements: dict[str, str],
    ) -> Iterator[dict[str, Any]]:
        """Stream ai-gateway chunks and deanonymize them on the fly.

        Args:
            chat_id (str): The chat that owns the request.
            anonymized_prompt (str): The anonymized prompt sent to the
                assistant.
            model (str): The AI model selected by the user.
            history (list[AssistantMessage]): Previous anonymized messages.
            replacements (dict[str, str]): The replacement mappings for
                deanonymization.

        Returns:
            Iterator[dict[str, Any]]: Safe response stream events.
        """

        def stream_events() -> Iterator[dict[str, Any]]:
            started_at = time.perf_counter()
            chunk_count = 0
            anonymized_chunks: list[str] = []
            buffer = ""

            for chunk in self._container.ai_gateway.stream_response(
                AssistantStreamRequest(
                    chat_id=chat_id,
                    messages=[
                        *history,
                        AssistantMessage(
                            role="user",
                            content=anonymized_prompt,
                        ),
                    ],
                    model=model,
                )
            ):
                if not chunk:
                    continue

                chunk_count += 1
                anonymized_chunks.append(chunk)
                safe_text, buffer = self._deanonymize_stream_fragment(
                    current_buffer=buffer,
                    fragment=chunk,
                    replacements=replacements,
                )
                if safe_text:
                    yield {
                        "event": "chunk",
                        "content": safe_text,
                    }

            remaining_text = self._flush_deanonymization_buffer(
                current_buffer=buffer,
                replacements=replacements,
            )
            if remaining_text:
                yield {
                    "event": "chunk",
                    "content": remaining_text,
                }

            print(
                "ORCHESTRATOR ai-gateway stream done "
                f"elapsed={time.perf_counter() - started_at:.3f}s "
                f"chunk_count={chunk_count}",
                flush=True,
            )
            yield {
                "event": "anonymized_response",
                "content": "".join(anonymized_chunks),
            }
            yield {"event": "completed"}

        return stream_events()

    def _deanonymize_stream_fragment(
        self,
        current_buffer: str,
        fragment: str,
        replacements: dict[str, str],
    ) -> tuple[str, str]:
        """Restore one streamed fragment while protecting partial tags.

        Args:
            current_buffer (str): Text buffered from previous incomplete tags.
            fragment (str): The newly received assistant chunk.
            replacements (dict[str, str]): Placeholder replacement map.

        Returns:
            tuple[str, str]: Safe text ready to emit and the updated buffer.
        """
        combined = current_buffer + fragment
        match = self._partial_placeholder_pattern.search(combined)

        if match:
            safe_text = combined[:match.start()]
            next_buffer = combined[match.start():]
        else:
            safe_text = combined
            next_buffer = ""

        for placeholder, original in replacements.items():
            safe_text = safe_text.replace(placeholder, original)

        return safe_text, next_buffer

    def _flush_deanonymization_buffer(
        self,
        current_buffer: str,
        replacements: dict[str, str],
    ) -> str:
        """Flush remaining buffered placeholder text at the end of a stream.

        Args:
            current_buffer (str): The remaining buffered text.
            replacements (dict[str, str]): Placeholder replacement map.

        Returns:
            str: The final safe text.
        """
        flushed = current_buffer
        for placeholder, original in replacements.items():
            flushed = flushed.replace(placeholder, original)
        return flushed

    def _build_anonymized_pdf_filename(self, filename: str) -> str:
        """Build the filename used for the anonymized PDF preview.

        Args:
            filename (str): The original filename.

        Returns:
            str: The anonymized PDF filename.
        """
        if filename.lower().endswith(".pdf"):
            return f"{filename[:-4]}_anonimizado.pdf"

        return f"{filename}_anonimizado.pdf"

    def _build_document_prompt(
        self,
        document_context: ProcessedDocumentContext,
    ) -> str:
        """Build the prompt sent into the safe response pipeline.

        Args:
            document_context (ProcessedDocumentContext): The stored document
                data.

        Returns:
            str: The combined prompt and document text.
        """
        prompt = document_context.prompt.strip()
        extracted_text = document_context.extracted_text.strip()

        if prompt and extracted_text:
            return (
                "User prompt:\n"
                f"{prompt}\n\n"
                "Document text:\n"
                f"{extracted_text}"
            )

        return prompt or extracted_text
