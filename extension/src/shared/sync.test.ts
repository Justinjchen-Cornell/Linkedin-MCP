import { expect, it } from "vitest";
import { buildSyncQueue } from "./sync";

it("builds a deduped queue capped at five", () => {
  const posts = [
    { urn: "urn:1" }, { urn: null }, { urn: "urn:1" },
    { urn: "urn:2" }, { urn: "urn:3" }, { urn: "urn:4" }, { urn: "urn:5" }, { urn: "urn:6" },
  ];
  expect(buildSyncQueue(posts)).toEqual(["urn:1", "urn:2", "urn:3", "urn:4", "urn:5"]);
});
