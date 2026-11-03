import type { CaptureSource, CapturedCommentPayload, CapturedPostPayload } from "../shared/types";
import {
  AUTHOR_LINK_SELECTORS,
  AUTHOR_NAME_SELECTORS,
  COMMENT_AUTHOR_SELECTORS,
  COMMENT_COUNT_SELECTORS,
  COMMENT_ITEM_SELECTORS,
  COMMENT_TEXT_SELECTORS,
  HEADLINE_SELECTORS,
  PERMALINK_SELECTORS,
  POST_SELECTORS,
  REACTION_SELECTORS,
  REPOST_SELECTORS,
  TEXT_SELECTORS,
} from "../shared/selectors";

function pick(root: Element, selectors: string[]): Element | null {
  for (const selector of selectors) {
    const found = root.querySelector(selector);
    if (found) return found;
  }
  return null;
}

function textOf(el: Element | null): string {
  if (!el) return "";
  const html = el as HTMLElement;
  return (html.innerText || el.textContent || "").trim();
}

function firstText(root: Element, selectors: string[]): string {
  for (const selector of selectors) {
    const found = root.querySelector(selector);
    const value = textOf(found);
    if (value) return value;
  }
  return "";
}

function absoluteUrl(href: string | null): string | null {
  if (!href) return null;
  try {
    return new URL(href, "https://www.linkedin.com").toString();
  } catch {
    return null;
  }
}

function normalizeUrl(url: string | null): string | null {
  if (!url) return null;
  try {
    const parsed = new URL(url);
    parsed.search = "";
    parsed.hash = "";
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return url;
  }
}

export function parseCount(label: string | null | undefined): number {
  if (!label) return 0;
  const cleaned = label.replace(/,/g, "").replace(/\s+/g, " ").trim();
  const match = cleaned.match(/([\d.]+)\s*([KkMm]?)/);
  if (!match) return 0;
  const value = Number.parseFloat(match[1]);
  if (!Number.isFinite(value)) return 0;
  const unit = match[2].toUpperCase();
  const multiplier = unit === "K" ? 1_000 : unit === "M" ? 1_000_000 : 1;
  return Math.round(value * multiplier);
}

function countFrom(root: Element, selectors: string[]): number {
  for (const selector of selectors) {
    const found = root.querySelector(selector);
    if (!found) continue;
    const label = `${found.getAttribute("aria-label") || ""} ${textOf(found)}`.trim();
    if (label) return parseCount(label);
  }
  return 0;
}

const NEW_POST_SELECTOR = "div[role='listitem'][componentkey^='update-card-focus']";
const OLD_POST_SELECTOR =
  "div.feed-shared-update-v2[data-urn], div[data-urn^='urn:li:activity'], li[data-urn^='urn:li:activity']";

