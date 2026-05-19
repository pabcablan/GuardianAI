"""Runtime configuration schema for Unsloth-backed models."""
from __future__ import annotations

from pydantic import BaseModel


class UnslothConfig(BaseModel):
    """Represent optional settings for loading an Unsloth model.

    Attributes:
        max_seq_length (int | None): Maximum sequence length configured at
            load time.
        dtype (str | None): Optional dtype override for the loaded model.
        load_in_4bit (bool | None): Whether to load the model in 4-bit mode.
    """

    max_seq_length: int | None = 4096
    dtype: str | None = None
    load_in_4bit: bool | None = True
