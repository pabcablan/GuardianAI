"""Configuration values for the model-provider module."""
from __future__ import annotations

import os


DEFAULT_PRIVACY_MODEL_ID = os.getenv(
    "DEFAULT_PRIVACY_MODEL_ID",
    "unsloth/Qwen3.5-2B",
)
DEFAULT_PRIVACY_MODEL_NAME = os.getenv(
    "DEFAULT_PRIVACY_MODEL_NAME",
    "privacy_anonymizer",
)
DEFAULT_DOCUMENT_MODEL_ID = os.getenv(
    "DEFAULT_DOCUMENT_MODEL_ID",
    DEFAULT_PRIVACY_MODEL_ID,
)
DEFAULT_DOCUMENT_MODEL_NAME = os.getenv(
    "DEFAULT_DOCUMENT_MODEL_NAME",
    "document_extractor",
)
