"""
Defines an adapter to load models using the HuggingFace Transformers library.
It is responsible for loading a model given its identifier and optional parameters, and managing loaded models and tokenizers.
"""

import threading
from typing import Any

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from infrastructure.ports.model_repository import ModelRepository


class TransformersLoader(ModelRepository):
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
        return cls._instance

    async def load(self, model_id: str, name: str, **kwargs) -> tuple[Any, Any]:
        """
        Load a model given its identifier and optional parameters.
        
        Args:
            model_id (str): The identifier of the model to load (e.g., HuggingFace repo name).
            name (str): The name to assign to the loaded model.
            **kwargs: Additional parameters for loading the model:
                - gpu_index (int, optional): The GPU index to load the model on. If not provided, it will be loaded on CPU.
                - quantization_config (BitsAndBytesConfig, optional): The quantization configuration for loading the model. If not provided, the model will be loaded without quantization.
    
        Returns:
            tuple[Any, Any]: A tuple containing the loaded model object and the corresponding tokenizer.
        """
        if name not in self._models:
            print(f"Loading '{model_id}' via Transformers...")
                
            gpu_index = kwargs.get("gpu_index")
            quantization_config = kwargs.get("quantization_config")
            device_map = {"": f"cuda:{gpu_index}"} if gpu_index is not None else "auto"
                
            tokenizer = AutoTokenizer.from_pretrained(model_id)
            model = AutoModelForCausalLM.from_pretrained(model_id, quantization_config=quantization_config,
                                                              device_map=device_map)
            model.eval()

            self._tokenizers[name] = tokenizer
            self._models[name] = model
            self._model_ids[name] = model_id

            print(f"'{name}' ready on {device_map}.")
        else:
            print(f"'{name}' already loaded, skipping.")

        return self._models[name], self._tokenizers[name]

    async def get(self, name: str) -> tuple[Any, Any]:
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

    async def unload(self, name: str):
        """
        Unload a model and its tokenizer by name.

        Args:
            name (str): The name assigned to the loaded model to unload.
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
             list[dict[str, str]]: A list of dictionaries containing information about each loaded model (e.g., name, identifier).
         """
         return [{"name": name, "model_id": self._model_ids[name]} for name in self._models.keys()]