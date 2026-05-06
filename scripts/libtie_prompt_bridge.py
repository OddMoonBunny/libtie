from __future__ import annotations

import json
import os
from pathlib import Path

import gradio as gr
from fastapi import Body

from modules import script_callbacks, scripts


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
}


def receive_prompt(payload: dict = Body(...)):
    positive = str(payload.get("positive") or payload.get("Positive") or "")
    negative = str(payload.get("negative") or payload.get("Negative") or "")
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
        }
    )
    return {"ok": True, "id": LATEST_PUSHED_PROMPT["id"]}


def latest_prompt():
    return LATEST_PUSHED_PROMPT


def register_routes(_demo, app):
    app.post("/libtie/prompt")(receive_prompt)
    app.get("/libtie/prompt")(latest_prompt)


script_callbacks.on_app_started(register_routes)


def resolve_prompts_path(value: str | None) -> Path:
    raw = (value or "").strip().strip('"')
    path = Path(raw) if raw else DEFAULT_PROMPTS_PATH

    if path.is_dir():
        direct = path / "prompts.json"
        debug = path / "bin" / "Debug" / "prompts.json"
        if direct.exists():
            return direct
        return debug

    return path


def load_library(path_value: str | None) -> tuple[list[dict], str | None]:
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

    return normalized, f"Loaded {sum(len(c['prompts']) for c in normalized)} prompts from {path}"


def category_names(categories: list[dict]) -> list[str]:
    return [category["name"] for category in categories]


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


def find_category(categories: list[dict], category_name: str | None) -> dict | None:
    for category in categories:
        if category["name"] == category_name:
            return category
    return categories[0] if categories else None


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


def refresh_library(path_value: str | None):
    categories, message = load_library(path_value)
    cats = category_names(categories)
    selected_category = cats[0] if cats else None
    prompts = prompt_names(categories, selected_category)
    selected_prompt = prompts[0] if prompts else None
    positive, negative = prompt_values(find_prompt(categories, selected_category, selected_prompt))

    return (
        gr.update(choices=cats, value=selected_category),
        gr.update(choices=prompts, value=selected_prompt),
        positive,
        negative,
        message,
    )


def select_category(path_value: str | None, category_name: str | None):
    categories, message = load_library(path_value)
    prompts = prompt_names(categories, category_name)
    selected_prompt = prompts[0] if prompts else None
    positive, negative = prompt_values(find_prompt(categories, category_name, selected_prompt))

    return gr.update(choices=prompts, value=selected_prompt), positive, negative, message


def select_prompt(path_value: str | None, category_name: str | None, prompt_name: str | None):
    categories, message = load_library(path_value)
    positive, negative = prompt_values(find_prompt(categories, category_name, prompt_name))
    return positive, negative, message


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
        return scripts.AlwaysVisible

    def ui(self, is_img2img):
        target_tab = "img2img" if is_img2img else "txt2img"

        with gr.Accordion("libtie Prompt Library Bridge", open=False):
            library_path = gr.Textbox(
                label="Prompt Library path",
                value=str(DEFAULT_PROMPTS_PATH),
                placeholder=r"D:\Repo\lib\bin\Debug\prompts.json",
            )
            with gr.Row():
                reload_button = gr.Button("Reload")
                insert_mode = gr.Radio(["Append", "Replace"], value="Append", label="Insert mode")
                apply_at_generation = gr.Checkbox(label="Also apply at generation", value=False)

            category = gr.Dropdown(label="Category", choices=[], value=None)
            prompt = gr.Dropdown(label="Prompt", choices=[], value=None)
            positive = gr.Textbox(label="Positive", lines=3)
            negative = gr.Textbox(label="Negative", lines=3)
            status = gr.Markdown("Load a Prompt Library `prompts.json` file.")

            send_button = gr.Button("Add selected prompt to WebUI prompt boxes")
            target = gr.Textbox(value=target_tab, visible=False)

        reload_button.click(
            fn=refresh_library,
            inputs=[library_path],
            outputs=[category, prompt, positive, negative, status],
        )
        category.change(
            fn=select_category,
            inputs=[library_path, category],
            outputs=[prompt, positive, negative, status],
        )
        prompt.change(
            fn=select_prompt,
            inputs=[library_path, category, prompt],
            outputs=[positive, negative, status],
        )
        send_button.click(
            fn=None,
            inputs=[positive, negative, insert_mode, target],
            outputs=[],
            _js="libtieAddPromptToWebui",
        )

        return [apply_at_generation, positive, negative, insert_mode]

    def process(self, p, apply_at_generation, positive, negative, insert_mode):
        if not apply_at_generation:
            return

        p.prompt = join_prompt(p.prompt, positive, insert_mode)
        p.negative_prompt = join_prompt(p.negative_prompt, negative, insert_mode)
