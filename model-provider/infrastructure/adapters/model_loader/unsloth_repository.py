"""
Defines an adapter to load models using the Unsloth library.
It is responsible for loading models optimized for Unsloth given their identifier, managing the registry of loaded models and tokenizers.
"""

import threading
from typing import Any

# Avoid Torch Dynamo/FX tracing conflicts when Unsloth patches the model for
# inference. This must be set before importing Unsloth.
import os

os.environ.setdefault("TORCHDYNAMO_DISABLE", "1")
os.environ.setdefault("UNSLOTH_COMPILE_DISABLE", "1")

from infrastructure.ports.model_repository import ModelRepository


SHARED_MODEL_ALIASES = {
    "privacy_anonymizer": "document_extractor",
    "document_extractor": "privacy_anonymizer",
}


class UnslothLoader(ModelRepository):
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """
        Handles the Singleton pattern to ensure only one instance of the Provider exists.
        """
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
        """
        Load a model given its identifier and optional parameters using Unsloth.

        Args:
            model_id (str): The identifier of the model to load (e.g., Unsloth repo name).
            name (str): The name to assign to the loaded model.
            **kwargs: Additional parameters for loading the model.
                - max_seq_length (int, optional): The maximum sequence length for the model. Default is 4096.
                - dtype (str, optional): The data type to load the model with (e.g., "float16", "int8"). If not provided, the model will be loaded with its default data type.
                - load_in_4bit (bool, optional): Whether to load the model in 4-bit precision. Default is True.

        Returns:
            tuple[Any, Any]: A tuple containing the loaded model object and the corresponding tokenizer.
        """
        model_kind = self._resolve_model_kind(model_id, name, kwargs)
        if name not in self._models and model_id.startswith("unsloth/"):
            existing_name = self._find_loaded_model_name(model_id)
            if existing_name is not None:
                self._tokenizers[name] = self._tokenizers[existing_name]
                self._models[name] = self._models[existing_name]
                self._model_ids[name] = model_id
                self._model_kinds[name] = self._model_kinds[existing_name]
                print(
                    f"'{name}' now reuses loaded model '{existing_name}'."
                )
                return self._models[name], self._tokenizers[name]

            print(f"Downloading/loading '{model_id}' ...")

            if model_kind == "vision":
                model, tokenizer = self._load_vision_model(model_id, **kwargs)
            else:
                model, tokenizer = self._load_language_model(model_id, **kwargs)

            self._tokenizers[name] = tokenizer
            self._models[name] = model
            self._model_ids[name] = model_id
            self._model_kinds[name] = model_kind
            self._register_shared_alias(
                model_id=model_id,
                source_name=name,
                model_kind=model_kind,
            )
            print(f"'{name}' ready on ({model_kind}).")
        else:
            print(f"'{name}' already loaded, skipping.")

        return self._models[name], self._tokenizers[name]

    def _resolve_model_kind(
        self,
        model_id: str,
        name: str,
        kwargs: dict[str, Any],
    ) -> str:
        """
        Resolve whether a model should be loaded as text or vision.

        Args:
            model_id (str): The model identifier.
            name (str): The registered model name.
            kwargs (dict[str, Any]): Loading options.

        Returns:
            str: The resolved model kind.
        """
        if kwargs.pop("is_vision_model", False):
            return "vision"

        lowered_model_id = model_id.lower()
        if "-vl" in lowered_model_id or "vision" in lowered_model_id:
            return "vision"

        return "text"

    def _register_shared_alias(
        self,
        model_id: str,
        source_name: str,
        model_kind: str,
    ) -> None:
        """
        Register the counterpart model name as an alias to avoid double loads.

        Args:
            model_id (str): The model identifier.
            source_name (str): The already loaded model name.
            model_kind (str): The loaded model kind.
        """
        alias_name = SHARED_MODEL_ALIASES.get(source_name)
        if not alias_name or alias_name in self._models:
            return

        self._tokenizers[alias_name] = self._tokenizers[source_name]
        self._models[alias_name] = self._models[source_name]
        self._model_ids[alias_name] = model_id
        self._model_kinds[alias_name] = model_kind
        print(f"'{alias_name}' now aliases loaded model '{source_name}'.")

    def _load_language_model(self, model_id: str, **kwargs) -> tuple[Any, Any]:
        """
        Load a text model using Unsloth.

        Args:
            model_id (str): The model identifier.
            **kwargs: Additional loading options.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer.
        """
        from unsloth import FastLanguageModel

        max_seq_length = kwargs.get("max_seq_length", 4096)
        dtype = kwargs.get("dtype", None)
        load_in_4bit = kwargs.get("load_in_4bit", True)

        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_id,
            max_seq_length=max_seq_length,
            dtype=dtype,
            load_in_4bit=load_in_4bit,
        )

        FastLanguageModel.for_inference(model)
        model.eval()
        return model, tokenizer

    def _load_vision_model(self, model_id: str, **kwargs) -> tuple[Any, Any]:
        """
        Load a vision-language model using Transformers.

        Args:
            model_id (str): The model identifier.
            **kwargs: Additional loading options.

        Returns:
            tuple[Any, Any]: The loaded model and processor.
        """
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor

        load_kwargs: dict[str, Any] = {
            "device_map": kwargs.get("device_map", "auto"),
            "torch_dtype": kwargs.get("torch_dtype", "auto"),
            "trust_remote_code": kwargs.get("trust_remote_code", True),
        }

        if kwargs.get("load_in_4bit", True):
            try:
                from transformers import BitsAndBytesConfig

                load_kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_compute_dtype=torch.bfloat16,
                )
            except Exception:
                load_kwargs["load_in_4bit"] = True

        processor = AutoProcessor.from_pretrained(
            model_id,
            trust_remote_code=load_kwargs["trust_remote_code"],
        )
        model = AutoModelForImageTextToText.from_pretrained(
            model_id,
            **load_kwargs,
        )
        model.eval()
        return model, processor

    def _find_loaded_model_name(
        self,
        model_id: str,
    ) -> str | None:
        """
        Find an already loaded model by identifier.

        Args:
            model_id (str): The model identifier to search for.

        Returns:
            str | None: The existing model name, if present.
        """
        for loaded_name, loaded_model_id in self._model_ids.items():
            if loaded_model_id == model_id:
                return loaded_name

        return None

    def get(self, name: str) -> tuple[Any, Any]:
        """
        Retrieve a loaded model and its tokenizer by name.

        Args:
            name (str): The name assigned to the loaded model to retrieve.

        Returns:
            tuple[Any, Any]: A tuple containing the loaded model object and the corresponding tokenizer.
        """
        if name not in self._models:
            raise ValueError(f"'{name}' not loaded. Call load() first.")
        return self._models[name], self._tokenizers[name]

    def unload(self, name: str):
        """
        Unload a model and its tokenizer by name.

        Args:
            name (str): The name assigned to the loaded model to unload."""
        if name in self._models:
            del self._models[name]
            del self._tokenizers[name]
            del self._model_ids[name]
            del self._model_kinds[name]
            print(f"'{name}' unloaded.")

    def list_loaded_models(self) -> list[dict[str, str]]:
         """
         List all currently loaded models.

         Returns:
             list[dict[str, str]]: A list of dictionaries containing information about each loaded model (e.g., name, identifier).
         """
         return [
             {
                 "name": name,
                 "model_id": self._model_ids[name],
                 "kind": self._model_kinds[name],
             }
             for name in self._models.keys()
         ]
