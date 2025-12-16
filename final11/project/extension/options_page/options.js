const backendInput = document.getElementById("backendUrl");
const autoAnalyzeInput = document.getElementById("autoAnalyze");
const saveBtn = document.getElementById("save");
const savedLabel = document.getElementById("saved");

const DEFAULT_CONFIG = {
  backendUrl: "http://localhost:8000/analyze",
  autoAnalyze: true,
};

function loadConfig() {
  chrome.storage.sync.get(DEFAULT_CONFIG, ({ backendUrl, autoAnalyze }) => {
    backendInput.value = backendUrl;
    autoAnalyzeInput.checked = Boolean(autoAnalyze);
  });
}

function saveConfig() {
  const backendUrl = backendInput.value.trim() || DEFAULT_CONFIG.backendUrl;
  const autoAnalyze = autoAnalyzeInput.checked;
  chrome.storage.sync.set({ backendUrl, autoAnalyze }, () => {
    savedLabel.classList.remove("hidden");
    setTimeout(() => savedLabel.classList.add("hidden"), 1200);
  });
}

saveBtn.addEventListener("click", saveConfig);
loadConfig();



