"""Request schema for loading models into model-provider."""
from __future__ import annotations

from pydantic import BaseModel, Field

from application.body_params_schemas.transformers_config import (
    TransformersConfig,
)
from application.body_params_schemas.unsloth_config import UnslothConfig


class LoadModelRequest(BaseModel):
    """Represent one model loading request.

    Attributes:
        model_id (str): The source identifier of the model to load.
        name (str): The runtime name assigned to the loaded model.
        transformers (TransformersConfig | None): Optional runtime settings
            for the Transformers loader.
        unsloth (UnslothConfig | None): Optional runtime settings for the
            Unsloth loader.
    """

    model_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    transformers: TransformersConfig | None = None
    unsloth: UnslothConfig | None = None
