/**
 * Cost Melt VS Code Extension - Chat Sidebar Panel
 *
 * The webview (media/chat.js) never talks to the backend directly — it
 * only knows how to render messages and postMessage user input back to
 * this provider, which runs in the extension host (a normal Node.js
 * context) and does the actual HTTP call via BackendClient. This keeps
 * the API key and network access out of the webview's sandboxed,
 * less-trusted context.
 */

import * as vscode from "vscode";
import { BackendClient, CostMeltApiError } from "./backendClient";
import { SavingsTracker } from "./savingsTracker";

export class ChatViewProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = "costmelt.chatView";

  private view?: vscode.WebviewView;
  private pendingPrompt?: string;

  constructor(
    private readonly extensionUri: vscode.Uri,
    private readonly client: BackendClient,
    private readonly savingsTracker: SavingsTracker
  ) {}

  resolveWebviewView(webviewView: vscode.WebviewView): void {
    this.view = webviewView;

    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [vscode.Uri.joinPath(this.extensionUri, "media")],
    };
    webviewView.webview.html = this.getHtml(webviewView.webview);

    webviewView.webview.onDidReceiveMessage(async (message) => {
      if (message.command === "ready") {
        if (this.pendingPrompt) {
          const prompt = this.pendingPrompt;
          this.pendingPrompt = undefined;
          this.view?.webview.postMessage({ command: "addUserMessage", text: prompt });
          await this.handlePrompt(prompt);
        }
        return;
      }

      if (message.command === "send" && typeof message.text === "string") {
        await this.handlePrompt(message.text);
      }
    });
  }

  /** Called by the "Ask AI" command to inject a prompt (e.g. selected code). */
  async injectPrompt(prompt: string): Promise<void> {
    await vscode.commands.executeCommand("costmelt.chatView.focus");

    if (this.view) {
      this.view.webview.postMessage({ command: "addUserMessage", text: prompt });
      await this.handlePrompt(prompt);
    } else {
      // View hasn't been resolved yet (first activation) — the "ready"
      // handler above will flush this once it has been.
      this.pendingPrompt = prompt;
    }
  }

  private async handlePrompt(prompt: string): Promise<void> {
    if (!prompt.trim() || !this.view) {
      return;
    }

    this.view.webview.postMessage({ command: "thinking" });

    try {
      const result = await this.client.route(prompt);
      this.view.webview.postMessage({ command: "assistantMessage", result });
      await this.savingsTracker.record(result);
    } catch (err) {
      const message = err instanceof CostMeltApiError ? err.message : String(err);
      this.view.webview.postMessage({ command: "errorMessage", message });
    }
  }

  private getHtml(webview: vscode.Webview): string {
    const scriptUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "chat.js")
    );
    const styleUri = webview.asWebviewUri(
      vscode.Uri.joinPath(this.extensionUri, "media", "chat.css")
    );
    const nonce = getNonce();

    return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src 'nonce-${nonce}';" />
  <link href="${styleUri}" rel="stylesheet" />
  <title>Cost Melt Chat</title>
</head>
<body>
  <div id="messages"></div>
  <div id="input-row">
    <textarea id="input" rows="2" placeholder="Ask Cost Melt anything..."></textarea>
    <button id="send">Send</button>
  </div>
  <script nonce="${nonce}" src="${scriptUri}"></script>
</body>
</html>`;
  }
}

function getNonce(): string {
  let text = "";
  const possible = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
  for (let i = 0; i < 32; i++) {
    text += possible.charAt(Math.floor(Math.random() * possible.length));
  }
  return text;
}
