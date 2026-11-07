export function buildSyncQueue(
  posts: Array<{ urn: string | null }>,
  limit = 5,
): string[] {
  const seen = new Set<string>();
  const queue: string[] = [];
  for (const post of posts) {
    if (!post.urn || seen.has(post.urn)) continue;
    seen.add(post.urn);
    queue.push(post.urn);
    if (queue.length >= limit) break;
  }
  return queue;
}
