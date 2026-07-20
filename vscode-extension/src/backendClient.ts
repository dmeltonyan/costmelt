/**
 * Cost Melt VS Code Extension - Backend Client
 *
 * Talks to the Cost Melt backend's /v1/route endpoint. Kept deliberately
 * small and dependency-free (uses the extension host's built-in fetch,
 * available since VS Code bundles Node 18+) rather than pulling in axios
 * like the standalone SDKs — a VS Code extension should stay lightweight.
 */

import * as vscode from "vscode";

export const SECRET_KEY_ID = "costmelt.apiKey";

export interface CostSummary {
  actual_cost: number;
  baseline_cost: number;
  absolute_savings: number;
  savings_pct: number;
}

export interface RouteResponse {
  response: string;
  model_used: string;
  complexity: number;
  cache_hit: boolean;
  tokens_in: number;
  tokens_out: number;
  cost: CostSummary;
  latency_ms: number;
}

export class CostMeltApiError extends Error {
  constructor(message: string, public readonly statusCode?: number) {
    super(message);
    this.name = "CostMeltApiError";
  }
}

export class BackendClient {
  constructor(private readonly context: vscode.ExtensionContext) {}

  private getBackendUrl(): string {
    const configured = vscode.workspace
      .getConfiguration("costmelt")
      .get<string>("backendUrl");
    return (configured || "http://localhost:8000").replace(/\/$/, "");
  }

  async getApiKey(): Promise<string | undefined> {
    return this.context.secrets.get(SECRET_KEY_ID);
  }

  async setApiKey(key: string): Promise<void> {
    await this.context.secrets.store(SECRET_KEY_ID, key);
  }

  async clearApiKey(): Promise<void> {
    await this.context.secrets.delete(SECRET_KEY_ID);
  }

  /**
   * Send a prompt through Cost Melt's routing pipeline.
   *
   * Throws CostMeltApiError for anything that isn't a clean 200 —
   * callers are expected to catch it and show a friendly message rather
   * than letting a raw exception surface in VS Code's UI.
   */
  async route(prompt: string): Promise<RouteResponse> {
    const apiKey = await this.getApiKey();
    if (!apiKey) {
      throw new CostMeltApiError(
        "No API key set. Run \"Cost Melt: Set API Key\" first."
      );
    }

    const url = `${this.getBackendUrl()}/v1/route`;

    let response: Response;
    try {
      response = await fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${apiKey}`,
        },
        body: JSON.stringify({ prompt }),
      });
    } catch (err) {
      throw new CostMeltApiError(
        `Could not reach the Cost Melt backend at ${url}. Is it running? (${
          err instanceof Error ? err.message : String(err)
        })`
      );
    }

    if (!response.ok) {
      const body = await response.json().catch(() => null) as
        | { message?: string; error?: string }
        | null;
      const message =
        body?.message || body?.error || `Request failed with status ${response.status}`;
      throw new CostMeltApiError(message, response.status);
    }

    return (await response.json()) as RouteResponse;
  }
}
