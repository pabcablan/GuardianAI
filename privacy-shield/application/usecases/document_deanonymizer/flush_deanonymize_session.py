from application.services.deanonymization_session_registry import (
    DeanonymizationSessionRegistry,
)


class FlushDeanonymizeSession:
    """Flush and close one active deanonymization session."""

    def __init__(self, registry: DeanonymizationSessionRegistry) -> None:
        """Initialize the flush-session use case.

        Args:
            registry (DeanonymizationSessionRegistry): The active session
                registry.
        """
        self._registry = registry

    def execute(self, session_id: str) -> dict[str, str]:
        """Flush and close one active session.

        Args:
            session_id (str): The active session identifier.

        Returns:
            dict[str, str]: Payload containing any remaining restored content.
        """
        return {"content": self._registry.flush(session_id)}
