const messagesEl = document.getElementById("messages");
const formEl = document.getElementById("chat-form");
const inputEl = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");
const themeBtn = document.getElementById("theme-btn");
const infoBtn = document.getElementById("info-btn");
const infoDialog = document.getElementById("info-dialog");
const infoClose = document.getElementById("info-close");

const MAX_HISTORY = 20;
const history = [];

initTheme();

function initTheme() {
  const saved = localStorage.getItem("theme");
  const prefersLight = window.matchMedia("(prefers-color-scheme: light)").matches;
  setTheme(saved || (prefersLight ? "light" : "dark"), false);
}

function setTheme(theme, persist = true) {
  document.documentElement.dataset.theme = theme;
  if (persist) localStorage.setItem("theme", theme);
}

themeBtn.addEventListener("click", () => {
  setTheme(document.documentElement.dataset.theme === "light" ? "dark" : "light");
});

infoBtn.addEventListener("click", () => infoDialog.showModal());
infoClose.addEventListener("click", () => infoDialog.close());
infoDialog.addEventListener("click", (event) => {
  if (event.target === infoDialog) infoDialog.close();
});

formEl.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;

  inputEl.value = "";
  sendBtn.disabled = true;
  addMessage("user", text);

  const loadingEl = addMessage("assistant", "Thinking...");
  loadingEl.classList.add("loading");

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, history }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => null);
      throw new Error(error?.detail || `Request failed (${response.status})`);
    }

    const data = await response.json();
    loadingEl.querySelector(".bubble").textContent = data.reply;
    loadingEl.classList.remove("loading");
    history.push({ role: "user", content: text });
    history.push({ role: "assistant", content: data.reply });
    if (history.length > MAX_HISTORY) history.splice(0, history.length - MAX_HISTORY);
  } catch (err) {
    loadingEl.classList.remove("loading");
    loadingEl.classList.add("error");
    loadingEl.querySelector(".bubble").textContent = err.message;
  } finally {
    sendBtn.disabled = false;
    inputEl.focus();
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }
});

function addMessage(role, text) {
  const wrapper = document.createElement("div");
  wrapper.className = `message ${role}`;
  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;
  wrapper.appendChild(bubble);
  messagesEl.appendChild(wrapper);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrapper;
}
