import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { describe, expect, it } from "vitest";
import { extractAccountSnapshot, hasProfileMetrics, hasProfilePosts, parseMetricNumber } from "./analytics";

function doc(file: string) {
  return new JSDOM(readFileSync(`tests/fixtures/${file}`, "utf8")).window.document;
}

describe("analytics", () => {
  it("parses account snapshot", () => {
    const s = extractAccountSnapshot(doc("profile_analytics.html"));
    expect(s).toMatchObject({
      followers: 1773, connections: 500, profile_views: 965,
      post_impressions_7d: 1512, search_appearances_7d: 103,
    });
  });

  it("detects profile metrics readiness", () => {
    expect(hasProfileMetrics("1,773 followers")).toBe(true);
    expect(hasProfileMetrics("965 profile views")).toBe(true);
    expect(hasProfileMetrics("Loading...")).toBe(false);
  });

  it("detects profile posts readiness", () => {
    expect(hasProfilePosts(doc("feed_new.html"))).toBe(true);
    expect(hasProfilePosts(doc("profile_analytics.html"))).toBe(false);
  });

  it("parses metric numbers", () => {
    expect(parseMetricNumber("1,773")).toBe(1773);
    expect(parseMetricNumber("500+")).toBe(500);
    expect(parseMetricNumber("1.2K")).toBe(1200);
    expect(parseMetricNumber("abc")).toBeNull();
    expect(parseMetricNumber(null)).toBeNull();
  });
});
