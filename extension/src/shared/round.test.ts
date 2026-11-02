import { expect, it } from "vitest";
import { buildRoundPlan } from "./round";

it("caps a round at five tasks and drops missing urls", () => {
  const tasks = Array.from({ length: 7 }, (_, i) => ({ id: i, kind: "keyword", value: `k${i}`, url: `https://x/${i}` }));
  expect(buildRoundPlan(tasks)).toHaveLength(5);
  expect(buildRoundPlan([{ id: 1, kind: "keyword", value: "x", url: "" }])).toHaveLength(0);
});
