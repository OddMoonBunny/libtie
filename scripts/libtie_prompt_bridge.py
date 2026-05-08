from __future__ import annotations

import json
import os
import sys
from pathlib import Path

from fastapi import Body

from modules import script_callbacks, scripts

EXTENSION_ROOT = Path(__file__).resolve().parents[1]
if str(EXTENSION_ROOT) not in sys.path:
    sys.path.insert(0, str(EXTENSION_ROOT))

import libtie_shared


PROMPT_LIBRARY_ROOT = Path(os.environ.get("LIBTIE_PROMPT_LIBRARY_DIR", r"D:\Repo\lib"))
DEFAULT_PROMPTS_PATH = Path(
    os.environ.get(
        "LIBTIE_PROMPTS_JSON",
        str(PROMPT_LIBRARY_ROOT / "bin" / "Debug" / "prompts.json"),
    )
)
LATEST_PUSHED_PROMPT = {
    "id": 0,
    "positive": "",
    "negative": "",
    "mode": "Replace",
    "target": "txt2img",
    "category": "",
    "prompt_name": "",
}


def receive_prompt(payload: dict = Body(...)):
    positive = str(payload.get("positive") or payload.get("Positive") or "")
    negative = str(payload.get("negative") or payload.get("Negative") or "")
    category = str(payload.get("category") or payload.get("Category") or "")
    prompt_name = str(payload.get("promptName") or payload.get("prompt_name") or payload.get("Name") or "")
    mode = str(payload.get("mode") or "Replace")
    target = str(payload.get("target") or "txt2img")

    if mode not in {"Append", "Replace"}:
        mode = "Replace"
    if target not in {"txt2img", "img2img"}:
        target = "txt2img"

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


def latest_prompt():
    return LATEST_PUSHED_PROMPT


def save_gallery_image(payload: dict = Body(...)):
    return libtie_shared.save_gallery_image(payload)


def register_routes(_demo, app):
    app.post("/libtie/prompt")(receive_prompt)
    app.get("/libtie/prompt")(latest_prompt)
    app.post("/libtie/gallery")(save_gallery_image)


script_callbacks.on_app_started(register_routes)


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


class Script(scripts.Script):
    def title(self):
        return "libtie Prompt Library Bridge"

    def show(self, is_img2img):
        return False

    def ui(self, is_img2img):
        return []

    def process(self, p):
        return
