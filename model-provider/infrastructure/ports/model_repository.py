"""Port that defines model loading operations."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelRepository(ABC):
    """Define the contract for model repositories."""

    @abstractmethod
    def load(self, model_id: str, name: str, **kwargs) -> tuple[Any, Any]:
        """Load a model given its identifier and optional parameters.

        Args:
            model_id (str): The model identifier.
            name (str): The model registry name.
            **kwargs: Additional loading parameters.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer or processor.
        """
        raise NotImplementedError

    @abstractmethod
    def get(self, name: str) -> tuple[Any, Any]:
        """Get a loaded model and tokenizer or processor by name.

        Args:
            name (str): The model registry name.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer or processor.
        """
        raise NotImplementedError

    @abstractmethod
    def unload(self, name: str) -> None:
        """Unload a model by name.

        Args:
            name (str): The model registry name.
        """
        raise NotImplementedError

    @abstractmethod
    def list_loaded_models(self) -> list[dict[str, str]]:
        """List all currently loaded models.

        Returns:
            list[dict[str, str]]: Loaded model metadata.
        """
        raise NotImplementedError
