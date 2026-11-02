import { apiFetch, getBackendUrl } from "../shared/api";

async function refreshStatus(): Promise<void> {
  const status = document.getElementById("status");
  if (!status) return;
  try {
    const data = await apiFetch<{ captured_posts: number }>("/api/extension/status");
    status.textContent = `已连接 · 已采集 ${data.captured_posts} 条`;
    status.style.background = "#e7f6ec";
  } catch {
    status.textContent = "未连接：请先启动本地后台";
    status.style.background = "#fdecea";
  }
}

async function init(): Promise<void> {
  const input = document.getElementById("backend") as HTMLInputElement | null;
  if (input) input.value = await getBackendUrl();

  document.getElementById("save")?.addEventListener("click", async () => {
    if (!input) return;
    await chrome.storage.local.set({ backendUrl: input.value.trim() });
    await refreshStatus();
  });

  document.getElementById("open")?.addEventListener("click", async () => {
    await chrome.tabs.create({ url: await getBackendUrl() });
  });

  await refreshStatus();
  setInterval(() => void refreshStatus(), 5000);
}

void init();
