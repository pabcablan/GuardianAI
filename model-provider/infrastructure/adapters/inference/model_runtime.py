"""Runtime helpers for model inference."""
from __future__ import annotations


def get_model_device(model):
    """Return the first device used by a model.

    Args:
        model: The loaded model.

    Returns:
        The model device.
    """
    if hasattr(model, "device"):
        return model.device

    return next(model.parameters()).device


def supports_vision(model, tokenizer) -> bool:
    """Return whether the loaded model can consume images.

    Args:
        model: The loaded model.
        tokenizer: The tokenizer or processor.

    Returns:
        bool: True when vision inputs are supported.
    """
    if hasattr(tokenizer, "image_processor"):
        return True

    config = getattr(model, "config", None)
    return hasattr(config, "vision_config")


def move_inputs_to_device(inputs, device):
    """Move tensor inputs to a model device.

    Args:
        inputs: The processor/tokenizer output.
        device: The target torch device.

    Returns:
        The moved inputs.
    """
    if hasattr(inputs, "to"):
        return inputs.to(device)

    return {
        key: value.to(device) if hasattr(value, "to") else value
        for key, value in inputs.items()
    }


def get_eos_token_id(tokenizer) -> int | None:
    """Return an EOS token id from a tokenizer or processor.

    Args:
        tokenizer: The tokenizer or processor.

    Returns:
        int | None: The EOS token id if available.
    """
    if hasattr(tokenizer, "eos_token_id"):
        return tokenizer.eos_token_id

    nested_tokenizer = getattr(tokenizer, "tokenizer", None)
    if nested_tokenizer is not None:
        return getattr(nested_tokenizer, "eos_token_id", None)

    return None
