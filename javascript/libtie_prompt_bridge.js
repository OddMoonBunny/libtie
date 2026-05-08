function libtieTextAreaForId(id) {
  const root = gradioApp();
  const wrapper = root.querySelector(`#${id}`);
  if (!wrapper) return null;
  return wrapper.querySelector("textarea");
}

function libtieSetPromptText(textarea, incoming, mode) {
  if (!textarea) return;

  const current = (textarea.value || "").trim();
  const next = (incoming || "").trim();
  let value = current;

  if (mode === "Replace") {
    value = next;
  } else if (next.length > 0) {
    value = current.length > 0 ? `${current}, ${next}` : next;
  }

  textarea.value = value;
  textarea.dispatchEvent(new Event("input", { bubbles: true }));
  textarea.dispatchEvent(new Event("change", { bubbles: true }));
}

function libtieRememberCategory(category) {
  const value = (category || "").trim();
  if (value.length > 0) {
    localStorage.setItem("libtieGalleryCategory", value);
  }
}

function libtieAddPromptToWebui(positive, negative, mode, targetTab, category) {
  const tab = targetTab === "img2img" ? "img2img" : "txt2img";
  const promptArea = libtieTextAreaForId(`${tab}_prompt`);
  const negativeArea = libtieTextAreaForId(`${tab}_neg_prompt`);

  libtieRememberCategory(category);
  libtieSetPromptText(promptArea, positive, mode);
  libtieSetPromptText(negativeArea, negative, mode);

  return [];
}

let libtieLastPromptId = 0;

async function libtiePollPromptBridge() {
  try {
    const response = await fetch("/libtie/prompt", { cache: "no-store" });
    if (!response.ok) return;

    const payload = await response.json();
    if (!payload || !payload.id || payload.id <= libtieLastPromptId) return;

    libtieLastPromptId = payload.id;
    libtieAddPromptToWebui(
      payload.positive || "",
      payload.negative || "",
      payload.mode || "Replace",
      payload.target || "txt2img",
      payload.category || ""
    );
  } catch (_error) {
    // WebUI may still be starting or the extension endpoint may be unavailable.
  }
}

setInterval(libtiePollPromptBridge, 750);

function libtieSelectedImageDataUrl() {
  const root = gradioApp();
  const selected = root.querySelector(
    "#txt2img_gallery .thumbnail-item.selected img, #txt2img_gallery .thumbnail-item:focus img, #txt2img_gallery img"
  );
  if (!selected) return null;

  const src = selected.currentSrc || selected.src || "";
  if (src.startsWith("data:image/")) return src;

  const canvas = document.createElement("canvas");
  canvas.width = selected.naturalWidth || selected.width;
  canvas.height = selected.naturalHeight || selected.height;
  const context = canvas.getContext("2d");
  context.drawImage(selected, 0, 0);
  return canvas.toDataURL("image/png");
}

async function libtieSendSelectedImageToGallery() {
  const image = libtieSelectedImageDataUrl();
  if (!image) {
    alert("libtie could not find a selected txt2img gallery image.");
    return;
  }

  const response = await fetch("http://127.0.0.1:8797/libtie/gallery/", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ image }),
  });
  const payload = await response.json();

  if (!response.ok || !payload.ok) {
    alert(`libtie gallery save failed: ${payload.error || response.statusText}`);
    return;
  }

  alert("Saved to the selected Prompt Library gallery.");
}

function libtieCreateGalleryButton() {
  const button = document.createElement("button");
  button.type = "button";
  button.title = "Send selected image to Prompt Library gallery";
  button.textContent = "PL";
  button.className = "lg secondary gradio-button tool";
  button.style.minWidth = "42px";
  button.addEventListener("click", libtieSendSelectedImageToGallery);
  return button;
}

function libtieInstallGalleryButton() {
  const root = gradioApp();
  const gallery = root.querySelector("#txt2img_gallery");
  if (!gallery || root.querySelector("#libtie_send_gallery")) return;

  const buttons = gallery.parentElement?.querySelector(".form") || gallery.parentElement;
  if (!buttons) return;

  const button = libtieCreateGalleryButton();
  button.id = "libtie_send_gallery";
  buttons.appendChild(button);
}

setInterval(libtieInstallGalleryButton, 1000);
