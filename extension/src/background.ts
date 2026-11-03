import { apiFetch, getWatchlistRound, pollBackend } from "./shared/api";
import { buildRoundPlan } from "./shared/round";
import { captureLimits } from "./shared/capture-settings";
import { withTimeout } from "./shared/timeout";
import type { WatchlistTask } from "./shared/types";

const POLL_ALARM = "poll";
const ROUND_ALARM = "round_next";
const ROUND_STATE_KEY = "roundState";
const SECURITY_ICON =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=";

interface RoundState {
  tasks: WatchlistTask[];
  index: number;
  captured: number;
  failed: number;
  scrollScreens: number;
  maxPosts: number;
}

function ensurePollAlarm(): void {
  chrome.alarms.create(POLL_ALARM, { periodInMinutes: 0.5 });
}

function notifySecurityChallenge(): void {
  chrome.notifications.create({
    type: "basic",
    iconUrl: SECURITY_ICON,
    title: "LinkedIn 要求验证",
    message: "请手动完成验证后再采集；本轮已停止。",
  });
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function waitForTabComplete(tabId: number): Promise<void> {
  return new Promise((resolve, reject) => {
    let settled = false;
    const finish = (): void => {
      if (settled) return;
      settled = true;
      chrome.tabs.onUpdated.removeListener(listener);
      clearTimeout(timer);
      resolve();
    };
    const listener = (id: number, info: any): void => {
      if (id === tabId && info.status === "complete") finish();
    };
    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      chrome.tabs.onUpdated.removeListener(listener);
      reject(new Error("tab_timeout"));
    }, 30_000);
    chrome.tabs.onUpdated.addListener(listener);
    void chrome.tabs.get(tabId).then((tab) => {
      if (tab.status === "complete") finish();
    }).catch(() => undefined);
  });
}

async function sendCaptureToTab(
  tabId: number,
  source?: string,
  dryRun = false,
  scrollScreens?: number,
  keyword?: string | null,
  maxPosts = 100,
): Promise<any> {
  const message = { type: "CAPTURE_PAGE", source, dryRun, scrollScreens, keyword, maxPosts };
  try {
    return await withTimeout(chrome.tabs.sendMessage(tabId, message), 20000, "content_script_timeout");
  } catch {
    await chrome.scripting.executeScript({ target: { tabId }, files: ["content/main.js"] });
    return await withTimeout(chrome.tabs.sendMessage(tabId, message), 20000, "content_script_timeout");
  }
}

export async function captureActiveTab(
  source?: string,
  dryRun = false,
  scrollScreens = 0,
  maxPosts = 100,
): Promise<any> {
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    if (!tab?.id) return { error: "no_active_tab" };
    if (!tab.url?.includes("linkedin.com")) return { error: "not_linkedin" };

    const response = await sendCaptureToTab(tab.id, source, dryRun, scrollScreens, null, maxPosts);
    console.log("[LinkedIn 工作台] content response", response);
    if (!response?.ok) {
      if (response?.error === "security_challenge") notifySecurityChallenge();
      return { error: response?.error || "capture_failed" };
    }
    if (dryRun) return { stats: response.stats };

    return apiFetch<{ inserted: number; updated: number; skipped: number }>(
      "/api/extension/capture",
      { method: "POST", body: JSON.stringify(response.payload) },
    );
  } catch (error) {
    console.error("[LinkedIn 工作台] captureActiveTab failed", error);
    return { error: String(error) };
  }
}

chrome.runtime.onInstalled.addListener(ensurePollAlarm);
chrome.runtime.onStartup.addListener(ensurePollAlarm);
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === POLL_ALARM) {
    void pollBackend().catch(() => undefined);
  } else if (alarm.name === ROUND_ALARM) {
    void processNextRoundTask();
  }
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "CAPTURE_ACTIVE_TAB") {
    void captureActiveTab(msg.source, Boolean(msg.dryRun), msg.scrollScreens, msg.maxPosts)
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ error: String(error) }));
    return true;
  }
  if (msg?.type === "RUN_ROUND") {
    void runWatchlistRound()
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ error: String(error) }));
    return true;
  }
  return undefined;
});

void ensurePollAlarm();
void pollBackend().catch(() => undefined);

async function getRoundState(): Promise<RoundState | undefined> {
  const stored = await chrome.storage.local.get(ROUND_STATE_KEY);
  return stored[ROUND_STATE_KEY] as RoundState | undefined;
}

async function setRoundState(state: RoundState): Promise<void> {
  await chrome.storage.local.set({ [ROUND_STATE_KEY]: state });
}

async function clearRoundState(): Promise<void> {
  await chrome.storage.local.remove(ROUND_STATE_KEY);
}

async function finishRound(state: RoundState): Promise<void> {
  await clearRoundState();
  chrome.notifications.create({
    type: "basic",
    iconUrl: SECURITY_ICON,
    title: "采集完成",
    message: `本轮完成：新增/更新 ${state.captured} 条，失败 ${state.failed} 个。`,
  });
}

async function processNextRoundTask(): Promise<void> {
  const state = await getRoundState();
  if (!state) return;
  if (state.index >= state.tasks.length) {
    await finishRound(state);
    return;
  }

  const task = state.tasks[state.index];
  let tabId: number | undefined;
  try {
    const tab = await chrome.tabs.create({ url: task.url, active: false });
    tabId = tab.id;
    if (!tabId) throw new Error("tab_create_failed");
    await waitForTabComplete(tabId);
    await sleep(2000 + Math.random() * 3000);
    const response = await sendCaptureToTab(
      tabId,
      task.kind === "hashtag" ? "hashtag" : "search",
      false,
      state.scrollScreens,
      task.value,
      state.maxPosts,
    );
    if (!response?.ok) {
      if (response?.error === "security_challenge") {
        notifySecurityChallenge();
        await clearRoundState();
        return;
      }
      throw new Error(response?.error || "capture_failed");
    }
    const result = await apiFetch<{ inserted: number; updated: number }>(
      "/api/extension/capture",
      { method: "POST", body: JSON.stringify(response.payload) },
    );
    state.captured += result.inserted + result.updated;
  } catch {
    state.failed += 1;
  } finally {
    if (tabId !== undefined) {
      try {
        await chrome.tabs.remove(tabId);
      } catch {
        // tab already closed
      }
    }
  }

  state.index += 1;
  await setRoundState(state);
  if (state.index < state.tasks.length) {
    chrome.alarms.create(ROUND_ALARM, { delayInMinutes: 1 });
  } else {
    await finishRound(state);
  }
}

export async function runWatchlistRound(): Promise<any> {
  if (await getRoundState()) return { error: "round_running" };
  const { tasks } = await getWatchlistRound(5);
  const plan = buildRoundPlan(tasks);
  if (!plan.length) return { error: "no_tasks" };
  const settings = await apiFetch<Record<string, string>>("/api/settings").catch(() => ({}));
  const limits = captureLimits(settings);
  await setRoundState({ tasks: plan, index: 0, captured: 0, failed: 0, ...limits });
  void processNextRoundTask();
  return { started: true, count: plan.length };
}
