from datetime import datetime, timedelta, UTC
from domain.entities.session import Session
from domain.value_objects.session_id import SessionId
from domain.exceptions import SessionNotFoundError
from application.ports.session_manager import SessionManager


class MemorySessionManager(SessionManager):
    def __init__(self, session_ttl_minutes: int = 60):
        self._sessions: dict[str, Session] = {}
        self._session_ttl_minutes = session_ttl_minutes

    def create(self, user_id: str, org_id: str) -> Session:
        session_id = SessionId.generate()
        session = Session(
            user_id=user_id,
            org_id=org_id,
            session_id=session_id,
            expiry=datetime.now(UTC) + timedelta(minutes=self._session_ttl_minutes)
        )
        self._sessions[str(session_id)] = session
        return session

    def validate(self, session_id: SessionId) -> Session:
        session = self._sessions.get(str(session_id))
        if not session:
            raise SessionNotFoundError(str(session_id))
        if session.is_expired():
            del self._sessions[str(session_id)]
            raise SessionNotFoundError(str(session_id))
        return session