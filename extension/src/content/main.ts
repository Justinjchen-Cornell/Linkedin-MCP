import { detectPageType, extractPostsFromDocument, isSecurityChallenge } from "./extract";
import { shouldInject } from "./guard";

if (shouldInject(window)) {
  (window as any).__linkedinWorkbenchInjected = true;

  chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
    if (msg?.type !== "CAPTURE_PAGE") return;
    (async () => {
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
    })();
    return true;
  });
}
