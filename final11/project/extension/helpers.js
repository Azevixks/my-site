// Helpers for extracting and cleaning visible text from the page.
function extractPageText() {
  const selectors = ["article", "main", "[role='article']", ".post", ".news"];
  let text = "";

  for (const selector of selectors) {
    const el = document.querySelector(selector);
    if (el && el.innerText) {
      text = el.innerText;
      break;
    }
  }

  if (!text) {
    text = document.body?.innerText || "";
  }

  return text.trim().replace(/\s+/g, " ");
}

function summarizeForSend(text, maxChars = 4000) {
  if (text.length <= maxChars) return text;
  // Keep the beginning and end to preserve context.
  const head = text.slice(0, Math.floor(maxChars * 0.7));
  const tail = text.slice(-Math.floor(maxChars * 0.2));
  return `${head}\n...\n${tail}`;
}

// Expose globally for other scripts loaded after this file.
window.stopFakeHelpers = { extractPageText, summarizeForSend };

