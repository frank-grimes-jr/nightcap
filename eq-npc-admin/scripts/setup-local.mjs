import { readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";

// Explicitly imports only the existing local server DB profile; never prints its secret.
const workspace = path.resolve(process.argv[2] ?? "..");
const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const source = JSON.parse(
  await readFile(
    path.join(workspace, "akk-stack/server/eqemu_config.json"),
    "utf8",
  ),
).server.database;
if (!source || !source.username || !source.db)
  throw new Error("Existing EQEmu database configuration was not found");
const config = {
  port: 3100,
  repository: "..",
  gitRemote: "origin",
  gitBase: "main",
  targets: [
    {
      id: "local",
      label: "Local Docker",
      database: {
        host: "127.0.0.1",
        port: 3307,
        user: source.username,
        password: source.password,
        database: source.db,
      },
    },
  ],
};
await writeFile(
  path.join(root, "config.local.json"),
  JSON.stringify(config, null, 2) + "\n",
  { flag: "wx", mode: 0o600 },
);
console.log(
  "Local Docker profile created in ignored config.local.json. Existing files are never overwritten.",
);
