class SessionNotFoundError(Exception):
    def __init__(self, session_id: str):
        super().__init__(f"Session {session_id} not found or has expired")
        self.session_id = session_id


class ProviderError(Exception):
    def __init__(self, message: str):
        super().__init__(message)


class ProviderRateLimitError(ProviderError):
    def __init__(self, message: str):
        super().__init__(message)


class ProviderConnectionError(ProviderError):
    def __init__(self, message: str):
        super().__init__(message)


class ProviderAPIError(ProviderError):
    def __init__(self, message: str):
        super().__init__(message)