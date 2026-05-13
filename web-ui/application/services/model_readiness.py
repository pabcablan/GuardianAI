"""Check whether the required backend models are ready."""
from __future__ import annotations

import httpx


class ModelReadinessService:
    """Query model-provider readiness for the models used by web-ui."""

    def __init__(
        self,
        base_url: str,
        privacy_model_name: str,
        document_model_name: str,
        timeout_seconds: float,
    ) -> None:
        self._base_url = base_url
        self._privacy_model_name = privacy_model_name
        self._document_model_name = document_model_name
        self._timeout_seconds = timeout_seconds

    def get_readiness(self) -> dict[str, object]:
        """Return whether the required models are loaded."""
        model_names = [self._privacy_model_name]
        if self._document_model_name != self._privacy_model_name:
            model_names.append(self._document_model_name)

        statuses: dict[str, str] = {}
        try:
            with httpx.Client(
                base_url=self._base_url,
                timeout=self._timeout_seconds,
            ) as client:
                for model_name in model_names:
                    response = client.get(
                        "/model_status",
                        params={"name": model_name},
                    )
                    response.raise_for_status()
                    statuses[model_name] = str(response.json())
        except httpx.HTTPError as error:
            return {
                "ready": False,
                "message": "El proveedor de modelos aún no está disponible.",
                "detail": str(error),
                "models": statuses,
            }

        missing_models = [
            name
            for name, status_text in statuses.items()
            if " is loaded." not in status_text
        ]
        if missing_models:
            return {
                "ready": False,
                "message": "Cargando modelos de GuardianAI...",
                "models": statuses,
            }

        return {
            "ready": True,
            "message": "Modelos listos.",
            "models": statuses,
        }
