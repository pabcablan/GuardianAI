from dataclasses import dataclass
from datetime import datetime, UTC
from ..value_objects.session_id import SessionId


@dataclass
class Session:
    user_id: str
    org_id: str
    session_id: SessionId
    expiry: datetime

    def is_expired(self) -> bool:
        return datetime.now(UTC) > self.expiry