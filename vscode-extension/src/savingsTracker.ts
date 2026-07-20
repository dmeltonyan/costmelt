/**
 * Cost Melt VS Code Extension - Savings Tracker
 *
 * Keeps a running total of what Cost Melt has saved you, shown in the
 * status bar. Persisted in globalState so it survives VS Code restarts
 * instead of resetting every session.
 */

import * as vscode from "vscode";
import { RouteResponse } from "./backendClient";

const TOTAL_SAVED_KEY = "costmelt.totalSaved";
const REQUEST_COUNT_KEY = "costmelt.requestCount";

export class SavingsTracker {
  private readonly statusBarItem: vscode.StatusBarItem;
  private totalSaved: number;
  private requestCount: number;

  constructor(private readonly context: vscode.ExtensionContext) {
    this.totalSaved = context.globalState.get<number>(TOTAL_SAVED_KEY, 0);
    this.requestCount = context.globalState.get<number>(REQUEST_COUNT_KEY, 0);

    this.statusBarItem = vscode.window.createStatusBarItem(
      vscode.StatusBarAlignment.Right,
      100
    );
    this.statusBarItem.command = "costmelt.focusChat";
    this.render();
    this.statusBarItem.show();
  }

  async record(response: RouteResponse): Promise<void> {
    this.totalSaved += response.cost.absolute_savings;
    this.requestCount += 1;
    await this.context.globalState.update(TOTAL_SAVED_KEY, this.totalSaved);
    await this.context.globalState.update(REQUEST_COUNT_KEY, this.requestCount);
    this.render();
  }

  private render(): void {
    this.statusBarItem.text = `$(zap) Cost Melt: $${this.totalSaved.toFixed(4)} saved`;
    this.statusBarItem.tooltip =
      this.requestCount > 0
        ? `${this.requestCount} request(s) routed through Cost Melt — click to open chat`
        : "No requests yet — click to open Cost Melt chat";
  }

  dispose(): void {
    this.statusBarItem.dispose();
  }
}
