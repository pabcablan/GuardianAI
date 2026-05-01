""""
Defines the contract to load a model.
It is responsible for loading a model given its identifier and optional parameters.
"""

from abc import ABC, abstractmethod
from typing import Any

class ModelRepository(ABC):
    @abstractmethod
    def load(self, model_id: str, name:str, **kwargs) -> tuple[Any, Any]:
        """
        Load a model given its identifier and optional parameters.

        Args:
            model_id (str): The identifier of the model to load (e.g., HuggingFace repo name).
            name (str): The name to assign to the loaded model.
            **kwargs: Additional parameters for loading the model (e.g., device, quantization config).
        
        Returns:
            tuple[Any, Any]: A tuple containing (model, tokenizer).
        """
        pass

    @abstractmethod
    def get(self, name: str) -> tuple[Any, Any]:
        """
        Get a loaded model and its tokenizer by name.

        Args:
            name (str): The name of the loaded model to retrieve.
        
        Returns:
            tuple[Any, Any]: A tuple containing (model, tokenizer).
        """
        pass

    @abstractmethod
    def unload(self, name: str):
        """
        Unload a model and its tokenizer by name.

        Args:
            name (str): The name of the loaded model to unload.
        """
        pass

    @abstractmethod
    def list_loaded_models(self) -> list[dict[str, str]]:
        """
        List all currently loaded models.

        Returns:
            list[dict[str, str]]: A list of dictionaries containing information about each loaded model (e.g., name, identifier).
        """
        pass