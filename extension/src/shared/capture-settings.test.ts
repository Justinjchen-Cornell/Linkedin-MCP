import { expect, it } from "vitest";
import { captureLimits } from "./capture-settings";

it("clamps capture settings", () => {
  expect(captureLimits({})).toEqual({ scrollScreens: 3, maxPosts: 100 });
  expect(captureLimits({ capture_scroll_screens: "9", max_posts_per_capture: "500" })).toEqual({ scrollScreens: 3, maxPosts: 100 });
  expect(captureLimits({ capture_scroll_screens: "0", max_posts_per_capture: "1" })).toEqual({ scrollScreens: 0, maxPosts: 1 });
  expect(captureLimits({ capture_scroll_screens: "abc", max_posts_per_capture: "xyz" })).toEqual({ scrollScreens: 3, maxPosts: 100 });
});
