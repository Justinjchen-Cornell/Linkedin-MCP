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
  const pattern = new RegExp("([0-9,.]+%?)\s*\n?\s*" + label, "i");
  const match = text.match(pattern);
  return match ? parseMetricNumber(match[1]) : null;
}

export function extractPostMetrics(doc: Document, url: string): PostMetricsPayload {
  const text = doc.body?.innerText || doc.body?.textContent || "";
  return {
    urn: url.match(/urn:li:activity:[0-9]+/)?.[0] ?? null,
    impressions: metricBeforeLabel(text, "Impressions"),
    members_reached: metricBeforeLabel(text, "Members reached"),
    in_network_pct: metricBeforeLabel(text, "In-network"),
    out_network_pct: metricBeforeLabel(text, "Out-of-network"),
    profile_viewers: metricBeforeLabel(text, "Profile viewers from this post"),
    followers_gained: metricBeforeLabel(text, "Followers gained from this post"),
    social_engagements: metricBeforeLabel(text, "Social engagements"),
    reactions: metricBeforeLabel(text, "Reactions"),
    comments: metricBeforeLabel(text, "Comments"),
    reposts: metricBeforeLabel(text, "Reposts"),
    saves: metricBeforeLabel(text, "Saves"),
    sends: metricBeforeLabel(text, "Sends on LinkedIn"),
    raw_text: text.slice(0, 20_000),
  };
}
