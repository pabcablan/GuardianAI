from typing import Optional

from pydantic import BaseModel

from application.body_params_schemas.transformers_config import TransformersConfig
from application.body_params_schemas.unsloth_config import UnslothConfig


class LoadModelRequest(BaseModel):
    model_id: str
    name: str

    transformers: Optional[TransformersConfig] = None
    unsloth: Optional[UnslothConfig] = None