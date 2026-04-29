from dataclasses import dataclass
from collections.abc import Callable

@dataclass(frozen=True)
class ExtractionProgress:
    stage: str
    current: int
    total: int
    message: str

ExtractionProgressCallback = Callable[[ExtractionProgress], None]

# TODO SHOULD THIS BE ERASED
