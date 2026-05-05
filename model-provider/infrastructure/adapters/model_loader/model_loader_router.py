"""Route model loading requests to the proper concrete loader."""
from __future__ import annotations

import threading
from typing import Any

from infrastructure.ports.model_repository import ModelRepository


SHARED_MODEL_ALIASES = {
    "privacy_anonymizer": "document_extractor",
    "document_extractor": "privacy_anonymizer",
}


class ModelLoaderRouter(ModelRepository):
    """Choose between Unsloth and Transformers model loaders."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure only one router instance exists."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._loader_by_name = {}
                    cls._instance._model_ids = {}
                    cls._instance._aliases = {}
        return cls._instance

    async def load(self, model_id: str, name: str, **kwargs) -> tuple[Any, Any]:
        """Load a model through the appropriate concrete loader.

        Args:
            model_id (str): The model identifier.
            name (str): The model registry name.
            **kwargs: Additional loading options.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer or processor.
        """
        existing_name = self._find_loaded_model_name(model_id)
        if existing_name is not None and name != existing_name:
            self._aliases[name] = existing_name
            self._model_ids[name] = model_id
            self._loader_by_name[name] = self._loader_by_name[existing_name]
            print(f"'{name}' now reuses loaded model '{existing_name}'.")
            return await self.get(name)

        loader = self._select_loader(model_id, kwargs)
        model, tokenizer = await loader.load(model_id, name, **kwargs)
        self._loader_by_name[name] = loader
        self._model_ids[name] = model_id
        self._register_shared_alias(
            model_id=model_id,
            source_name=name,
            loader=loader,
        )
        return model, tokenizer

    def _select_loader(
        self,
        model_id: str,
        kwargs: dict[str, Any],
    ) -> ModelRepository:
        """Select the loader that should handle the model.

        Args:
            model_id (str): The model identifier.
            kwargs (dict[str, Any]): Loading options.

        Returns:
            ModelRepository: The concrete loader.
        """
        if self._is_transformers_model(model_id, kwargs):
            from infrastructure.adapters.model_loader.transformers_loader import (
                TransformersLoader,
            )

            return TransformersLoader()

        from infrastructure.adapters.model_loader.unsloth_repository import (
            UnslothLoader,
        )

        return UnslothLoader()

    def _is_transformers_model(
        self,
        model_id: str,
        kwargs: dict[str, Any],
    ) -> bool:
        """Return whether a model should be loaded through Transformers.

        Args:
            model_id (str): The model identifier.
            kwargs (dict[str, Any]): Loading options.

        Returns:
            bool: True when Transformers should load the model.
        """
        lowered_model_id = model_id.lower()
        return (
            not model_id.startswith("unsloth/")
            or kwargs.get("is_vision_model", False)
            or "-vl" in lowered_model_id
            or "vision" in lowered_model_id
        )

    def _register_shared_alias(
        self,
        model_id: str,
        source_name: str,
        loader: ModelRepository,
    ) -> None:
        """Register the counterpart model name as an alias.

        Args:
            model_id (str): The loaded model identifier.
            source_name (str): The loaded model registry name.
            loader (ModelRepository): The loader that owns the source model.
        """
        alias_name = SHARED_MODEL_ALIASES.get(source_name)
        if not alias_name or alias_name in self._model_ids:
            return

        self._aliases[alias_name] = source_name
        self._model_ids[alias_name] = model_id
        self._loader_by_name[alias_name] = loader
        print(f"'{alias_name}' now aliases loaded model '{source_name}'.")

    def _find_loaded_model_name(self, model_id: str) -> str | None:
        """Find an already loaded model by identifier.

        Args:
            model_id (str): The model identifier to search for.

        Returns:
            str | None: The existing model name, if present.
        """
        for loaded_name, loaded_model_id in self._model_ids.items():
            if loaded_model_id == model_id and loaded_name not in self._aliases:
                return loaded_name

        return None

    async def get(self, name: str) -> tuple[Any, Any]:
        """Retrieve a loaded model and tokenizer or processor by name.

        Args:
            name (str): The model registry name.

        Returns:
            tuple[Any, Any]: The loaded model and tokenizer or processor.
        """
        source_name = self._aliases.get(name, name)
        loader = self._loader_by_name.get(name)
        if loader is None:
            raise ValueError(f"'{name}' not loaded. Call load() first.")

        return await loader.get(source_name)

    async def unload(self, name: str) -> None:
        """Unload a model or remove one alias by name.

        Args:
            name (str): The model registry name.
        """
        if name in self._aliases:
            del self._aliases[name]
            del self._loader_by_name[name]
            del self._model_ids[name]
            return

        loader = self._loader_by_name.get(name)
        if loader is None:
            return

        aliases_to_remove = [
            alias for alias, source in self._aliases.items() if source == name
        ]
        for alias in aliases_to_remove:
            del self._aliases[alias]
            del self._loader_by_name[alias]
            del self._model_ids[alias]

        await loader.unload(name)
        del self._loader_by_name[name]
        del self._model_ids[name]

    async def list_loaded_models(self) -> list[dict[str, str]]:
        """List loaded models and registered aliases.

        Returns:
            list[dict[str, str]]: The loaded model metadata.
        """
        loaded_models: list[dict[str, str]] = []
        seen_loader_ids: set[int] = set()
        for loader in self._loader_by_name.values():
            loader_id = id(loader)
            if loader_id in seen_loader_ids:
                continue
            seen_loader_ids.add(loader_id)
            loaded_models.extend(await loader.list_loaded_models())

        for alias_name, source_name in self._aliases.items():
            loaded_models.append(
                {
                    "name": alias_name,
                    "model_id": self._model_ids[alias_name],
                    "kind": "alias",
                    "source": source_name,
                }
            )

        return loaded_models
