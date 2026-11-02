import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";
import { extractPostsFromDocument, parseCount, detectPageType, isSecurityChallenge } from "./extract";

function doc(file: string) {
  return new JSDOM(readFileSync(`tests/fixtures/${file}`, "utf8")).window.document;
}

describe("extract", () => {
  it("parses English feed posts", () => {
    const posts = extractPostsFromDocument(doc("feed_en.html"), "feed");
    expect(posts).toHaveLength(2);
    expect(posts[0]).toMatchObject({
      urn: "urn:li:activity:111",
      author_name: "Alice Chen",
      author_headline: "Founder at Acme",
      reactions: 1234,
      comments_count: 12,
      reposts: 3,
    });
    expect(posts[0].text).toContain("AI content ops");
  });

  it("parses Chinese feed post", () => {
    const posts = extractPostsFromDocument(doc("feed_zh.html"), "feed");
    expect(posts[0].author_name).toBe("陈嘉");
    expect(posts[0].text).toContain("内容运营");
  });

  it("parses search results", () => {
    const posts = extractPostsFromDocument(doc("search_en.html"), "search", "SaaS");
    expect(posts).toHaveLength(1);
    expect(posts[0].source).toBe("search");
    expect(posts[0].keyword).toBe("SaaS");
  });

  it("parses counts", () => {
    expect(parseCount("1,234 reactions")).toBe(1234);
    expect(parseCount("2.3K")).toBe(2300);
    expect(parseCount("1.1M")).toBe(1100000);
    expect(parseCount(null)).toBe(0);
  });

  it("detects page types", () => {
    expect(detectPageType("https://www.linkedin.com/feed/")).toBe("feed");
    expect(detectPageType("https://www.linkedin.com/search/results/content/?keywords=x")).toBe("search");
    expect(detectPageType("https://www.linkedin.com/feed/hashtag/?keywords=x")).toBe("hashtag");
    expect(detectPageType("https://www.linkedin.com/in/alice/recent-activity/all/")).toBe("profile");
  });

  it("detects security challenges", () => {
    const d = new JSDOM("<title>Security Verification</title><body>unusual activity</body>").window.document;
    expect(isSecurityChallenge(d)).toBe(true);
    expect(isSecurityChallenge(doc("feed_en.html"))).toBe(false);
  });
});
