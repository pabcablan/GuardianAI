"""Load text and vision-language models through HuggingFace Transformers."""
from __future__ import annotations

import threading
from typing import Any

from infrastructure.ports.model_repository import ModelRepository


class TransformersLoader(ModelRepository):
    """Load and store models through the Transformers library."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one Transformers loader instance exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._models = {}
                    cls._instance._tokenizers = {}
                    cls._instance._model_ids = {}
                    cls._instance._model_kinds = {}
        return cls._instance

    def load(self, model_id: str, name: str, **kwargs) -> tuple[Any, Any]:
        """Load a model using Transformers.

        Args:
            model_id (str): The HuggingFace model identifier.
            name (str): The model registry name.
            **kwargs: Additional Transformers loading options.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer or processor.
        """
        if name not in self._models:
            model_kind = self._resolve_model_kind(model_id, kwargs)
            print(
                f"Loading '{model_id}' via Transformers ({model_kind})..."
            )

            if model_kind == "vision":
                model, tokenizer = self._load_vision_model(model_id, **kwargs)
            else:
                model, tokenizer = self._load_language_model(model_id, **kwargs)

            self._models[name] = model
            self._tokenizers[name] = tokenizer
            self._model_ids[name] = model_id
            self._model_kinds[name] = model_kind
            print(f"'{name}' ready on Transformers ({model_kind}).")
        else:
            print(f"'{name}' already loaded, skipping.")

        return self._models[name], self._tokenizers[name]

    def _resolve_model_kind(
        self,
        model_id: str,
        kwargs: dict[str, Any],
    ) -> str:
        """Resolve whether the model should be loaded as text or vision.

        Args:
            model_id (str): The model identifier.
            kwargs (dict[str, Any]): Loading options.

        Returns:
            str: ``vision`` for VLMs, otherwise ``text``.
        """
        if kwargs.pop("is_vision_model", False):
            return "vision"

        lowered_model_id = model_id.lower()
        if "-vl" in lowered_model_id or "vision" in lowered_model_id:
            return "vision"

        return "text"

    def _load_language_model(self, model_id: str, **kwargs) -> tuple[Any, Any]:
        """Load a causal language model using Transformers.

        Args:
            model_id (str): The model identifier.
            **kwargs: Additional Transformers loading options.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer.
        """
        from transformers import AutoModelForCausalLM, AutoTokenizer

        gpu_index = kwargs.get("gpu_index")
        device_map = {"": f"cuda:{gpu_index}"} if gpu_index is not None else "auto"
        trust_remote_code = kwargs.get("trust_remote_code", True)
        tokenizer = AutoTokenizer.from_pretrained(
            model_id,
            trust_remote_code=trust_remote_code,
        )
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            device_map=device_map,
            quantization_config=self._build_quantization_config(kwargs),
            trust_remote_code=trust_remote_code,
        )
        model.eval()
        return model, tokenizer

    def _load_vision_model(self, model_id: str, **kwargs) -> tuple[Any, Any]:
        """Load a vision-language model using Transformers.

        Args:
            model_id (str): The model identifier.
            **kwargs: Additional Transformers loading options.

        Returns:
            tuple[Any, Any]: The loaded model and processor.
        """
        from transformers import AutoModelForImageTextToText, AutoProcessor

        trust_remote_code = kwargs.get("trust_remote_code", True)
        load_kwargs: dict[str, Any] = {
            "device_map": kwargs.get("device_map", "auto"),
            "torch_dtype": kwargs.get("torch_dtype", "auto"),
            "trust_remote_code": trust_remote_code,
        }
        quantization_config = self._build_quantization_config(kwargs)
        if quantization_config is not None:
            load_kwargs["quantization_config"] = quantization_config

        processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=trust_remote_code,
        )
        model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            **load_kwargs,
        )
        model.eval()
        return model, processor

    def _build_quantization_config(self, kwargs: dict[str, Any]) -> Any | None:
        """Build an optional Transformers quantization config.

        Args:
            kwargs (dict[str, Any]): Loading options.

        Returns:
            Any | None: A BitsAndBytesConfig instance or ``None``.
        """
        raw_config = kwargs.get("quantization_config")
        if raw_config:
            from transformers import BitsAndBytesConfig

            return BitsAndBytesConfig(**raw_config)

        if not kwargs.get("load_in_4bit", False):
            return None

        try:
            import torch
            from transformers import BitsAndBytesConfig

            return BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=torch.bfloat16,
            )
        except Exception:
            return None

    def get(self, name: str) -> tuple[Any, Any]:
        """Retrieve a loaded model and tokenizer or processor by name.

        Args:
            name (str): The model registry name.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer or processor.
        """
        if name not in self._models:
            raise ValueError(f"'{name}' not loaded. Call load() first.")
        return self._models[name], self._tokenizers[name]

    def unload(self, name: str) -> None:
        """Unload a model and tokenizer or processor by name.

        Args:
            name (str): The model registry name.
        """
        if name in self._models:
            del self._models[name]
            del self._tokenizers[name]
            del self._model_ids[name]
            del self._model_kinds[name]
            print(f"'{name}' unloaded.")

    def list_loaded_models(self) -> list[dict[str, str]]:
        """List all models loaded by this loader.

        Returns:
            list[dict[str, str]]: The loaded model metadata.
        """
        return [
            {
                "name": name,
                "model_id": self._model_ids[name],
                "kind": self._model_kinds[name],
            }
            for name in self._models.keys()
        ]
