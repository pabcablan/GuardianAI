import time

from infrastructure.ports.deanonymizer import Deanonymizer


class DeanonymizationSessionRegistry:
    """Store active deanonymization sessions inside privacy-shield."""

    def __init__(self, session_ttl_seconds: float = 900.0) -> None:
        """Initialize the registry for stateful deanonymization sessions.

        Args:
            session_ttl_seconds (float): Maximum idle lifetime for one active
                session before it is discarded automatically.
        """
        self._deanonymizers: dict[str, Deanonymizer] = {}
        self._replacements: dict[str, dict[str, str]] = {}
        self._last_seen_at: dict[str, float] = {}
        self._session_ttl_seconds = session_ttl_seconds

    def start(
        self,
        session_id: str,
        deanonymizer: Deanonymizer,
        replacements: dict[str, str],
    ) -> None:
        """Register a new deanonymization session.

        Args:
            session_id (str): The unique session identifier.
            deanonymizer (Deanonymizer): The stateful deanonymizer instance.
            replacements (dict[str, str]): Placeholder replacement mappings.

        Raises:
            ValueError: If the session identifier is already active.
        """
        self._prune_expired_sessions()
        if session_id in self._deanonymizers:
            raise ValueError(
                f"Deanonymization session '{session_id}' already exists."
            )
        self._deanonymizers[session_id] = deanonymizer
        self._replacements[session_id] = dict(replacements)
        self._last_seen_at[session_id] = time.monotonic()

    def restore_chunk(self, session_id: str, chunk: str) -> str:
        """Restore one streamed chunk for an active session.

        Args:
            session_id (str): The active session identifier.
            chunk (str): The incoming anonymized chunk.

        Returns:
            str: The restored safe text that can be emitted immediately.

        Raises:
            KeyError: If the session is unknown.
        """
        self._prune_expired_sessions()
        deanonymizer = self._deanonymizers[session_id]
        replacements = self._replacements[session_id]
        self._last_seen_at[session_id] = time.monotonic()
        return deanonymizer.deanonymize(chunk, replacements)

    def flush(self, session_id: str) -> str:
        """Flush and close an active deanonymization session.

        Args:
            session_id (str): The active session identifier.

        Returns:
            str: Any remaining restored buffered text.

        Raises:
            KeyError: If the session is unknown.
        """
        self._prune_expired_sessions()
        deanonymizer = self._deanonymizers.pop(session_id)
        replacements = self._replacements.pop(session_id)
        self._last_seen_at.pop(session_id, None)
        return deanonymizer.flush(replacements)

    def _prune_expired_sessions(self) -> None:
        """Remove idle sessions whose lifetime has exceeded the TTL."""
        now = time.monotonic()
        expired_session_ids = [
            session_id
            for session_id, last_seen_at in self._last_seen_at.items()
            if now - last_seen_at > self._session_ttl_seconds
        ]

        for session_id in expired_session_ids:
            self._deanonymizers.pop(session_id, None)
            self._replacements.pop(session_id, None)
            self._last_seen_at.pop(session_id, None)
