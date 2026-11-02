export type CaptureSource = "feed" | "search" | "hashtag" | "profile" | "analytics";

export interface CapturedCommentPayload {
  author_name: string;
  author_url: string | null;
  text: string;
  created_at: string | null;
  reactions: number;
}

export interface CapturedPostPayload {
  urn: string | null;
  url: string | null;
  author_name: string;
  author_url: string | null;
  author_headline: string | null;
  text: string;
  posted_at: string | null;
  reactions: number;
  comments_count: number;
  reposts: number;
  media: Array<{ type: string; url: string }>;
  source: CaptureSource;
  keyword: string | null;
  raw_html: string;
  comments: CapturedCommentPayload[];
}

export interface PollResponse {
  tasks: unknown[];
  server_time: string;
}

export interface WatchlistTask {
  id: number;
  kind: string;
  value: string;
  url: string;
}
