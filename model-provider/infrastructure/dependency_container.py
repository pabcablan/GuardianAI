"""Dependency composition for the model-provider module."""
from __future__ import annotations

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


def build_controller() -> Controller:
    """Build the model controller dependency graph.

    Returns:
        Controller: The configured model controller.
    """
    return Controller(
        model_loader=UnslothLoader(),
        inference_engine=ModelInferenceEngine(),
    )


async def load_startup_models(controller: Controller) -> None:
    """Load the models required at service startup.

    Args:
        controller (Controller): The model controller.
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
        controller (Controller): The model controller.
        model_id (str): The model identifier.
        model_name (str): The model registry name.
        label (str): A human-readable model role.

    Raises:
        RuntimeError: If the model cannot be loaded.
    """
    print(
        f"Loading default {label} model '{model_name}' from '{model_id}'...",
        flush=True,
    )
    request = LoadModelRequest(
        model_id=model_id,
        name=model_name,
    )
    result = await controller.load_model(request)
    print(result, flush=True)
    if result.startswith("Error "):
        raise RuntimeError(result)
