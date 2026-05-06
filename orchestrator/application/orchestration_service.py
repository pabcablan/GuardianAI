"""Application service that coordinates GuardianAI module calls."""
from __future__ import annotations

import time
from collections.abc import Iterator
from typing import Any

from application.services.anonymization_registry import AnonymizationRegistry
from application.services.document_registry import DocumentRegistry
from domain.anonymized_pdf_preview import AnonymizedPdfPreview
from domain.processed_document import ProcessedDocumentContext
from infrastructure.dependency_container import OrchestratorContainer
from infrastructure.ports.ai_gateway_port import AssistantStreamRequest
from infrastructure.ports.document_processor_port import DocumentUploadRequest
from infrastructure.ports.privacy_shield_port import AnonymizedPrompt


class OrchestrationService:
    """Coordinate document processing, anonymization, assistant, and restore."""

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
        )
        self._anonymization_registry.store(anonymized_prompt)
        return anonymized_prompt

    def preview_document_anonymization(
        self,
        chat_id: str,
        document_id: str,
    ) -> AnonymizedPrompt:
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
        )
        self._anonymization_registry.store(anonymized_prompt)
        return anonymized_prompt

    def stream_anonymized_response(
        self,
        chat_id: str,
        anonymized_text: str,
        anonymization_id: str,
        model: str,
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
        assistant_chunks = self._collect_ai_gateway_chunks(
            chat_id=chat_id,
            anonymized_prompt=anonymized_text,
            model=model,
        )
        return self._stream_response_from_anonymized_chunks(
            assistant_chunks=assistant_chunks,
            replacements=self._anonymization_registry.get(anonymization_id),
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
        )
        self._anonymization_registry.store(anonymized_prompt)
        print(
            f"{log_prefix} anonymize done "
            f"elapsed={time.perf_counter() - started_at:.3f}s "
            f"replacement_count={anonymized_prompt.replacement_count}",
            flush=True,
        )
        started_at = time.perf_counter()
        assistant_chunks = self._collect_ai_gateway_chunks(
            chat_id=chat_id,
            anonymized_prompt=anonymized_prompt.text,
            model=model,
        )
        print(
            f"{log_prefix} ai-gateway done "
            f"elapsed={time.perf_counter() - started_at:.3f}s "
            f"chunk_count={len(assistant_chunks)}",
            flush=True,
        )
        return (
            anonymized_prompt,
            self._stream_response_from_anonymized_chunks(
                assistant_chunks=assistant_chunks,
                replacements=anonymized_prompt.replacements,
            ),
        )

    def _collect_ai_gateway_chunks(
        self,
        chat_id: str,
        anonymized_prompt: str,
        model: str,
    ) -> list[str]:
        """Collect assistant chunks from the configured ai-gateway.

        Args:
            chat_id (str): The chat that owns the request.
            anonymized_prompt (str): The anonymized prompt sent to the
                assistant.
            model (str): The AI model selected by the user.

        Returns:
            list[str]: The anonymized assistant response chunks.
        """
        return [
            chunk
            for chunk in self._container.ai_gateway.stream_response(
                AssistantStreamRequest(
                    chat_id=chat_id,
                    prompt=anonymized_prompt,
                    model=model,
                )
            )
            if chunk
        ]

    def _stream_response_from_anonymized_chunks(
        self,
        assistant_chunks: list[str],
        replacements: dict[str, str],
    ) -> Iterator[dict[str, Any]]:
        """Restore assistant chunks through privacy-shield.

        Args:
            assistant_chunks (list[str]): The anonymized assistant chunks.
            replacements (dict[str, str]): The replacement mappings for
                deanonymization.

        Returns:
            Iterator[dict[str, Any]]: Safe response stream events.
        """
        return self._container.privacy_shield.deanonymize_stream(
            chunks=assistant_chunks,
            replacements=replacements,
        )

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
