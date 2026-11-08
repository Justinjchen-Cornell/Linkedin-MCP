import { expect, it } from "vitest";
import { fillScheduleId } from "./autofill";

it("parses lw_fill schedule id", () => {
  expect(fillScheduleId("https://www.linkedin.com/feed/?lw_fill=12")).toBe(12);
  expect(fillScheduleId("https://www.linkedin.com/feed/")).toBeNull();
  expect(fillScheduleId("https://www.linkedin.com/feed/?lw_fill=abc")).toBeNull();
});
