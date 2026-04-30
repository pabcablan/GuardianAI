from typing import Optional

from pydantic import BaseModel


class UnslothConfig (BaseModel):
    max_seq_length: Optional[int] = 4096
    dtype: Optional[str] = None
    load_in_4bit: Optional[bool] = True
