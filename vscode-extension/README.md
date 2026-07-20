# Cost Melt for VS Code

Ask AI questions right inside VS Code, routed through your own [Cost Melt](../README.md) backend — which automatically picks the cheapest model capable of answering, checks a semantic cache before spending anything, and shows you exactly what it saved on every single request.

This is a personal-use extension: it talks to a Cost Melt backend running on your own machine. It is not published to the Marketplace.

## Features

- **Cost Melt: Ask AI** — select some code (or nothing, and type a question) and get a routed AI answer without leaving your editor. Right-click a selection for the same command.
- **Chat panel** — a persistent sidebar chat (click the Cost Melt icon in the Activity Bar) for back-and-forth conversations.
- **Status bar savings tracker** — bottom-right corner shows a running total of what Cost Melt has saved you, updated after every request, and remembered across restarts.
- **Secure API key storage** — your key is stored with VS Code's built-in `SecretStorage`, never written to a settings file in plain text.

## Setup

1. Make sure your Cost Melt backend is running (`cd backend && uvicorn main:app --reload`) and has real Supabase + LLM provider credentials configured — see the main repo README.
2. Create yourself an API key: `python scripts/create_admin_key.py --user-id you@example.com`
3. In VS Code, run **Cost Melt: Set API Key** from the Command Palette (`Ctrl+Shift+P` / `Cmd+Shift+P`) and paste it in.
4. (Optional) If your backend isn't at `http://localhost:8000`, set `costmelt.backendUrl` in your VS Code settings.

## Using it

- **Command Palette → Cost Melt: Ask AI** — with no selection, it'll prompt you to type a question. With a code selection, it sends the selected code as the prompt (great for "explain this" or "what's wrong here").
- **Activity Bar → Cost Melt icon** — opens the persistent chat panel.
- **Cost Melt: Set/Clear API Key** — manage your stored key.

## Installing it locally (not from the Marketplace)

```bash
cd vscode-extension
npm install
npm run compile
npm run package        # produces costmelt-vscode-0.1.0.vsix
```

Then in VS Code: Extensions view → `...` menu (top-right) → **Install from VSIX...** → select the generated file.

## How it's built

- `src/extension.ts` — registers commands, the chat webview, and the status bar item.
- `src/backendClient.ts` — the only file that talks to the Cost Melt backend (`POST /v1/route`).
- `src/chatViewProvider.ts` — the sidebar chat panel. The webview (`media/chat.js`) only renders messages and posts user input back to the extension host; it never makes network calls itself, so your API key never enters the webview's sandboxed context.
- `src/savingsTracker.ts` — the status bar counter, persisted via `context.globalState`.
