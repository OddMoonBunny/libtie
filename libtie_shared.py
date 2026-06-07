from __future__ import annotations

import json
import os
import base64
import re
import uuid
from pathlib import Path


PROMPT_LIBRARY_ROOT = Path(os.environ.get("LIBTIE_PROMPT_LIBRARY_DIR", r"D:\Repo\lib"))
DEFAULT_PROMPTS_PATH = Path(
    os.environ.get(
        "LIBTIE_PROMPTS_JSON",
        str(PROMPT_LIBRARY_ROOT / "bin" / "Debug" / "prompts.json"),
    )
)
PROMPT_LIBRARY_BUILD_DIR = Path(
    os.environ.get(
        "LIBTIE_PROMPT_LIBRARY_BUILD_DIR",
        str(PROMPT_LIBRARY_ROOT / "bin" / "Debug"),
    )
)


def resolve_prompts_path(value: str | None = None) -> Path:
    raw = (value or "").strip().strip('"')
    path = Path(raw) if raw else DEFAULT_PROMPTS_PATH

    if path.is_dir():
        direct = path / "prompts.json"
        debug = path / "bin" / "Debug" / "prompts.json"
        if direct.exists():
            return direct
        return debug

    return path


def load_library(path_value: str | None = None) -> tuple[list[dict], str | None]:
    path = resolve_prompts_path(path_value)
    if not path.exists():
        return [], f"Prompt file not found: {path}"

    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
    except Exception as exc:
        return [], f"Could not read {path}: {exc}"

    if isinstance(payload, list):
        categories = payload
    elif isinstance(payload, dict):
        categories = payload.get("Categories") or payload.get("categories") or []
    else:
        return [], f"Unsupported prompt JSON format in {path}"

    normalized = []
    for category in categories:
        if not isinstance(category, dict):
            continue
        name = category.get("Category") or category.get("category") or category.get("Name")
        prompts = category.get("Prompts") or category.get("prompts") or []
        if name:
            normalized.append({"name": str(name), "prompts": prompts if isinstance(prompts, list) else []})

    total = sum(len(category["prompts"]) for category in normalized)
    return normalized, f"Loaded {total} prompts from {path}"


def category_names(categories: list[dict]) -> list[str]:
    return [category["name"] for category in categories]


def find_category(categories: list[dict], category_name: str | None) -> dict | None:
    for category in categories:
        if category["name"] == category_name:
            return category
    return categories[0] if categories else None


def prompt_names(categories: list[dict], category_name: str | None) -> list[str]:
    category = find_category(categories, category_name)
    if not category:
        return []

    names = []
    for prompt in category["prompts"]:
        if isinstance(prompt, dict):
            name = prompt.get("Name") or prompt.get("name")
            if name:
                names.append(str(name))
    return names


def find_prompt(categories: list[dict], category_name: str | None, prompt_name: str | None) -> dict | None:
    category = find_category(categories, category_name)
    if not category:
        return None

    prompts = [prompt for prompt in category["prompts"] if isinstance(prompt, dict)]
    for prompt in prompts:
        if (prompt.get("Name") or prompt.get("name")) == prompt_name:
            return prompt
    return prompts[0] if prompts else None


def prompt_values(prompt: dict | None) -> tuple[str, str]:
    if not prompt:
        return "", ""
    positive = prompt.get("Positive") or prompt.get("positive") or ""
    negative = prompt.get("Negative") or prompt.get("negative") or ""
    return str(positive), str(negative)


def _coerce_int(value, default: int) -> int:
    try:
        if value is None:
            return default
        return int(str(value).strip())
    except Exception:
        return default


def prompt_dimensions(prompt: dict | None, default_width: int = 512, default_height: int = 512) -> tuple[int, int]:
    if not prompt:
        return default_width, default_height

    width = (
        prompt.get("Width")
        or prompt.get("width")
        or prompt.get("W")
        or prompt.get("w")
    )
    height = (
        prompt.get("Height")
        or prompt.get("height")
        or prompt.get("H")
        or prompt.get("h")
    )
    return _coerce_int(width, default_width), _coerce_int(height, default_height)


def prompt_batch(prompt: dict | None, default_batch_count: int = 1, default_batch_size: int = 1) -> tuple[int, int]:
    if not prompt:
        return default_batch_count, default_batch_size

    batch_count = (
        prompt.get("BatchCount")
        or prompt.get("batch_count")
        or prompt.get("BC")
        or prompt.get("bc")
    )
    batch_size = (
        prompt.get("BatchSize")
        or prompt.get("batch_size")
        or prompt.get("BS")
        or prompt.get("bs")
    )
    return _coerce_int(batch_count, default_batch_count), _coerce_int(batch_size, default_batch_size)


