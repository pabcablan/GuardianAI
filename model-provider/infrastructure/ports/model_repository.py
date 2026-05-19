"""Port for loading, retrieving, and unloading runtime models."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ModelRepository(ABC):
    """Define the model lifecycle operations used by model-provider."""

    @abstractmethod
    async def load(
        self,
        model_id: str,
        name: str,
        **kwargs: Any,
    ) -> tuple[Any, Any]:
        """Load one model and its paired processor.

        Args:
            model_id (str): The source identifier of the model to load.
            name (str): The runtime name assigned to the loaded model.
            **kwargs (Any): Loader-specific options such as quantization or
                sequence length.

        Returns:
            tuple[Any, Any]: The loaded model and processor objects.
        """
        ...

    @abstractmethod
    async def get(self, name: str) -> tuple[Any, Any]:
        """Return one previously loaded model and processor.

        Args:
            name (str): The runtime name of the loaded model.

        Returns:
            tuple[Any, Any]: The loaded model and processor objects.
        """
        ...

    @abstractmethod
    async def unload(self, name: str) -> None:
        """Unload one model and processor from memory.

        Args:
            name (str): The runtime name of the loaded model.
        """
        ...

    @abstractmethod
    async def list_loaded_models(self) -> list[dict[str, str]]:
        """Return the registry of currently loaded models.

        Returns:
            list[dict[str, str]]: Loaded model names and identifiers.
        """
        ...
