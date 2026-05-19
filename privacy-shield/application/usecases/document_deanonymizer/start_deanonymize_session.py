from collections.abc import Callable

from application.services.deanonymization_session_registry import (
    DeanonymizationSessionRegistry,
)
from infrastructure.ports.deanonymizer import Deanonymizer


class StartDeanonymizeSession:
    """Open a new stateful deanonymization session."""

    def __init__(
        self,
        registry: DeanonymizationSessionRegistry,
        deanonymizer_factory: Callable[[], Deanonymizer],
    ) -> None:
        """Initialize the start-session use case.

        Args:
            registry (DeanonymizationSessionRegistry): The active session
                registry.
            deanonymizer_factory (Callable[[], Deanonymizer]): Factory used to
                create one deanonymizer per session.
        """
        self._registry = registry
        self._deanonymizer_factory = deanonymizer_factory

    def execute(
        self,
        session_id: str,
        replacements: dict[str, str],
    ) -> dict[str, str]:
        """Register a new deanonymization session.

        Args:
            session_id (str): The unique session identifier.
            replacements (dict[str, str]): Placeholder replacement mappings.

        Returns:
            dict[str, str]: Confirmation payload with the opened session id.
        """
        self._registry.start(
            session_id=session_id,
            deanonymizer=self._deanonymizer_factory(),
            replacements=replacements,
        )
        return {"session_id": session_id}
