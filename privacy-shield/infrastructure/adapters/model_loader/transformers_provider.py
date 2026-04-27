"""
Defines an adapter to load models using the HuggingFace Transformers library.
It is responsible for loading a model given its identifier and optional parameters, and managing loaded models and tokenizers.
"""

import threading
from typing import List, Tuple, Any

from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from infrastructure.ports.model_provider import ModelProvider


class TransformersProvider(ModelProvider):
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
        Load a model given its identifier and optional parameters.
        
        Args:
            model_id (str): The identifier of the model to load (e.g., HuggingFace repo name).
            name (str): The name to assign to the loaded model.
            **kwargs: Additional parameters for loading the model:
                - gpu_index (int, optional): The GPU index to load the model on. If not provided, it will be loaded on CPU.
                - quantization_config (BitsAndBytesConfig, optional): The quantization configuration for loading the model. If not provided, the model will be loaded without quantization.
    
        Returns:
            Tuple[Any, Any]: A tuple containing the loaded model object and the corresponding tokenizer.
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
            print(f"'{name}' ready on {device_map}.")
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
            name (str): The name assigned to the loaded model to unload.
        """
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