from __future__ import annotations

import time
from functools import lru_cache
from io import BytesIO
from pathlib import Path

from domain.document import ExtractionProgress, ExtractionProgressCallback

MODEL_NAME = "unsloth/Qwen3.5-2B"
GPU_INDEX = 0
PROMPT = """Transcribe todo el texto visible de esta pagina exactamente como aparece.
Manten el contenido literal.
No anadas explicaciones.
No inventes texto.
Si algo no se lee bien, mantenlo lo mas fiel posible a lo visible."""
DPI_SCALE = 2.0


def _require_dependency(module_name: str, error: Exception) -> None:
    raise RuntimeError(
        f"Missing optional dependency '{module_name}' for document extraction."
    ) from error


def load_model(model_name: str, gpu_index: int):
    try:
        import torch
        from transformers import AutoModelForImageTextToText, AutoProcessor
    except ModuleNotFoundError as error:
        _require_dependency("transformers/torch", error)

    print(f"Cargando modelo {model_name} en GPU {gpu_index}...")

    model = AutoModelForImageTextToText.from_pretrained(
        model_name,
        torch_dtype=torch.bfloat16,
        device_map={"": gpu_index},
        trust_remote_code=True,
    )
    processor = AutoProcessor.from_pretrained(
        model_name,
        trust_remote_code=True,
    )
    print("Modelo cargado.")
    return model, processor


@lru_cache(maxsize=1)
def load_runtime_vlm():
    return load_model(MODEL_NAME, GPU_INDEX)


def pdf_to_images(pdf_bytes: bytes, scale: float = DPI_SCALE):
    try:
        import fitz
        from PIL import Image
    except ModuleNotFoundError as error:
        _require_dependency("pymupdf/Pillow", error)

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    images = []
    matrix = fitz.Matrix(scale, scale)

    for page in document:
        pixmap = page.get_pixmap(matrix=matrix)
        image = Image.frombytes("RGB", [pixmap.width, pixmap.height], pixmap.samples)
        images.append(image)

    document.close()
    return images


def extract_page(image, model, processor, prompt: str) -> str:
    try:
        import torch
    except ModuleNotFoundError as error:
        _require_dependency("torch", error)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image", "image": image},
                {"type": "text", "text": prompt},
            ],
        }
    ]

    input_text = processor.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    inputs = processor(
        text=[input_text],
        images=[image],
        return_tensors="pt",
    ).to(model.device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=1200,
            do_sample=False,
            use_cache=True,
            eos_token_id=processor.tokenizer.eos_token_id,
            pad_token_id=processor.tokenizer.pad_token_id,
            max_time=60,
        )

    input_token_count = inputs["input_ids"].shape[1]
    new_tokens = output_ids[0][input_token_count:]
    return processor.decode(new_tokens, skip_special_tokens=True)


def extract_pdf_text(
    pdf_bytes: bytes,
    *,
    progress_callback: ExtractionProgressCallback | None = None,
) -> tuple[str, int]:
    if progress_callback is not None:
        progress_callback(
            ExtractionProgress(
                stage="starting",
                current=0,
                total=1,
                message="Cargando modelo VLM para extraer el documento...",
            )
        )

    model, processor = load_runtime_vlm()
    images = pdf_to_images(pdf_bytes, scale=DPI_SCALE)
    total_pages = len(images)
    texts: list[str] = []

    if progress_callback is not None:
        progress_callback(
            ExtractionProgress(
                stage="starting",
                current=0,
                total=max(total_pages, 1),
                message=f"Preparando extraccion de {total_pages} paginas...",
            )
        )

    for index, image in enumerate(images, start=1):
        start = time.time()
        page_text = extract_page(image, model, processor, PROMPT)
        elapsed = time.time() - start
        print(f"Pagina {index}/{total_pages} procesada en {elapsed:.2f}s")
        texts.append(page_text.strip())

        if progress_callback is not None:
            progress_callback(
                ExtractionProgress(
                    stage="extracting",
                    current=index,
                    total=max(total_pages, 1),
                    message=f"Pagina {index} de {total_pages} procesada.",
                )
            )

    return "\n\n".join(texts).strip(), total_pages


def save_uploaded_pdf(content: bytes, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(content)
    return destination


def save_extracted_text(text: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(text, encoding="utf-8")
    return destination
