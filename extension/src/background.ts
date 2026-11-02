import { apiFetch, pollBackend } from "./shared/api";

const POLL_ALARM = "poll";
const SECURITY_ICON =
  "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII=";

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

async function sendCaptureToTab(tabId: number, source?: string, dryRun?: boolean): Promise<any> {
  const message = { type: "CAPTURE_PAGE", source, dryRun };
  try {
    return await chrome.tabs.sendMessage(tabId, message);
  } catch {
    await chrome.scripting.executeScript({ target: { tabId }, files: ["content/main.js"] });
    return await chrome.tabs.sendMessage(tabId, message);
  }
}

export async function captureActiveTab(source?: string, dryRun = false): Promise<any> {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id) return { error: "no_active_tab" };
  if (!tab.url?.includes("linkedin.com")) return { error: "not_linkedin" };

  const response = await sendCaptureToTab(tab.id, source, dryRun);
  if (!response?.ok) {
    if (response?.error === "security_challenge") notifySecurityChallenge();
    return { error: response?.error || "capture_failed" };
  }
  if (dryRun) return { stats: response.stats };

  return apiFetch<{ inserted: number; updated: number; skipped: number }>(
    "/api/extension/capture",
    { method: "POST", body: JSON.stringify(response.payload) },
  );
}

chrome.runtime.onInstalled.addListener(ensurePollAlarm);
chrome.runtime.onStartup.addListener(ensurePollAlarm);
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === POLL_ALARM) {
    void pollBackend().catch(() => undefined);
  }
});

chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "CAPTURE_ACTIVE_TAB") {
    void captureActiveTab(msg.source, Boolean(msg.dryRun))
      .then((result) => sendResponse(result))
      .catch((error) => sendResponse({ error: String(error) }));
    return true;
  }
  return undefined;
});

void ensurePollAlarm();
void pollBackend().catch(() => undefined);
