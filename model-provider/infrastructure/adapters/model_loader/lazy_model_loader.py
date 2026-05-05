"""Lazy model loader adapter for model-provider."""
from __future__ import annotations

from typing import Any

from infrastructure.ports.model_repository import ModelRepository
from infrastructure.adapters.model_loader.model_loader_router import (
                ModelLoaderRouter,
            )

class LazyModelLoader(ModelRepository):
    """Import the model loader router only when a model operation is requested."""

    def __init__(self) -> None:
        """Initialize the lazy loader."""
        self._loader = None

    def _get_loader(self):
        """Return the real model loader router.

        Returns:
            ModelLoaderRouter: The concrete model loader router.
        """
        if self._loader is None:
            self._loader = ModelLoaderRouter()

        return self._loader

    async def load(self, model_id: str, name: str, **kwargs) -> tuple[Any, Any]:
        """Load a model through the concrete loader.

        Args:
            model_id (str): The model identifier.
            name (str): The model registry name.
            **kwargs: Additional loading options.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer or processor.
        """
        return await self._get_loader().load(model_id, name, **kwargs)

    async def get(self, name: str) -> tuple[Any, Any]:
        """Get a loaded model through the concrete loader.

        Args:
            name (str): The model registry name.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer or processor.
        """
        return await self._get_loader().get(name)

    async def unload(self, name: str) -> None:
        """Unload a model through the concrete loader.

        Args:
            name (str): The model registry name.
        """
        return await self._get_loader().unload(name)

    async def list_loaded_models(self) -> list[dict[str, str]]:
        """List loaded models through the concrete loader.

        Returns:
            list[dict[str, str]]: The loaded model metadata.
        """
        return await self._get_loader().list_loaded_models()


LazyUnslothLoader = LazyModelLoader
