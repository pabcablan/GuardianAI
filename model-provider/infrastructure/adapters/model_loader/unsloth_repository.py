"""Load text models through the Unsloth library."""
from __future__ import annotations

import os
import threading
from typing import Any

from infrastructure.ports.model_repository import ModelRepository

# Avoid Torch Dynamo/FX tracing conflicts when Unsloth patches the model for
# inference. These values must be set before importing Unsloth.
os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
os.environ.setdefault("UNSLOTH_COMPILE_DISABLE", "1")


class UnslothLoader(ModelRepository):
    """Load and store text models optimized by Unsloth."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one Unsloth loader instance exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._models = {}
                    cls._instance._tokenizers = {}
                    cls._instance._model_ids = {}
        return cls._instance

    async def load(self, model_id: str, name: str, **kwargs) -> tuple[Any, Any]:
        """
        Load a model given its identifier and optional parameters using Unsloth.

        Args:
            model_id (str): The Unsloth model identifier.
            name (str): The model registry name.
            **kwargs: Additional Unsloth loading options.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer.
        """
        if not model_id.startswith("unsloth/"):
            raise ValueError(
                "UnslothLoader only accepts model identifiers starting "
                "with 'unsloth/'."
            )

        if name not in self._models:
            print(f"Downloading/loading '{model_id}' through Unsloth ...")
            model, tokenizer = self._load_language_model(model_id, **kwargs)
            self._models[name] = model
            self._tokenizers[name] = tokenizer
            self._model_ids[name] = model_id
            print(f"'{name}' ready on Unsloth.")
        else:
            print(f"'{name}' already loaded, skipping.")

        return self._models[name], self._tokenizers[name]

    def _load_language_model(
        self,
        model_id: str,
        **kwargs,
    ) -> tuple[Any, Any]:
        """Load a language model from Unsloth.

        Args:
            model_id (str): The Unsloth model identifier.
            **kwargs: Additional Unsloth loading options.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer.
        """
        from unsloth import FastLanguageModel

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_id,
            max_seq_length=kwargs.get("max_seq_length", 4096),
            dtype=kwargs.get("dtype", None),
            load_in_4bit=kwargs.get("load_in_4bit", True),
        )
        FastLanguageModel.for_inference(model)
        model.eval()
        return model, tokenizer

    async def get(self, name: str) -> tuple[Any, Any]:
        """Retrieve a loaded model and tokenizer by name.

        Args:
            name (str): The model registry name.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer.
        """
        if name not in self._models:
            raise ValueError(f"'{name}' not loaded. Call load() first.")
        return self._models[name], self._tokenizers[name]

    async def unload(self, name: str):
        """
        Unload a model and its tokenizer by name.

        Args:
            name (str): The model registry name.
        """
        if name in self._models:
            del self._models[name]
            del self._tokenizers[name]
            del self._model_ids[name]
            print(f"'{name}' unloaded.")

    async def list_loaded_models(self) -> list[dict[str, str]]:
        """
         List all currently loaded models.

        Returns:
            list[dict[str, str]]: The loaded model metadata.
        """
        return [
            {
                "name": name,
                "model_id": self._model_ids[name],
                "kind": "unsloth",
            }
            for name in self._models.keys()
        ]
