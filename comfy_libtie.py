from __future__ import annotations

from aiohttp import web

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

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "status")
    FUNCTION = "load_prompt"
    CATEGORY = "libtie"

    def load_prompt(self, library_path, category, prompt_name):
        categories, message = libtie_shared.load_library(library_path)
        prompt = libtie_shared.find_prompt(categories, category, prompt_name)
        positive, negative = libtie_shared.prompt_values(prompt)
        return positive, negative, message or ""


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

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "status")
    FUNCTION = "load_prompt"
    CATEGORY = "libtie"

    def load_prompt(self, library_path, category, prompt_name):
        categories, message = libtie_shared.load_library(library_path)
        prompt = libtie_shared.find_prompt(categories, category, prompt_name)
        positive, negative = libtie_shared.prompt_values(prompt)
        return positive, negative, message or ""


class LibtiePushedPrompt:
    @classmethod
    def INPUT_TYPES(cls):
        return {"required": {"fallback": ("STRING", {"default": ""})}}

    RETURN_TYPES = ("STRING", "STRING", "INT")
    RETURN_NAMES = ("positive", "negative", "push_id")
    FUNCTION = "current_prompt"
    CATEGORY = "libtie"

    def current_prompt(self, fallback):
        payload = libtie_shared.LATEST_PUSHED_PROMPT
        positive = payload.get("positive") or fallback
        negative = payload.get("negative") or ""
        return positive, negative, int(payload.get("id") or 0)


def register_routes():
    if PromptServer is None:
        return

    routes = PromptServer.instance.routes

    @routes.post("/libtie/prompt")
    async def receive_prompt(request):
        payload = await request.json()
        return web.json_response(libtie_shared.set_pushed_prompt(payload))

    @routes.get("/libtie/prompt")
    async def latest_prompt(_request):
        return web.json_response(libtie_shared.LATEST_PUSHED_PROMPT)


register_routes()


NODE_CLASS_MAPPINGS = {
    "LibtiePromptFromLibrary": LibtiePromptFromLibrary,
    "LibtiePromptByName": LibtiePromptByName,
    "LibtiePushedPrompt": LibtiePushedPrompt,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "LibtiePromptFromLibrary": "libtie Prompt From Library",
    "LibtiePromptByName": "libtie Prompt By Name",
    "LibtiePushedPrompt": "libtie Pushed Prompt",
}
