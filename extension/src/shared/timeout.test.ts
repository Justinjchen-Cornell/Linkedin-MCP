import { expect, it } from "vitest";
import { withTimeout } from "./timeout";

it("resolves a fast promise", async () => {
  await expect(withTimeout(Promise.resolve(1), 50)).resolves.toBe(1);
});

it("rejects a slow promise", async () => {
  await expect(withTimeout(new Promise(() => undefined), 10, "slow")).rejects.toThrow("slow");
});
