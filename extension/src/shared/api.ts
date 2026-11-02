import type { PollResponse, WatchlistTask } from "./types";

const DEFAULT_BACKEND = "http://127.0.0.1:8765";

export async function getBackendUrl(): Promise<string> {
  const stored = await chrome.storage.local.get("backendUrl");
  return (stored.backendUrl as string) || DEFAULT_BACKEND;
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const base = await getBackendUrl();
  const response = await fetch(base + path, {
    ...init,
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
  });
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function pollBackend(): Promise<PollResponse> {
  return apiFetch<PollResponse>("/api/extension/poll", {
    method: "POST",
    body: JSON.stringify({
      extension_version: "0.1.0",
      last_seen: new Date().toISOString(),
    }),
  });
}

export async function getWatchlistRound(limit = 5): Promise<{ tasks: WatchlistTask[] }> {
  return apiFetch<{ tasks: WatchlistTask[] }>(`/api/watchlist/round?limit=${limit}`);
}
