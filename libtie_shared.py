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
    "positive": "",
    "negative": "",
    "mode": "Replace",
    "target": "txt2img",
    "category": "",
    "prompt_name": "",
}


def set_pushed_prompt(payload: dict) -> dict:
    positive = str(payload.get("positive") or payload.get("Positive") or "")
    negative = str(payload.get("negative") or payload.get("Negative") or "")
    category = str(payload.get("category") or payload.get("Category") or "")
    prompt_name = str(payload.get("promptName") or payload.get("prompt_name") or payload.get("Name") or "")
    mode = str(payload.get("mode") or "Replace")
    target = str(payload.get("target") or "txt2img")

    if mode not in {"Append", "Replace"}:
        mode = "Replace"

    LATEST_PUSHED_PROMPT.update(
        {
            "id": int(LATEST_PUSHED_PROMPT["id"]) + 1,
            "positive": positive,
            "negative": negative,
            "mode": mode,
            "target": target,
            "category": category,
            "prompt_name": prompt_name,
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
    category = _safe_name(str(payload.get("category") or payload.get("Category") or "chars"))
    image_data = str(payload.get("image") or payload.get("image_data") or payload.get("Image") or "")
    image_bytes, ext = _decode_data_url(image_data)

    build_dir = Path(str(payload.get("build_dir") or PROMPT_LIBRARY_BUILD_DIR))
    prompts_path = build_dir / "prompts.json"
    image_dir = build_dir / "images" / category
    image_dir.mkdir(parents=True, exist_ok=True)

    entry_id = str(uuid.uuid4())
    entry_name = f"{category}_gallery_{entry_id}"
    dest_path = image_dir / f"{entry_name}.{ext}"
    dest_path.write_bytes(image_bytes)

    categories = _load_raw_prompt_data(prompts_path)
    category_entry = None
    for item in categories:
        if isinstance(item, dict) and item.get("Category") == category:
            category_entry = item
            break

    if category_entry is None:
        category_entry = {"Category": category, "Prompts": []}
        categories.append(category_entry)

    prompts = category_entry.setdefault("Prompts", [])
    prompts.append({"Name": entry_name, "Positive": "", "Negative": "", "ImagePath": str(dest_path)})

    prompts_path.parent.mkdir(parents=True, exist_ok=True)
    with prompts_path.open("w", encoding="utf-8") as handle:
        json.dump(categories, handle, indent=2)
        handle.write("\n")

    return {
        "ok": True,
        "category": category,
        "name": entry_name,
        "image_path": str(dest_path),
        "prompts_path": str(prompts_path),
    }
