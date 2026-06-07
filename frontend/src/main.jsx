import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import App from "./App";

// ── Break out of the Hugging Face Spaces iframe ──────────────────────────────
// HF embeds the app in an iframe on huggingface.co/spaces/...; inside that
// frame, Google refuses to render its OAuth consent screen (X-Frame-Options),
// so sign-in 403s. Detect framing and bounce the WHOLE tab to our own URL,
// where OAuth works. window.location.href on the framed doc is still our app's
// URL, so this lands the user on the real hf.space page.
(function escapeIframe() {
  try {
    if (window.self !== window.top) {
      window.top.location.href = window.location.href;
    }
  } catch {
    // cross-origin: we can't read top, but we ARE framed — force the break.
    window.top.location.href = window.location.href;
  }
})();

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
