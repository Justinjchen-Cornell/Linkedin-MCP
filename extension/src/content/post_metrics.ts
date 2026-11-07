import { parseMetricNumber } from "./analytics";

export interface PostMetricsPayload {
  urn: string | null;
  impressions: number | null;
  members_reached: number | null;
  in_network_pct: number | null;
  out_network_pct: number | null;
  profile_viewers: number | null;
  followers_gained: number | null;
  social_engagements: number | null;
  reactions: number | null;
  comments: number | null;
  reposts: number | null;
  saves: number | null;
  sends: number | null;
  raw_text: string;
}

function metricBeforeLabel(text: string, label: string): number | null {
  const pattern = new RegExp(String.raw`([0-9,.]+%?)\s*\n?\s*` + label, "i");
  const match = text.match(pattern);
  return match ? parseMetricNumber(match[1]) : null;
}


function metricAfterLabel(text: string, label: string): number | null {
  const pattern = new RegExp(label + String.raw`[\s\S]{0,80}?([0-9,.]+%?)`, "i");
  const match = text.match(pattern);
  return match ? parseMetricNumber(match[1]) : null;
}

export function hasPostMetrics(text: string): boolean {
  return (
    /impressions|曝光/i.test(text) &&
    /members reached|触达/i.test(text) &&
    /social engagements|互动/i.test(text)
  );
}

export function extractPostMetrics(doc: Document, url: string): PostMetricsPayload {
  const text = doc.body?.innerText || doc.body?.textContent || "";
  const metricsText = text.includes("Discovery") ? text.slice(text.indexOf("Discovery")) : text;
  return {
    urn: url.match(/urn:li:activity:[0-9]+/)?.[0] ?? null,
    impressions: metricBeforeLabel(metricsText, "Impressions"),
    members_reached: metricBeforeLabel(metricsText, "Members reached"),
    in_network_pct: metricAfterLabel(metricsText, "In-network"),
    out_network_pct: metricAfterLabel(metricsText, "Out-of-network"),
    profile_viewers: metricBeforeLabel(metricsText, "Profile viewers from this post"),
    followers_gained: metricBeforeLabel(metricsText, "Followers gained from this post"),
    social_engagements: metricBeforeLabel(metricsText, "Social engagements"),
    reactions: metricAfterLabel(metricsText, "Reactions"),
    comments: metricAfterLabel(metricsText, "Comments"),
    reposts: metricAfterLabel(metricsText, "Reposts"),
    saves: metricAfterLabel(metricsText, "Saves"),
    sends: metricAfterLabel(metricsText, "Sends on LinkedIn"),
    raw_text: text.slice(0, 20_000),
  };
}
