from pydantic import BaseModel
from typing import Optional, Dict, Any


class TransformersConfig(BaseModel):
    gpu_index: Optional[int] = None
    quantization_config: Optional[Dict[str, Any]] = None