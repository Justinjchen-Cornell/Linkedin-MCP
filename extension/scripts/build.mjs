import { build } from "esbuild";
import { cp, mkdir, rm } from "node:fs/promises";

await rm("dist", { recursive: true, force: true });
await mkdir("dist/content", { recursive: true });
await mkdir("dist/popup", { recursive: true });

const common = {
  bundle: true,
  format: "iife",
  platform: "browser",
  target: "chrome120",
  logLevel: "info",
};

await build({ ...common, entryPoints: ["src/background.ts"], outfile: "dist/background.js" });
await build({ ...common, entryPoints: ["src/content/main.ts"], outfile: "dist/content/main.js" });
await build({ ...common, entryPoints: ["src/popup/main.ts"], outfile: "dist/popup/main.js" });
await cp("manifest.json", "dist/manifest.json");
await cp("src/popup/index.html", "dist/popup/index.html");
