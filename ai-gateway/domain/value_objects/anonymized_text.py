from dataclasses import dataclass


@dataclass(frozen=True)
class AnonymizedText:
    value: str

    def __post_init__(self):
        if not self.value or not self.value.strip():
            raise ValueError("AnonymizedText cannot be empty")

    def __str__(self) -> str:
        return self.value