const statusEl = document.getElementById("status");
const resultEl = document.getElementById("result");
const labelEl = document.getElementById("label");
const confidenceEl = document.getElementById("confidence");
const emotionEl = document.getElementById("emotion");
const emotionDescEl = document.getElementById("emotionDesc");
const reasonsEl = document.getElementById("reasons");
const errorEl = document.getElementById("error");
const refreshBtn = document.getElementById("refresh");

function renderState(state) {
  if (!state || state.status === "idle") {
    statusEl.textContent = "Очікування даних...";
    resultEl.classList.add("hidden");
    return;
  }

  if (state.status === "loading") {
    statusEl.textContent = "Аналізуємо текст...";
    resultEl.classList.add("hidden");
    return;
  }

  if (state.status === "error") {
    statusEl.textContent = "Сталася помилка";
    resultEl.classList.remove("hidden");
    labelEl.textContent = "—";
    labelEl.className = "";
    confidenceEl.textContent = "";
    emotionEl.textContent = "";
    emotionDescEl.textContent = "";
    reasonsEl.innerHTML = "";
    errorEl.textContent = state.error || "Невідома помилка";
    return;
  }

  const { data } = state;
  statusEl.textContent = "Готово";
  resultEl.classList.remove("hidden");
  labelEl.textContent = data.result === "fake" ? "❌ Фейк" : data.result === "real" ? "✅ Не фейк" : "⚠️ Невизначено";
  labelEl.className = data.result;
  confidenceEl.textContent = `Довіра: ${(data.confidence * 100).toFixed(0)}%`;
  let toneLabel;
  let toneExplain;
  if (data.emotion === "factual") {
    toneLabel = "нейтральний (factual)";
    toneExplain = "Текст поданий спокійно, по фактах, без емоційного тиску.";
  } else if (data.emotion === "emotional") {
    toneLabel = "емоційний (emotional)";
    toneExplain = "Багато емоційних/маніпулятивних висловів, що можуть впливати на сприйняття.";
  } else {
    toneLabel = "змішаний (mixed)";
    toneExplain = "Є і фактологія, і емоційні елементи; тон частково впливає на оцінку.";
  }
  emotionEl.textContent = `Тон: ${toneLabel}`;
  emotionDescEl.textContent = toneExplain;
  reasonsEl.innerHTML = "";
  errorEl.textContent = "";
  (data.reasons || []).forEach((reason) => {
    const li = document.createElement("li");
    li.textContent = reason;
    reasonsEl.appendChild(li);
  });
}

function requestState() {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    if (!tab) return;
    chrome.runtime.sendMessage({ type: "get_result", tabId: tab.id }, renderState);
  });
}

refreshBtn.addEventListener("click", () => {
  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    const tab = tabs[0];
    if (!tab?.id) return;
    chrome.tabs.sendMessage(tab.id, { type: "manual_analyze" }, () => {
      // Ignore errors when content script is missing.
      requestState();
    });
  });
});

// Listen for push updates from background.
chrome.runtime.onMessage.addListener((msg) => {
  if (msg.type === "analysis_status") {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (tabs[0]?.id === msg.tabId) {
        renderState({ status: msg.status, data: msg.data, error: msg.error });
      }
    });
  }
});

requestState();



