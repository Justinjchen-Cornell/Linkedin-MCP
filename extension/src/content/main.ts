import { extractAccountSnapshot, hasProfileMetrics, hasProfilePosts } from "./analytics";
import { detectPageType, extractPostsFromDocument, isSecurityChallenge } from "./extract";
import { shouldInject } from "./guard";
import { extractPostMetrics, hasPostMetrics } from "./post_metrics";

if (shouldInject(window)) {
  window.__linkedinWorkbenchInjected = true;

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type === "SYNC_PROFILE") {
      (async () => {
        try {
          if (isSecurityChallenge(document)) {
            sendResponse({ ok: false, error: "security_challenge" });
            return;
          }
          const started = Date.now();
          while (Date.now() - started < 15000) {
            const text = document.body?.innerText || "";
            if (hasProfileMetrics(text) && hasProfilePosts(document)) break;
            if (!hasProfilePosts(document)) window.scrollBy(0, window.innerHeight * 0.8);
            await new Promise((resolve) => setTimeout(resolve, 500));
          }
          const snapshot = extractAccountSnapshot(document);
          const posts = extractPostsFromDocument(document, "profile").slice(0, 100);
          sendResponse({ ok: true, snapshot, posts, page_url: location.href });
        } catch (error) {
          console.error("[LinkedIn 工作台] profile sync failed", error);
          sendResponse({ ok: false, error: String(error) });
        }
      })();
      return true;
    }

    if (msg?.type === "EXTRACT_POST_METRICS") {
      (async () => {
        try {
          if (isSecurityChallenge(document)) {
            sendResponse({ ok: false, error: "security_challenge" });
            return;
          }
          window.scrollTo(0, document.body.scrollHeight);
          const started = Date.now();
          while (!hasPostMetrics(document.body?.innerText || "") && Date.now() - started < 10000) {
            await new Promise((resolve) => setTimeout(resolve, 500));
          }
          sendResponse({ ok: true, metrics: extractPostMetrics(document, location.href) });
        } catch (error) {
          console.error("[LinkedIn 工作台] post metrics failed", error);
          sendResponse({ ok: false, error: String(error) });
        }
      })();
      return true;
    }

    if (msg?.type !== "CAPTURE_PAGE") return;
    (async () => {
      try {
        if (isSecurityChallenge(document)) {
          sendResponse({ ok: false, error: "security_challenge" });
          return;
        }
        const source = msg.source ?? detectPageType(location.href);
        const screens = Math.min(Math.max(msg.scrollScreens ?? 0, 0), 3);
        for (let i = 0; i < screens; i++) {
          window.scrollBy(0, window.innerHeight * 0.9);
          await new Promise((resolve) => setTimeout(resolve, 2000 + Math.random() * 3000));
        }
        const maxPosts = Math.min(Math.max(Number(msg.maxPosts) || 100, 1), 100);
        const posts = extractPostsFromDocument(document, source, msg.keyword ?? null).slice(0, maxPosts);
        console.log("[LinkedIn 工作台] captured posts", posts.length);
        if (msg.dryRun) {
          sendResponse({
            ok: true,
            stats: {
              posts: posts.length,
              with_author: posts.filter((post) => post.author_name).length,
              with_text: posts.filter((post) => post.text).length,
            },
          });
          return;
        }
        sendResponse({
          ok: true,
          payload: { page_url: location.href, page_type: source, posts },
        });
      } catch (error) {
        console.error("[LinkedIn 工作台] capture failed", error);
        sendResponse({ ok: false, error: String(error) });
      }
    })();
    return true;
  });
}
