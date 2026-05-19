from infrastructure.adapters.anonymization.optimized_api_anonymizer import (
    OptimizedApiAnonymizer,
)
from infrastructure.ports.anonymizer import Anonymizer


class AnonymizerProvider:
    """Build and cache API-backed anonymizer implementations."""

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self._cache: dict[str, Anonymizer] = {}

    def get_anonymizer(self, model_alias: str | None = None) -> Anonymizer:
        """Return a cached API anonymizer for the requested model alias.

        Args:
            model_alias (str | None): Logical model name exposed by model-provider.

        Returns:
            Anonymizer: Cached anonymizer instance bound to that model alias.
        """
        cache_key = model_alias or "default"

        if cache_key not in self._cache:
            self._cache[cache_key] = OptimizedApiAnonymizer(
                api_url=self.kwargs["api_url"],
                model_name=model_alias,
                client=self.kwargs.get("client"),
            )

        return self._cache[cache_key]
