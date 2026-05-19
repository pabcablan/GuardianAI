from application.services.deanonymization_session_registry import (
    DeanonymizationSessionRegistry,
)


class DeanonymizeSessionChunk:
    """Restore one chunk within an existing deanonymization session."""

    def __init__(self, registry: DeanonymizationSessionRegistry) -> None:
        """Initialize the chunk restoration use case.

        Args:
            registry (DeanonymizationSessionRegistry): The active session
                registry.
        """
        self._registry = registry

    def execute(self, session_id: str, chunk: str) -> dict[str, str]:
        """Restore one streamed chunk for an active session.

        Args:
            session_id (str): The active session identifier.
            chunk (str): The incoming anonymized chunk.

        Returns:
            dict[str, str]: Payload containing the restored chunk content.
        """
        return {
            "content": self._registry.restore_chunk(
                session_id=session_id,
                chunk=chunk,
            )
        }
