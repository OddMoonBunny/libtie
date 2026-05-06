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

function libtieAddPromptToWebui(positive, negative, mode, targetTab) {
  const tab = targetTab === "img2img" ? "img2img" : "txt2img";
  const promptArea = libtieTextAreaForId(`${tab}_prompt`);
  const negativeArea = libtieTextAreaForId(`${tab}_neg_prompt`);

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
      payload.target || "txt2img"
    );
  } catch (_error) {
    // WebUI may still be starting or the extension endpoint may be unavailable.
  }
}

setInterval(libtiePollPromptBridge, 750);
