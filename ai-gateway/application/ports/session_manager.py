from abc import ABC, abstractmethod
from domain.entities.session import Session
from domain.value_objects.session_id import SessionId


class SessionManager(ABC):

    @abstractmethod
    def create(self, user_id: str, org_id: str) -> Session:
        ...

    @abstractmethod
    def validate(self, session_id: SessionId) -> Session:
        ...