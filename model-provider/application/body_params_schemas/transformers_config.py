"""Runtime configuration schema for Transformers-backed models."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class TransformersConfig(BaseModel):
    """Represent optional settings for loading a Transformers model.

    Attributes:
        gpu_index (int | None): Optional GPU index used for the device map.
        quantization_config (dict[str, Any] | None): Optional quantization
            settings forwarded to the loader.
    """

    gpu_index: int | None = None
    quantization_config: dict[str, Any] | None = None
