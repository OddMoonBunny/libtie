from __future__ import annotations

import sys
from pathlib import Path

from fastapi import Body

from modules import script_callbacks, scripts

EXTENSION_ROOT = Path(__file__).resolve().parents[1]
if str(EXTENSION_ROOT) not in sys.path:
    sys.path.insert(0, str(EXTENSION_ROOT))

import libtie_shared


def receive_prompt(payload: dict = Body(...)):
    return libtie_shared.set_pushed_prompt(payload)


def latest_prompt():
    return libtie_shared.LATEST_PUSHED_PROMPT


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
