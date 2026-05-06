# libtie Automatic1111 Prompt Library Bridge

`libtie` bridges AUTOMATIC1111 Stable Diffusion WebUI to the Prompt Library app in `D:\Repo\lib`.

It can read the Prompt Library `prompts.json` format from inside WebUI, and it also exposes a local endpoint so the Prompt Library app can push its current positive and negative prompts directly into the WebUI prompt boxes.

## Install

Clone or copy this repository into your WebUI `extensions` directory:

```powershell
cd path\to\stable-diffusion-webui
git clone <this-repo-url> extensions\libtie
```

Restart WebUI after installation.

## Usage

### Push From Prompt Library

Install this extension, restart WebUI, then use the **Send A1111** button in the Prompt Library app. It posts the current Positive and Negative text to:

```text
http://127.0.0.1:7860/libtie/prompt
```

The extension browser script polls that endpoint and applies the newest pushed prompt to txt2img.

### Pull From WebUI

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

Automatic1111 loads extension scripts from the `scripts/` folder. The main script is:

- `scripts/libtie_prompt_bridge.py`

The WebUI textarea updater lives in:

- `javascript/libtie_prompt_bridge.js`
