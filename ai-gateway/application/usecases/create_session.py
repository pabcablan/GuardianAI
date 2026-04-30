from ..ports import SessionManager
from domain.entities import Session

class CreateSession:
    def __init__(self, session_manager: SessionManager):
        self._session_manager = session_manager

    def execute(self, user_id: str, org_id: str) -> Session:
        session = self._session_manager.create(user_id, org_id)
        return session