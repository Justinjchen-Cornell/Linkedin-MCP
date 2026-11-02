import { pollBackend } from "./shared/api";

const POLL_ALARM = "poll";

function ensurePollAlarm(): void {
  chrome.alarms.create(POLL_ALARM, { periodInMinutes: 0.5 });
}

chrome.runtime.onInstalled.addListener(ensurePollAlarm);
chrome.runtime.onStartup.addListener(ensurePollAlarm);
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === POLL_ALARM) {
    void pollBackend().catch(() => undefined);
  }
});

void ensurePollAlarm();
void pollBackend().catch(() => undefined);
