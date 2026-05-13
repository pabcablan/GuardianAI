"""Configuration values for the web-ui module."""
from __future__ import annotations

import os

from dotenv import load_dotenv


load_dotenv()


MODEL_PROVIDER_BASE_URL = os.getenv(
    "MODEL_PROVIDER_BASE_URL",
    "http://127.0.0.1:8010",
)
PRIVACY_MODEL_NAME = os.getenv("PRIVACY_MODEL_NAME", "qwen3.5")
DOCUMENT_MODEL_NAME = os.getenv("DOCUMENT_MODEL_NAME", "qwen3.5")
MODEL_STATUS_TIMEOUT_SECONDS = 2.0
