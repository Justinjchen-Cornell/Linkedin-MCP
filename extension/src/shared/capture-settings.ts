export function captureLimits(values: Record<string, string | undefined>): {
  scrollScreens: number;
  maxPosts: number;
} {
  const rawScreens = values.capture_scroll_screens;
  const rawMax = values.max_posts_per_capture;
  const screens = Number(rawScreens);
  const max = Number(rawMax);
  return {
    scrollScreens:
      rawScreens && rawScreens.trim() !== "" && Number.isFinite(screens)
        ? Math.min(Math.max(Math.trunc(screens), 0), 3)
        : 3,
    maxPosts:
      rawMax && rawMax.trim() !== "" && Number.isFinite(max)
        ? Math.min(Math.max(Math.trunc(max), 1), 100)
        : 100,
  };
}
