import { apiFetch, getWatchlistRound, pollBackend, postAccountSnapshot, postPostMetrics } from "./shared/api";
import { buildRoundPlan } from "./shared/round";
import { captureLimits } from "./shared/capture-settings";
import { withTimeout } from "./shared/timeout";
import { buildSyncQueue } from "./shared/sync";
import type { WatchlistTask } from "./shared/types";

const POLL_ALARM = "poll";
const ROUND_ALARM = "round_next";
const ROUND_STATE_KEY = "roundState";
const SYNC_ALARM = "sync_next";
const SYNC_STATE_KEY = "syncState";
const ANALYTICS_ALARM = "analytics_daily";
const SECURITY_ICON =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=";

interface SyncState {
  urns: string[];
  index: number;
  metrics: number;
  failed: number;
}

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
  } else if (alarm.name === SYNC_ALARM) {
    void processNextSyncMetric();
  } else if (alarm.name === ANALYTICS_ALARM) {
    void syncAccountData().finally(() => {
      void scheduleAnalyticsSync();
    });
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
  if (msg?.type === "SYNC_ACCOUNT") {
    void syncAccountData()
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ error: String(error) }));
    return true;
  }
  return undefined;
});

async function scheduleAnalyticsSync(): Promise<void> {
  const settings = await apiFetch<Record<string, string>>("/api/settings").catch(
    (): Record<string, string> => ({}),
  );
  const rawHour = Number(settings.analytics_sync_hour ?? 9);
  const hour = Number.isFinite(rawHour) ? Math.min(Math.max(Math.trunc(rawHour), 0), 23) : 9;
  const now = new Date();
  const next = new Date(now);
  next.setHours(hour, 0, 0, 0);
  if (next.getTime() <= now.getTime()) {
    next.setDate(next.getDate() + 1);
  }
  chrome.alarms.create(ANALYTICS_ALARM, { when: next.getTime() });
}

void ensurePollAlarm();
void scheduleAnalyticsSync();
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

async function sendMessageToTab(
  tabId: number,
  message: unknown,
  timeout = 20_000,
): Promise<any> {
  try {
    return await withTimeout(chrome.tabs.sendMessage(tabId, message), timeout, "content_script_timeout");
  } catch {
    await chrome.scripting.executeScript({ target: { tabId }, files: ["content/main.js"] });
    return await withTimeout(chrome.tabs.sendMessage(tabId, message), timeout, "content_script_timeout");
  }
}

async function getSyncState(): Promise<SyncState | undefined> {
  const stored = await chrome.storage.local.get(SYNC_STATE_KEY);
  return stored[SYNC_STATE_KEY] as SyncState | undefined;
}

async function setSyncState(state: SyncState): Promise<void> {
  await chrome.storage.local.set({ [SYNC_STATE_KEY]: state });
}

async function clearSyncState(): Promise<void> {
  await chrome.storage.local.remove(SYNC_STATE_KEY);
}

async function finishSync(state: SyncState): Promise<void> {
  await clearSyncState();
  chrome.notifications.create({
    type: "basic",
    iconUrl: SECURITY_ICON,
    title: "账号数据同步完成",
    message: `帖子指标 ${state.metrics} 条，失败 ${state.failed} 条。`,
  });
}

async function processNextSyncMetric(): Promise<void> {
  const state = await getSyncState();
  if (!state) return;
  if (state.index >= state.urns.length) {
    await finishSync(state);
    return;
  }

  const urn = state.urns[state.index];
  let tabId: number | undefined;
  try {
    const tab = await chrome.tabs.create({
      url: `https://www.linkedin.com/analytics/post-summary/${urn}/`,
      active: true,
    });
    tabId = tab.id;
    if (!tabId) throw new Error("tab_create_failed");
    await Promise.race([waitForTabComplete(tabId).catch(() => undefined), sleep(8000)]);
    await sleep(2000 + Math.random() * 2000);
    const response = await sendMessageToTab(tabId, { type: "EXTRACT_POST_METRICS" });
    if (!response?.ok) {
      if (response?.error === "security_challenge") {
        notifySecurityChallenge();
        await clearSyncState();
        return;
      }
      throw new Error(response?.error || "post_metrics_failed");
    }
    await postPostMetrics(response.metrics);
    state.metrics += 1;
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
  await setSyncState(state);
  if (state.index < state.urns.length) {
    chrome.alarms.create(SYNC_ALARM, { delayInMinutes: 0.4 });
  } else {
    await finishSync(state);
  }
}

export async function syncAccountData(): Promise<any> {
  if (await getSyncState()) return { error: "sync_running" };

  const settings = await apiFetch<Record<string, string>>("/api/settings").catch((): Record<string, string> => ({}));
  const profileUrl = (settings.own_profile_url || "").trim();
  if (!profileUrl) return { error: "no_profile_url" };

  let tabId: number | undefined;
  try {
    const tab = await chrome.tabs.create({ url: profileUrl, active: false });
    tabId = tab.id;
    if (!tabId) throw new Error("tab_create_failed");
    await Promise.race([waitForTabComplete(tabId).catch(() => undefined), sleep(8000)]);
    await sleep(2000);
    const response = await sendMessageToTab(tabId, { type: "SYNC_PROFILE" });
    if (!response?.ok) {
      if (response?.error === "security_challenge") notifySecurityChallenge();
      return { error: response?.error || "profile_sync_failed" };
    }
    await postAccountSnapshot(response.snapshot);
    await apiFetch("/api/extension/capture", {
      method: "POST",
      body: JSON.stringify({
        page_url: response.page_url,
        page_type: "profile",
        posts: response.posts,
      }),
    });
    const urns = buildSyncQueue(response.posts);
    if (!urns.length) {
      await finishSync({ urns: [], index: 0, metrics: 0, failed: 0 });
      return { started: true, urns: 0 };
    }
    await setSyncState({ urns, index: 0, metrics: 0, failed: 0 });
    chrome.alarms.create(SYNC_ALARM, { delayInMinutes: 0.1 });
    return { started: true, urns: urns.length };
  } catch (error) {
    console.error("[LinkedIn 工作台] syncAccountData failed", error);
    return { error: String(error) };
  } finally {
    if (tabId !== undefined) {
      try {
        await chrome.tabs.remove(tabId);
      } catch {
        // tab already closed
      }
    }
  }
}

// Test/debug hooks; only reachable from the extension service worker context.
(globalThis as any).__lwSyncAccountData = syncAccountData;
(globalThis as any).__lwClearSync = async () => {
  await clearSyncState();
  chrome.alarms.clear(SYNC_ALARM);
};
