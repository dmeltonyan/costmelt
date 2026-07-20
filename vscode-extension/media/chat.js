// Cost Melt VS Code Extension - Chat webview script
// Runs inside the webview's isolated context. Talks to the extension
// host exclusively via postMessage — it never calls the backend itself.
(function () {
  const vscode = acquireVsCodeApi();
  const messagesEl = document.getElementById("messages");
  const inputEl = document.getElementById("input");
  const sendBtn = document.getElementById("send");

  let thinkingEl = null;

  function addMessage(role, text, meta) {
    const wrapper = document.createElement("div");
    wrapper.className = "message " + role;

    const bubble = document.createElement("div");
    bubble.className = "bubble";
    bubble.textContent = text;
    wrapper.appendChild(bubble);

    if (meta) {
      const metaEl = document.createElement("div");
      metaEl.className = "meta";
      metaEl.textContent = meta;
      wrapper.appendChild(metaEl);
    }

    messagesEl.appendChild(wrapper);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return wrapper;
  }

  function send() {
    const text = inputEl.value.trim();
    if (!text) {
      return;
    }
    addMessage("user", text);
    vscode.postMessage({ command: "send", text: text });
    inputEl.value = "";
  }

  sendBtn.addEventListener("click", send);
  inputEl.addEventListener("keydown", function (e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  });

  window.addEventListener("message", function (event) {
    const msg = event.data;

    switch (msg.command) {
      case "addUserMessage":
        addMessage("user", msg.text);
        break;

      case "thinking":
        thinkingEl = addMessage("assistant thinking", "Thinking...");
        break;

      case "assistantMessage": {
        if (thinkingEl) {
          thinkingEl.remove();
          thinkingEl = null;
        }
        const r = msg.result;
        const cacheNote = r.cache_hit ? " (from cache)" : "";
        const meta =
          r.model_used +
          cacheNote +
          " · saved $" +
          r.cost.absolute_savings.toFixed(4) +
          " (" +
          r.cost.savings_pct.toFixed(1) +
          "%) · " +
          Math.round(r.latency_ms) +
          "ms";
        addMessage("assistant", r.response, meta);
        break;
      }

      case "errorMessage":
        if (thinkingEl) {
          thinkingEl.remove();
          thinkingEl = null;
        }
        addMessage("error", msg.message);
        break;
    }
  });

  vscode.postMessage({ command: "ready" });
}());
