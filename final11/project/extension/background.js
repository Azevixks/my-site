const DEFAULT_CONFIG = {
  backendUrl: "http://localhost:8000/analyze",
  autoAnalyze: true,
};

const resultsByTab = {};

async function getConfig() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(DEFAULT_CONFIG, (cfg) => resolve(cfg));
  });
}

async function analyzeText(text, tabId) {
  const { backendUrl } = await getConfig();

  resultsByTab[tabId] = { status: "loading" };
  chrome.runtime.sendMessage({ type: "analysis_status", tabId, status: "loading" });

  try {
    const resp = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });

    if (!resp.ok) {
      throw new Error(`Backend returned ${resp.status}`);
    }

    const data = await resp.json();
    resultsByTab[tabId] = { status: "done", data };
    chrome.runtime.sendMessage({ type: "analysis_status", tabId, status: "done", data });
  } catch (err) {
    resultsByTab[tabId] = { status: "error", error: err.message };
    chrome.runtime.sendMessage({
      type: "analysis_status",
      tabId,
      status: "error",
      error: err.message,
    });
  }
}

chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "page_text" && sender.tab?.id) {
    analyzeText(msg.text, sender.tab.id);
    sendResponse({ ok: true });
    return true;
  }

  if (msg.type === "get_result") {
    const entry = resultsByTab[msg.tabId] || { status: "idle" };
    sendResponse(entry);
    return true;
  }
});

chrome.tabs.onRemoved.addListener((tabId) => {
  delete resultsByTab[tabId];
});



