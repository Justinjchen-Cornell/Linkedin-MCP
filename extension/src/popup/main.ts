import { apiFetch, getBackendUrl } from "../shared/api";

function setMessage(text: string, ok = true): void {
  const message = document.getElementById("message");
  if (!message) return;
  message.textContent = text;
  message.style.color = ok ? "#166534" : "#b91c1c";
}

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

async function sendRuntime(message: unknown): Promise<any> {
  return chrome.runtime.sendMessage(message);
}

async function init(): Promise<void> {
  const input = document.getElementById("backend") as HTMLInputElement | null;
  if (input) input.value = await getBackendUrl();

  document.getElementById("save")?.addEventListener("click", async () => {
    if (!input) return;
    await chrome.storage.local.set({ backendUrl: input.value.trim() });
    setMessage("地址已保存");
    await refreshStatus();
  });

  document.getElementById("open")?.addEventListener("click", async () => {
    await chrome.tabs.create({ url: await getBackendUrl() });
  });

  document.getElementById("capture")?.addEventListener("click", async () => {
    setMessage("采集中…");
    const result = await sendRuntime({ type: "CAPTURE_ACTIVE_TAB" });
    if (result?.error) {
      setMessage(`采集失败：${result.error}`, false);
    } else {
      setMessage(`新增 ${result.inserted} 条，更新 ${result.updated} 条，跳过 ${result.skipped} 条`);
      await refreshStatus();
    }
  });

  document.getElementById("selfcheck")?.addEventListener("click", async () => {
    const result = await sendRuntime({ type: "CAPTURE_ACTIVE_TAB", dryRun: true });
    if (result?.stats) {
      setMessage(
        `找到 ${result.stats.posts} 条（作者 ${result.stats.with_author} / 正文 ${result.stats.with_text}）`,
      );
    } else {
      setMessage(`自检失败：${result?.error || "unknown"}`, false);
    }
  });

  await refreshStatus();
  setInterval(() => void refreshStatus(), 5000);
}

void init();
