export function fillScheduleId(url: string): number | null {
  try {
    const value = new URL(url).searchParams.get("lw_fill");
    if (!value || !/^\d+$/.test(value)) return null;
    return Number(value);
  } catch {
    return null;
  }
}

function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function findStartPost(): HTMLElement | null {
  const elements = Array.from(
    document.querySelectorAll<HTMLElement>("button, [role='button'], div"),
  );
  return (
    elements.find((element) => {
      const text = (element.innerText || "").trim().toLowerCase();
      const aria = (element.getAttribute("aria-label") || "").toLowerCase();
      return (
        text === "start a post" ||
        text === "开始发帖" ||
        aria.includes("start a post") ||
        aria.includes("开始发帖")
      );
    }) ?? null
  );
}

function composerRoot(): ShadowRoot | Document | null {
  const outlet = document.querySelector("#interop-outlet");
  return outlet?.shadowRoot ?? document;
}

async function waitForEditor(timeout = 12_000): Promise<HTMLElement | null> {
  const started = Date.now();
  while (Date.now() - started < timeout) {
    const root = composerRoot();
    const editor = root?.querySelector<HTMLElement>(
      "[contenteditable='true'], div.ql-editor, div[role='textbox']",
    );
    if (editor) return editor;
    await sleep(500);
  }
  return null;
}

function fillEditor(editor: HTMLElement, text: string): void {
  editor.focus();
  const inserted = document.execCommand("insertText", false, text);
  if (!inserted || !(editor.innerText || "").trim()) {
    editor.innerText = text;
    editor.dispatchEvent(new Event("input", { bubbles: true }));
  }
}

function attachImageBytes(editor: HTMLElement, bytes: number[], type: string): void {
  try {
    const blob = new Blob([new Uint8Array(bytes)], { type });
    const file = new File([blob], "image.png", { type });
    const transfer = new DataTransfer();
    transfer.items.add(file);
    editor.dispatchEvent(
      new ClipboardEvent("paste", {
        bubbles: true,
        cancelable: true,
        clipboardData: transfer,
      }),
    );
  } catch {
    // image is best-effort
  }
}

function findPostButton(root: ShadowRoot | Document | null): HTMLButtonElement | null {
  if (!root) return null;
  const buttons = Array.from(root.querySelectorAll<HTMLButtonElement>("button"));
  return (
    buttons.find((button) => {
      const text = (button.innerText || "").trim().toLowerCase();
      const aria = (button.getAttribute("aria-label") || "").toLowerCase();
      return text === "post" || text === "发布" || aria === "post" || aria === "发布";
    }) ?? null
  );
}

function showOverlay(
  message: string,
  text: string,
  scheduleId: number,
  root: ShadowRoot | Document | null,
): void {
  document.getElementById("lw-autofill-bar")?.remove();
  const bar = document.createElement("div");
  bar.id = "lw-autofill-bar";
  bar.style.cssText =
    "position:fixed;left:16px;right:16px;bottom:16px;z-index:99999;background:#0a66c2;color:#fff;padding:12px 16px;border-radius:10px;font:14px -apple-system,'PingFang SC','Microsoft YaHei',sans-serif;display:flex;gap:10px;align-items:center;box-shadow:0 4px 18px rgba(0,0,0,.25)";
  const label = document.createElement("span");
  label.textContent = message;
  label.style.flex = "1";
  const button = (caption: string): HTMLButtonElement => {
    const element = document.createElement("button");
    element.textContent = caption;
    element.style.cssText =
      "padding:7px 12px;border:0;border-radius:7px;background:#fff;color:#0a66c2;cursor:pointer;font:inherit";
    return element;
  };
  const copy = button("复制文本");
  copy.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(text);
      label.textContent = "已复制。";
    } catch {
      label.textContent = "复制失败，请手动选择文本。";
    }
  });
  const confirm = button("确认发布");
  confirm.addEventListener("click", async () => {
    const post = findPostButton(root);
    if (!post) {
      label.textContent = "找不到发布按钮，请手动点 Post。";
      return;
    }
    post.click();
    await chrome.runtime.sendMessage({ type: "MARK_PUBLISHED", id: scheduleId }).catch(
      () => undefined,
    );
    label.textContent = "已点击发布，请在 LinkedIn 确认。";
  });
  const close = button("关闭");
  close.addEventListener("click", () => bar.remove());
  bar.append(label, copy, confirm, close);
  document.body.append(bar);
}

export async function maybeAutofill(): Promise<void> {
  const scheduleId = fillScheduleId(location.href);
  if (scheduleId === null) return;

  const result = await chrome.runtime.sendMessage({
    type: "GET_SCHEDULE",
    id: scheduleId,
  });
  if (!result?.ok) {
    showOverlay("连不上本地后台，无法自动填入。", "", scheduleId, null);
    return;
  }
  const data = result.data;

  const text = data.draft_body || "";
  if (!text) {
    showOverlay("这条排期没有正文。", "", scheduleId, null);
    return;
  }

  findStartPost()?.click();
  const editor = await waitForEditor();
  if (!editor) {
    showOverlay(
      "自动填入失败：找不到发布框。请用日历的“复制并打开 LinkedIn”。",
      text,
      scheduleId,
      null,
    );
  } else {
    fillEditor(editor, text);
    if (data.image_url) {
      const image = await chrome.runtime.sendMessage({
        type: "FETCH_IMAGE",
        url: data.image_url,
      });
      if (image?.ok) {
        attachImageBytes(editor, image.bytes, image.type);
      }
    }
    showOverlay(
      "已填入，请在 LinkedIn 检查后点发布。",
      text,
      scheduleId,
      composerRoot(),
    );
  }
  history.replaceState(null, "", location.pathname);
}
