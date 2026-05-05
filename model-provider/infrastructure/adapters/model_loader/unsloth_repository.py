"""Adapter that loads and stores models through Unsloth."""
from __future__ import annotations

import threading
from typing import Any

from unsloth import FastLanguageModel

from infrastructure.ports.model_repository import ModelRepository


class UnslothLoader(ModelRepository):
    """Load Unsloth models and expose them by application names."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one loader instance owns the loaded model registry."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._models = {}
                    cls._instance._tokenizers = {}
                    cls._instance._model_ids = {}

        return cls._instance

    async def load(self, model_id: str, name: str, **kwargs) -> tuple[Any, Any]:
        """Load a model or reuse an already loaded model with the same id.

        Args:
            model_id (str): The Unsloth model identifier.
            name (str): The application name assigned to the loaded model.
            **kwargs: Optional Unsloth loading parameters.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer.

        Raises:
            ValueError: If the model identifier is not an Unsloth model.
        """
        normalized_model_id = model_id.strip()
        if not normalized_model_id.startswith("unsloth/"):
            raise ValueError("UnslothLoader only supports unsloth/ model ids.")

        if name in self._models:
            print(f"'{name}' already loaded, skipping.")
            return self._models[name], self._tokenizers[name]

        existing_name = self._find_loaded_model_name(normalized_model_id)
        if existing_name is not None:
            self._models[name] = self._models[existing_name]
            self._tokenizers[name] = self._tokenizers[existing_name]
            self._model_ids[name] = normalized_model_id
            print(f"'{name}' now reuses loaded model '{existing_name}'.")
            return self._models[name], self._tokenizers[name]

        print(f"Downloading/loading '{normalized_model_id}' ...")
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=normalized_model_id,
            max_seq_length=kwargs.get("max_seq_length", 4096),
            dtype=kwargs.get("dtype"),
            load_in_4bit=kwargs.get("load_in_4bit", True),
        )

        FastLanguageModel.for_inference(model)
        model.eval()

        self._models[name] = model
        self._tokenizers[name] = tokenizer
        self._model_ids[name] = normalized_model_id
        print(f"'{name}' ready on (Unsloth).")

        return self._models[name], self._tokenizers[name]

    async def get(self, name: str) -> tuple[Any, Any]:
        """Retrieve a loaded model and tokenizer by name.

        Args:
            name (str): The application model name.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer.

        Raises:
            ValueError: If the requested model is not loaded.
        """
        if name not in self._models:
            raise ValueError(f"'{name}' not loaded. Call load() first.")

        return self._models[name], self._tokenizers[name]

    async def unload(self, name: str) -> None:
        """Unload one model name from the registry.

        Args:
            name (str): The application model name to unload.
        """
        if name not in self._models:
            return

        del self._models[name]
        del self._tokenizers[name]
        del self._model_ids[name]
        print(f"'{name}' unloaded.")

    async def list_loaded_models(self) -> list[dict[str, str]]:
        """List all loaded model names and identifiers.

        Returns:
            list[dict[str, str]]: The loaded model metadata.
        """
        return [
            {"name": name, "model_id": self._model_ids[name]}
            for name in self._models
        ]

    def _find_loaded_model_name(self, model_id: str) -> str | None:
        """Find the first loaded name for a model identifier.

        Args:
            model_id (str): The normalized model identifier.

        Returns:
            str | None: The loaded model name, if it exists.
        """
        for loaded_name, loaded_model_id in self._model_ids.items():
            if loaded_model_id == model_id:
                return loaded_name

        return None
