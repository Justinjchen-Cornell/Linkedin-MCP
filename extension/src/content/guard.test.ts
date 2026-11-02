import { expect, it } from "vitest";
import { shouldInject } from "./guard";

it("only injects once", () => {
  const win = {} as Window;
  expect(shouldInject(win)).toBe(true);
  win.__linkedinWorkbenchInjected = true;
  expect(shouldInject(win)).toBe(false);
});
