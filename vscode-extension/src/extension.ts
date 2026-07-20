/**
 * Cost Melt VS Code Extension - Entry Point
 */

import * as vscode from "vscode";
import { BackendClient } from "./backendClient";
import { ChatViewProvider } from "./chatViewProvider";
import { SavingsTracker } from "./savingsTracker";

export function activate(context: vscode.ExtensionContext): void {
  const client = new BackendClient(context);
  const savingsTracker = new SavingsTracker(context);
  const chatViewProvider = new ChatViewProvider(context.extensionUri, client, savingsTracker);

  context.subscriptions.push(
    savingsTracker,
    vscode.window.registerWebviewViewProvider(ChatViewProvider.viewType, chatViewProvider),

    vscode.commands.registerCommand("costmelt.setApiKey", async () => {
      const key = await vscode.window.showInputBox({
        title: "Cost Melt API Key",
        prompt: "Paste your Cost Melt API key (create one with scripts/create_admin_key.py)",
        password: true,
        ignoreFocusOut: true,
        validateInput: (value) =>
          value.trim().length === 0 ? "API key cannot be empty" : undefined,
      });

      if (key) {
        await client.setApiKey(key.trim());
        vscode.window.showInformationMessage("Cost Melt: API key saved securely.");
      }
    }),

    vscode.commands.registerCommand("costmelt.clearApiKey", async () => {
      await client.clearApiKey();
      vscode.window.showInformationMessage("Cost Melt: API key cleared.");
    }),

    vscode.commands.registerCommand("costmelt.focusChat", async () => {
      await vscode.commands.executeCommand("costmelt.chatView.focus");
    }),

    vscode.commands.registerCommand("costmelt.askAI", async () => {
      const editor = vscode.window.activeTextEditor;
      const selection = editor && !editor.selection.isEmpty
        ? editor.document.getText(editor.selection)
        : undefined;

      const prompt = selection ?? (await vscode.window.showInputBox({
        title: "Ask Cost Melt",
        prompt: "What do you want to ask?",
        ignoreFocusOut: true,
      }));

      if (!prompt || !prompt.trim()) {
        return;
      }

      const apiKey = await client.getApiKey();
      if (!apiKey) {
        const choice = await vscode.window.showWarningMessage(
          "Cost Melt: no API key set yet.",
          "Set API Key"
        );
        if (choice === "Set API Key") {
          await vscode.commands.executeCommand("costmelt.setApiKey");
        }
        return;
      }

      await chatViewProvider.injectPrompt(prompt);
    })
  );
}

export function deactivate(): void {
  // Nothing to clean up beyond what's registered in context.subscriptions.
}
