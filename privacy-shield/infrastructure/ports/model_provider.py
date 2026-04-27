""""
Defines the contract to load a model.
It is responsible for loading a model given its identifier and optional parameters.
"""

from abc import ABC, abstractmethod
from typing import Tuple, Any

class ModelProvider(ABC):
    @abstractmethod
    def load(self, model_id: str, name:str, **kwargs) -> Tuple[Any, Any]:
        """
        Load a model given its identifier and optional parameters.

        Args:
            model_id (str): The identifier of the model to load (e.g., HuggingFace repo name).
            name (str): The name to assign to the loaded model.
            **kwargs: Additional parameters for loading the model (e.g., device, quantization config).
        
        Returns:
            Tuple[Any, Any]: A tuple containing (model, tokenizer).
        """
        pass