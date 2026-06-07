from __future__ import annotations

import base64
from io import BytesIO

try:
    from aiohttp import web
except Exception:
    web = None

try:
    from server import PromptServer
except Exception:
    PromptServer = None

from . import libtie_shared


def _prompt_choices():
    categories, _message = libtie_shared.load_library()
    cats = libtie_shared.category_names(categories) or ["Default"]
    prompts = libtie_shared.prompt_names(categories, cats[0]) or ["First prompt in category"]
    return cats, prompts


class LibtiePromptFromLibrary:
    @classmethod
    def INPUT_TYPES(cls):
        cats, prompts = _prompt_choices()
        return {
            "required": {
                "library_path": ("STRING", {"default": str(libtie_shared.DEFAULT_PROMPTS_PATH)}),
                "category": (cats,),
                "prompt_name": (prompts,),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("positive", "negative", "status", "width", "height")
    FUNCTION = "load_prompt"
    CATEGORY = "libtie"

    def load_prompt(self, library_path, category, prompt_name):
        categories, message = libtie_shared.load_library(library_path)
        prompt = libtie_shared.find_prompt(categories, category, prompt_name)
        positive, negative = libtie_shared.prompt_values(prompt)
        width, height = libtie_shared.prompt_dimensions(prompt)
        return positive, negative, message or "", width, height


class LibtiePromptByName:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "library_path": ("STRING", {"default": str(libtie_shared.DEFAULT_PROMPTS_PATH)}),
                "category": ("STRING", {"default": ""}),
                "prompt_name": ("STRING", {"default": ""}),
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "INT")
    RETURN_NAMES = ("positive", "negative", "status", "width", "height")
    FUNCTION = "load_prompt"
    CATEGORY = "libtie"

    def load_prompt(self, library_path, category, prompt_name):
        categories, message = libtie_shared.load_library(library_path)
        prompt = libtie_shared.find_prompt(categories, category, prompt_name)
        positive, negative = libtie_shared.prompt_values(prompt)
        width, height = libtie_shared.prompt_dimensions(prompt)
        return positive, negative, message or "", width, height


class LibtiePushedPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"fallback": ("STRING", {"default": ""})}}

    RETURN_TYPES = ("STRING", "STRING", "STRING", "INT", "INT", "INT")
    RETURN_NAMES = ("positive", "negative", "category", "push_id", "width", "height")
    FUNCTION = "current_prompt"
    CATEGORY = "libtie"

    def current_prompt(self, fallback):
        payload = libtie_shared.LATEST_PUSHED_PROMPT
        positive = payload.get("positive") or fallback
        negative = payload.get("negative") or ""
        category = payload.get("category") or ""
        width = int(payload.get("width") or 512)
        height = int(payload.get("height") or 512)
        return positive, negative, category, int(payload.get("id") or 0), width, height


class LibtieSaveImageToGallery:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "image": ("IMAGE",),
                "category": ("STRING", {"default": "chars"}),
                "build_dir": ("STRING", {"default": str(libtie_shared.PROMPT_LIBRARY_BUILD_DIR)}),
            }
        }

    RETURN_TYPES = ("IMAGE", "STRING")
    RETURN_NAMES = ("image", "status")
    FUNCTION = "save_image"
    CATEGORY = "libtie"

    def save_image(self, image, category, build_dir):
        import numpy as np
        from PIL import Image

        first = image[0].detach().cpu().numpy()
        pixels = np.clip(first * 255.0, 0, 255).astype(np.uint8)
        pil_image = Image.fromarray(pixels)

        buffer = BytesIO()
        pil_image.save(buffer, format="PNG")
        image_data = "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode("ascii")

        result = libtie_shared.save_gallery_image(
            {
                "category": category,
                "build_dir": build_dir,
                "image": image_data,
            }
        )
        return image, f"Saved {result['name']} to {result['category']}"


def register_routes():
    if PromptServer is None or web is None:
        return

    routes = PromptServer.instance.routes

    @routes.post("/libtie/prompt")
    async def receive_prompt(request):
        payload = await request.json()
        return web.json_response(libtie_shared.set_pushed_prompt(payload))

    @routes.get("/libtie/prompt")
    async def latest_prompt(_request):
        return web.json_response(libtie_shared.LATEST_PUSHED_PROMPT)

    @routes.post("/libtie/gallery")
    async def save_gallery_image(request):
        payload = await request.json()
        return web.json_response(libtie_shared.save_gallery_image(payload))


register_routes()


NODE_CLASS_MAPPINGS = {
    "LibtiePromptFromLibrary": LibtiePromptFromLibrary,
    "LibtiePromptByName": LibtiePromptByName,
    "LibtiePushedPrompt": LibtiePushedPrompt,
    "LibtieSaveImageToGallery": LibtieSaveImageToGallery,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LibtiePromptFromLibrary": "libtie Prompt From Library",
    "LibtiePromptByName": "libtie Prompt By Name",
    "LibtiePushedPrompt": "libtie Pushed Prompt",
    "LibtieSaveImageToGallery": "libtie Save Image To Gallery",
}
