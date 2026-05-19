"""Dependency composition for the model-provider module."""
from __future__ import annotations

import logging

from application.body_params_schemas.load_model_request import LoadModelRequest
from application.usecases.model_controller.controller import Controller
from config import (
    DEFAULT_DOCUMENT_MODEL_ID,
    DEFAULT_DOCUMENT_MODEL_NAME,
    DEFAULT_PRIVACY_MODEL_ID,
    DEFAULT_PRIVACY_MODEL_NAME,
)
from infrastructure.adapters.inference.model_inference_engine import (
    ModelInferenceEngine,
)
from infrastructure.adapters.model_loader.unsloth_repository import (
    UnslothLoader,
)


LOGGER = logging.getLogger(__name__)


def build_controller() -> Controller:
    """Build the model-provider dependency graph.

    Returns:
        Controller: The configured application controller.
    """
    return Controller(
        model_loader=UnslothLoader(),
        inference_engine=ModelInferenceEngine(),
    )


async def load_startup_models(controller: Controller) -> None:
    """Load the models required at service startup.

    Args:
        controller (Controller): The application controller.
    """
    await _load_startup_model(
        controller=controller,
        model_id=DEFAULT_PRIVACY_MODEL_ID,
        model_name=DEFAULT_PRIVACY_MODEL_NAME,
        label="privacy",
    )

    if DEFAULT_DOCUMENT_MODEL_NAME != DEFAULT_PRIVACY_MODEL_NAME:
        await _load_startup_model(
            controller=controller,
            model_id=DEFAULT_DOCUMENT_MODEL_ID,
            model_name=DEFAULT_DOCUMENT_MODEL_NAME,
            label="document",
        )


async def _load_startup_model(
    controller: Controller,
    model_id: str,
    model_name: str,
    label: str,
) -> None:
    """Load one startup model through the controller.

    Args:
        controller (Controller): The application controller.
        model_id (str): The source model identifier.
        model_name (str): The runtime model name.
        label (str): A human-readable model role.

    Raises:
        RuntimeError: If the model cannot be loaded.
    """
    LOGGER.info(
        "Loading default %s model '%s' from '%s'.",
        label,
        model_name,
        model_id,
    )
    request = LoadModelRequest(
        model_id=model_id,
        name=model_name,
    )
    result = await controller.load_model(request)
    LOGGER.info(result)
    if result.startswith("Error "):
        raise RuntimeError(result)