def join_prompt(existing: str, incoming: str, mode: str) -> str:
    existing = (existing or "").strip()
    incoming = (incoming or "").strip()

    if mode == "Replace":
        return incoming
    if not incoming:
        return existing
    if not existing:
        return incoming
    return f"{existing}, {incoming}"


LATEST_PUSHED_PROMPT = {
    "id": 0,
    "kind": "prompt",
    "positive": "",
    "negative": "",
    "mode": "Replace",
    "target": "txt2img",
    "category": "",
    "prompt_name": "",
    "width": 512,
    "height": 512,
    "batch_count": 1,
    "batch_size": 1,
}


def set_pushed_prompt(payload: dict) -> dict:
    kind = str(payload.get("kind") or "prompt").lower()
    if kind not in {"prompt", "setup"}:
        kind = "prompt"

    target = str(payload.get("target") or LATEST_PUSHED_PROMPT.get("target") or "txt2img")
    width = _coerce_int(payload.get("width") or payload.get("Width") or payload.get("W"), LATEST_PUSHED_PROMPT.get("width", 512))
    height = _coerce_int(payload.get("height") or payload.get("Height") or payload.get("H"), LATEST_PUSHED_PROMPT.get("height", 512))
    batch_count = _coerce_int(payload.get("batch_count") or payload.get("BatchCount"), LATEST_PUSHED_PROMPT.get("batch_count", 1))
    batch_size = _coerce_int(payload.get("batch_size") or payload.get("BatchSize"), LATEST_PUSHED_PROMPT.get("batch_size", 1))

    if kind == "setup":
        # Setup-only push: preserve existing prompt text/mode/category/name
        LATEST_PUSHED_PROMPT.update(
            {
                "id": int(LATEST_PUSHED_PROMPT["id"]) + 1,
                "kind": "setup",
                "target": target,
                "width": width,
                "height": height,
                "batch_count": batch_count,
                "batch_size": batch_size,
            }
        )
        return {"ok": True, "id": LATEST_PUSHED_PROMPT["id"]}

    positive = str(payload.get("positive") or payload.get("Positive") or "")
    negative = str(payload.get("negative") or payload.get("Negative") or "")
    category = str(payload.get("category") or payload.get("Category") or "")
    prompt_name = str(payload.get("promptName") or payload.get("prompt_name") or payload.get("Name") or "")
    mode = str(payload.get("mode") or "Replace")

    if mode not in {"Append", "Replace"}:
        mode = "Replace"

    LATEST_PUSHED_PROMPT.update(
        {
            "id": int(LATEST_PUSHED_PROMPT["id"]) + 1,
            "kind": "prompt",
            "positive": positive,
            "negative": negative,
            "mode": mode,
            "target": target,
            "category": category,
            "prompt_name": prompt_name,
            "width": width,
            "height": height,
            "batch_count": batch_count,
            "batch_size": batch_size,
        }
    )
    return {"ok": True, "id": LATEST_PUSHED_PROMPT["id"]}


def _safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_. -]+", "_", (value or "").strip())
    cleaned = cleaned.strip(" .")
    return cleaned or "chars"


def _load_raw_prompt_data(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        categories = payload.get("Categories") or payload.get("categories")
        return categories if isinstance(categories, list) else []
    return []


def _decode_data_url(data_url: str) -> tuple[bytes, str]:
    match = re.match(r"^data:image/([a-zA-Z0-9.+-]+);base64,(.+)$", data_url or "", re.DOTALL)
    if not match:
        raise ValueError("Expected a base64 image data URL.")

    ext = match.group(1).lower()
    if ext == "jpeg":
        ext = "jpg"
    return base64.b64decode(match.group(2)), ext


def save_gallery_image(payload: dict) -> dict:
    data_url = payload.get("imageData") or payload.get("image_data")
    if not data_url:
        return {"ok": False, "error": "No image data provided"}

    try:
        image_bytes, ext = _decode_data_url(data_url)
    except Exception as exc:
        return {"ok": False, "error": f"Could not decode image data: {exc}"}

    filename = f'{_safe_name(payload.get("name") or "image")}_{uuid.uuid4().hex}.{ext}'
    gallery_dir = PROMPT_LIBRARY_BUILD_DIR / "gallery"
    gallery_dir.mkdir(parents=True, exist_ok=True)
    output_path = gallery_dir / filename

    try:
        output_path.write_bytes(image_bytes)
    except Exception as exc:
        return {"ok": False, "error": f"Could not write image to {output_path}: {exc}"}

    return {"ok": True, "filename": filename}
