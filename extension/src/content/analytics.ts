export interface AccountSnapshotPayload {
  followers: number | null;
  connections: number | null;
  profile_views: number | null;
  post_impressions_7d: number | null;
  search_appearances_7d: number | null;
  raw_text: string;
}

export function parseMetricNumber(value: string | null | undefined): number | null {
  if (!value) return null;
  const cleaned = value.replace(/,/g, "").replace(/\+/g, "").replace(/\s+/g, " ").trim();
  const match = cleaned.match(/([\d.]+)\s*([KM]?)/i);
  if (!match) return null;
  const number = Number.parseFloat(match[1]);
  if (!Number.isFinite(number)) return null;
  const unit = match[2].toUpperCase();
  const multiplier = unit === "K" ? 1_000 : unit === "M" ? 1_000_000 : 1;
  return Math.round(number * multiplier);
}

function metric(text: string, pattern: RegExp): number | null {
  const match = text.match(pattern);
  return match ? parseMetricNumber(match[1]) : null;
}

export function extractAccountSnapshot(doc: Document): AccountSnapshotPayload {
  const text = doc.body?.innerText || doc.body?.textContent || "";
  return {
    followers: metric(text, /([\d.,]+(?:\s*[KM])?)\s+followers/i),
    connections: metric(text, /([\d.,+]+(?:\s*[KM])?)\s+connections/i),
    profile_views: metric(text, /([\d.,]+(?:\s*[KM])?)\s+profile views/i),
    post_impressions_7d: metric(text, /([\d.,]+(?:\s*[KM])?)\s+post impressions/i),
    search_appearances_7d: metric(text, /([\d.,]+(?:\s*[KM])?)\s+search appearances/i),
    raw_text: text.slice(0, 20_000),
  };
}
