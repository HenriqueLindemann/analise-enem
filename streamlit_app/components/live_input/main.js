// Adapted from streamlit-keyup 0.3.0 (Zachary Blackwood); see LICENSE.
let initialized = false;
let timer;
let lastSent;
let frameHeight = 0;

function resizeFrame() {
  const height = Math.ceil(document.body.getBoundingClientRect().height) + 4;
  if (height !== frameHeight) {
    frameHeight = height;
    Streamlit.setFrameHeight(height);
  }
}

function onRender(event) {
  const theme = event.detail.theme;
  if (theme) {
    for (const [css, name] of Object.entries({
      "primary-color": "primaryColor", "background-color": "backgroundColor",
      "secondary-background-color": "secondaryBackgroundColor", "text-color": "textColor",
      "font": "font",
    })) document.documentElement.style.setProperty(`--${css}`, theme[name]);
  }
  // Python echoes values asynchronously. Do not replace drafts or selection.
  if (!initialized) {
    const {label, value, max_chars, debounce} = event.detail.args;
    const input = document.getElementById("input_box");
    document.getElementById("label").textContent = label;
    input.value = value || "";
    input.maxLength = max_chars;
    lastSent = input.value;
    const flush = () => {
      clearTimeout(timer);
      if (input.value !== lastSent) {
        lastSent = input.value;
        Streamlit.setComponentValue(lastSent);
      }
    };
    input.addEventListener("input", () => {
      clearTimeout(timer);
      timer = setTimeout(flush, debounce);
    });
    input.addEventListener("blur", flush);
    input.addEventListener("keydown", event => {
      if (event.key === "Enter" && !event.isComposing) flush();
    });
    new ResizeObserver(resizeFrame).observe(document.body);
    initialized = true;
  }
  resizeFrame();
}
Streamlit.events.addEventListener(Streamlit.RENDER_EVENT, onRender);
Streamlit.setComponentReady();