function extractAuthorName(el: Element): string {
  for (const prefix of ["Open control menu for post by ", "Hide post by "]) {
    const button = el.querySelector(`button[aria-label^='${prefix}']`);
    const label = button?.getAttribute("aria-label");
    if (label) return label.slice(prefix.length).trim();
  }
  const avatar = el.querySelector("img[alt^='View ']") as HTMLImageElement | null;
  if (avatar?.alt) {
    const match = avatar.alt.match(/^View (.+?)[’']s profile/);
    if (match) return match[1].trim();
  }
  return firstText(el, AUTHOR_NAME_SELECTORS);
}

function extractAuthorLink(el: Element): HTMLAnchorElement | null {
  const avatar = el.querySelector("img[alt^='View ']");
  const link = avatar?.closest("a[href*='/in/']");
  if (link) return link as HTMLAnchorElement;
  return pick(el, AUTHOR_LINK_SELECTORS) as HTMLAnchorElement | null;
}

function extractComments(el: Element): CapturedCommentPayload[] {
  const items = Array.from(el.querySelectorAll(COMMENT_ITEM_SELECTORS.join(","))).slice(0, 20);
  return items
    .map((item) => ({
      author_name: firstText(item, COMMENT_AUTHOR_SELECTORS),
      author_url: absoluteUrl((pick(item, AUTHOR_LINK_SELECTORS) as HTMLAnchorElement | null)?.getAttribute("href") ?? null),
      text: firstText(item, COMMENT_TEXT_SELECTORS),
      created_at: item.querySelector("time[datetime]")?.getAttribute("datetime") ?? null,
      reactions: countFrom(item, REACTION_SELECTORS),
    }))
    .filter((comment) => comment.text || comment.author_name);
}

export function extractPostFromElement(
  el: Element,
  source: CaptureSource,
  keyword?: string | null,
): CapturedPostPayload | null {
  const isNewPost = el.matches(NEW_POST_SELECTOR);
  const isOldPost = el.matches(OLD_POST_SELECTOR);
  if (!isNewPost && !isOldPost) return null;

  const urn = el.getAttribute("data-urn");
  const authorLink = extractAuthorLink(el);
  const authorName = extractAuthorName(el);
  const text = firstText(el, TEXT_SELECTORS);
  if (!text && !authorName) return null;

  const permalink = pick(el, PERMALINK_SELECTORS) as HTMLAnchorElement | null;
  const url =
    absoluteUrl(permalink?.getAttribute("href") ?? null) ||
    (urn ? `https://www.linkedin.com/feed/update/${urn}/` : null);

  return {
    urn,
    url,
    author_name: authorName,
    author_url: absoluteUrl(authorLink?.getAttribute("href") ?? null),
    author_headline: firstText(el, HEADLINE_SELECTORS) || null,
    text,
    posted_at: el.querySelector("time[datetime]")?.getAttribute("datetime") ?? null,
    reactions: countFrom(el, REACTION_SELECTORS),
    comments_count: countFrom(el, COMMENT_COUNT_SELECTORS),
    reposts: countFrom(el, REPOST_SELECTORS),
    media: Array.from(el.querySelectorAll("img"))
      .map((img) => img as HTMLImageElement)
      .filter(
        (image) =>
          image.src &&
          !(image.alt || "").startsWith("View ") &&
          !image.src.includes("profile-displayphoto"),
      )
      .slice(0, 4)
      .map((image) => ({ type: "image", url: image.src })),
    source,
    keyword: keyword ?? null,
    raw_html: el.outerHTML.slice(0, 200_000),
    comments: extractComments(el),
  };
}

export function extractPostsFromDocument(
  doc: Document,
  source: CaptureSource,
  keyword?: string | null,
): CapturedPostPayload[] {
  const nodes = Array.from(doc.querySelectorAll(POST_SELECTORS.join(",")));
  const seen = new Set<string>();
  const posts: CapturedPostPayload[] = [];
  for (const node of nodes) {
    const payload = extractPostFromElement(node, source, keyword);
    if (!payload) continue;
    const key =
      payload.urn ||
      normalizeUrl(payload.url) ||
      `${payload.author_name}|${payload.text.slice(0, 120)}`;
    if (seen.has(key)) continue;
    seen.add(key);
    posts.push(payload);
  }
  return posts;
}

export function detectPageType(url: string): CaptureSource {
  if (url.includes("/search/results/content")) return "search";
  if (url.includes("/feed/hashtag")) return "hashtag";
  if (url.includes("/analytics")) return "analytics";
  if (url.includes("/recent-activity")) return "profile";
  return "feed";
}

export function isSecurityChallenge(doc: Document): boolean {
  const haystack = `${doc.title}\n${doc.body?.innerText ?? doc.body?.textContent ?? ""}`.toLowerCase();
  return [
    "security verification",
    "unusual activity",
    "验证",
    "异常活动",
    "captcha",
    "checkpoint",
  ].some((phrase) => haystack.includes(phrase));
}
