(() => {
  const { extractPageText, summarizeForSend } = window.stopFakeHelpers || {};
  if (!extractPageText) return;

  function analyzeIfEnabled() {
    chrome.storage.sync.get(
      { autoAnalyze: true },
      ({ autoAnalyze }) => {
        if (!autoAnalyze) return;
        const text = extractPageText();
        if (!text || text.length < 50) return;
        chrome.runtime.sendMessage({
          type: "page_text",
          text: summarizeForSend(text),
        });
      },
    );
  }

  // Slight delay to allow page to render.
  setTimeout(analyzeIfEnabled, 1200);

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg.type === "manual_analyze") {
      analyzeIfEnabled();
      sendResponse({ ok: true });
      return true;
    }
    return false;
  });
})();

