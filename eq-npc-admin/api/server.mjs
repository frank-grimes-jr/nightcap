import { readFile, mkdir } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import express from "express";
import { execFile } from "node:child_process";
import { createApp } from "./app.mjs";
import { assert } from "./domain.mjs";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const configPath = process.env.NPC_ADMIN_CONFIG
  ? path.resolve(process.env.NPC_ADMIN_CONFIG)
  : path.join(root, "config.local.json");
const config = await readFile(configPath, "utf8")
  .then(JSON.parse)
  .catch((e) => {
    if (e.code === "ENOENT") return { targets: [] };
    throw e;
  });
config.targets ??= [];
assert(
  Array.isArray(config.targets) &&
    config.targets.every(
      (t) =>
        /^[a-z0-9-]{1,32}$/.test(t.id) &&
        typeof t.label === "string" &&
        t.label.length <= 100,
    ) &&
    new Set(config.targets.map((t) => t.id)).size === config.targets.length,
  "Invalid target profiles",
);
config.repository = path.resolve(root, config.repository ?? "..");
if (config.mapDirectory) {
  assert(typeof config.mapDirectory === "string", "Invalid client map folder");
  config.mapDirectory = path.resolve(root, config.mapDirectory);
}
const port = Number(process.env.NPC_ADMIN_PORT ?? config.port ?? 3100);
assert(
  Number.isInteger(port) && port >= 1024 && port <= 65535,
  "Invalid local port",
);
const localRoot = path.join(root, ".local");
await mkdir(localRoot, { recursive: true });
const { app, close } = createApp(config, localRoot);
let vite;
if (process.argv.includes("--dev")) {
  const { createServer } = await import("vite");
  vite = await createServer({
    root,
    server: { middlewareMode: true },
    appType: "spa",
  });
  app.use(vite.middlewares);
} else {
  app.use(express.static(path.join(root, "dist")));
  app.get("*", (req, res) =>
    res.sendFile(path.join(root, "dist", "index.html")),
  );
}
const server = app.listen(port, "127.0.0.1", () => {
  const url = `http://127.0.0.1:${port}`;
  console.log(`NPC Admin: ${url}`);
  if (process.argv.includes("--open") && process.platform === "win32")
    execFile(
      "rundll32.exe",
      ["url.dll,FileProtocolHandler", url],
      { windowsHide: true },
      () => {},
    );
});
server.on("error", (error) => {
  console.error(`Cannot listen on local port ${port}: ${error.code}`);
  process.exitCode = 1;
});
async function shutdown() {
  server.close();
  await vite?.close();
  await close();
}
process.on("SIGINT", shutdown);
process.on("SIGTERM", shutdown);
