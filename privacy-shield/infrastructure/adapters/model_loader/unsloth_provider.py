"""
Defines an adapter to load models using the Unsloth library.
It is responsible for loading models optimized for Unsloth given their identifier, managing the registry of loaded models and tokenizers.
"""

import threading
from typing import List, Tuple, Any

from unsloth import FastLanguageModel

from infrastructure.ports.model_provider import ModelProvider


class UnslothProvider(ModelProvider):
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
        return cls._instance

    def load(self, model_id: str, name: str, **kwargs) -> Tuple[Any, Any]:
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
            Tuple[Any, Any]: A tuple containing the loaded model object and the corresponding tokenizer.
        """
        if name not in self._models and model_id.startswith("unsloth/"):
            print(f"Downloading/loading '{model_id}' ...")

            max_seq_length = kwargs.get("max_seq_length", 4096)
            dtype = kwargs.get("dtype", None)
            load_in_4bit = kwargs.get("load_in_4bit", True)
            token = kwargs.get("token", None)

            model, tokenizer = FastLanguageModel.from_pretrained(model_name=model_id, max_seq_length=max_seq_length, 
                                                                 dtype=dtype, load_in_4bit=load_in_4bit)
            
            FastLanguageModel.for_inference(model)
            model.eval()

            self._tokenizers[name] = tokenizer
            self._models[name] = model
            print(f"'{name}' ready on (Unsloth).")
        else:
            print(f"'{name}' already loaded, skipping.")

        return self._models[name], self._tokenizers[name]

    def get(self, name: str) -> Tuple[Any, Any]:
        """
        Retrieve a loaded model and its tokenizer by name.

        Args:
            name (str): The name assigned to the loaded model to retrieve.

        Returns:
            Tuple[Any, Any]: A tuple containing the loaded model object and the corresponding tokenizer.
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
            print(f"'{name}' unloaded.")

    def list_models(self) -> List[str]:
        """
        List the names of all currently loaded models.

        Returns:
            List[str]: A list of names of the currently loaded models.
        """
        return list(self._models.keys())