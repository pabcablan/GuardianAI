"""Configuration values for the model-provider module."""
from __future__ import annotations

import os


DEFAULT_PRIVACY_MODEL_ID = os.getenv(
    "DEFAULT_PRIVACY_MODEL_ID",
    "unsloth/Qwen3.5-9B",
)
DEFAULT_PRIVACY_MODEL_NAME = os.getenv(
    "DEFAULT_PRIVACY_MODEL_NAME",
    "qwen3.5",
)
DEFAULT_DOCUMENT_MODEL_ID = os.getenv(
    "DEFAULT_DOCUMENT_MODEL_ID",
    DEFAULT_PRIVACY_MODEL_ID,
)
DEFAULT_DOCUMENT_MODEL_NAME = os.getenv(
    "DEFAULT_DOCUMENT_MODEL_NAME",
    DEFAULT_PRIVACY_MODEL_NAME,
)
