import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";
import { expect, it } from "vitest";
import { extractPostMetrics } from "./post_metrics";

it("parses post summary metrics", () => {
  const doc = new JSDOM(readFileSync("tests/fixtures/post_summary.html", "utf8")).window.document;
  const m = extractPostMetrics(doc, "https://www.linkedin.com/analytics/post-summary/urn:li:activity:7521581116454113280/");
  expect(m).toMatchObject({
    urn: "urn:li:activity:7521581116454113280",
    impressions: 665, members_reached: 184,
    in_network_pct: 72, out_network_pct: 28,
    profile_viewers: 0, followers_gained: 0,
    social_engagements: 1, reactions: 0, comments: 1,
    reposts: 0, saves: 0, sends: 0,
  });
});

it("handles blank lines between number and label", () => {
  const doc = new JSDOM(`<body><pre>Discovery

141

Impressions</pre></body>`).window.document;
  const m = extractPostMetrics(doc, "https://www.linkedin.com/analytics/post-summary/urn:li:activity:1/");
  expect(m.impressions).toBe(141);
});

it("returns null for missing metrics", () => {
  const doc = new JSDOM("<body><div>665</div><div>Impressions</div></body>").window.document;
  const m = extractPostMetrics(doc, "https://www.linkedin.com/analytics/post-summary/urn:li:activity:1/");
  expect(m.impressions).toBe(665);
  expect(m.members_reached).toBeNull();
});
