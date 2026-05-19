"""Model repository backed by Unsloth vision-capable runtimes."""
from __future__ import annotations

import logging
import threading
from typing import Any

from unsloth import FastVisionModel

from infrastructure.ports.model_repository import ModelRepository


LOGGER = logging.getLogger(__name__)


class UnslothLoader(ModelRepository):
    """Load, cache, and unload models through Unsloth."""

    _instance: "UnslothLoader | None" = None
    _lock = threading.Lock()

    def __new__(cls) -> "UnslothLoader":
        """Return the singleton runtime loader instance.

        Returns:
            UnslothLoader: The shared loader instance.
        """
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._models = {}
                    cls._instance._processors = {}
                    cls._instance._model_ids = {}
        return cls._instance

    async def load(
        self,
        model_id: str,
        name: str,
        **kwargs: Any,
    ) -> tuple[Any, Any]:
        """Load one Unsloth model and cache it by runtime name.

        Args:
            model_id (str): The source model identifier.
            name (str): The runtime name assigned to the model.
            **kwargs (Any): Optional Unsloth loader settings such as sequence
                length, dtype, or 4-bit loading.

        Returns:
            tuple[Any, Any]: The loaded model and processor.
        """
        if name in self._models:
            LOGGER.info("Model '%s' already loaded, skipping.", name)
            return self._models[name], self._processors[name]

        if not model_id.startswith("unsloth/"):
            raise ValueError(
                f"Unsupported model provider for '{model_id}'.",
            )

        LOGGER.info("Loading Unsloth model '%s' from '%s'.", name, model_id)

        max_seq_length = kwargs.get("max_seq_length", 4096)
        dtype = kwargs.get("dtype")
        load_in_4bit = kwargs.get("load_in_4bit", True)

        model, processor = FastVisionModel.from_pretrained(
            model_name=model_id,
            max_seq_length=max_seq_length,
            dtype=dtype,
            load_in_4bit=load_in_4bit,
        )

        FastVisionModel.for_inference(model)
        model.eval()

        self._processors[name] = processor
        self._models[name] = model
        self._model_ids[name] = model_id
        LOGGER.info("Model '%s' ready on Unsloth.", name)
        return model, processor

    async def get(self, name: str) -> tuple[Any, Any]:
        """Return one previously loaded model and processor.

        Args:
            name (str): The runtime name of the loaded model.

        Returns:
            tuple[Any, Any]: The loaded model and processor.

        Raises:
            ValueError: If the requested model is not loaded.
        """
        if name not in self._models:
            raise ValueError(f"'{name}' not loaded. Call load() first.")

        return self._models[name], self._processors[name]

    async def unload(self, name: str) -> None:
        """Unload one cached model and processor.

        Args:
            name (str): The runtime name of the loaded model.
        """
        if name in self._models:
            del self._models[name]
            del self._processors[name]
            del self._model_ids[name]
            LOGGER.info("Model '%s' unloaded.", name)

    async def list_loaded_models(self) -> list[dict[str, str]]:
        """Return the currently loaded runtime registry.

        Returns:
            list[dict[str, str]]: Loaded model names and source identifiers.
        """
        return [
            {"name": name, "model_id": self._model_ids[name]}
            for name in self._models
        ]
