# libtie Prompt Library Bridge

`libtie` bridges the Prompt Library app in `D:\Repo\lib` to both AUTOMATIC1111 Stable Diffusion WebUI and ComfyUI.

It reads the Prompt Library `prompts.json` format and exposes a local push endpoint so the Prompt Library app can send its current positive and negative prompts into either host.

## Automatic1111 Install

Clone or copy this repository into your WebUI `extensions` directory:

```powershell
cd path\to\stable-diffusion-webui
git clone <this-repo-url> extensions\libtie
```

Restart WebUI after installation.

## ComfyUI Install

Clone or copy this repository into your ComfyUI `custom_nodes` directory:

```powershell
cd path\to\ComfyUI
git clone <this-repo-url> custom_nodes\libtie
```

Restart ComfyUI after installation.

The custom node package provides:

- **libtie Prompt From Library** - loads a prompt from `prompts.json` using dropdowns.
- **libtie Prompt By Name** - loads a prompt by typed category/name.
- **libtie Pushed Prompt** - outputs the latest prompt pushed from the Prompt Library app.

## Usage

### Push From Prompt Library

Install the bridge in your target app, restart it, then use the matching button in the Prompt Library app.

Automatic1111:

```text
http://127.0.0.1:7860/libtie/prompt
```

ComfyUI:

```text
http://127.0.0.1:8188/libtie/prompt
```

For A1111, the extension browser script applies the newest pushed prompt to txt2img.

For ComfyUI, use the **libtie Pushed Prompt** node and connect its `positive` and `negative` outputs into your CLIP Text Encode nodes.

### Pull From Prompt Library In A1111

Open txt2img or img2img and expand **libtie Prompt Library Bridge**.

- Set **Prompt Library path** to either a `prompts.json` file or a Prompt Library folder.
- Click **Reload**.
- Pick a category and prompt.
- Choose **Append** or **Replace**.
- Click **Add selected prompt to WebUI prompt boxes**.

Default path:

```text
D:\Repo\lib\bin\Debug\prompts.json
```

If you enable **Also apply at generation**, the selected prompt is applied during generation too. Keep that off when you are already clicking the add button, unless you intentionally want the prompt applied at generation time.

## Development

Automatic1111 loads extension scripts from the `scripts` folder:

- `scripts/libtie_prompt_bridge.py`

The WebUI textarea updater lives in:

- `javascript/libtie_prompt_bridge.js`

ComfyUI loads custom node files from the repo root:

- `__init__.py`
- `comfy_libtie.py`
- `libtie_shared.py`
