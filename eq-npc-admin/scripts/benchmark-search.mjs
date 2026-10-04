import { readFile } from "node:fs/promises";
import { createPool, searchNpcs } from "../api/database.mjs";
const config = JSON.parse(
  await readFile(new URL("../config.local.json", import.meta.url), "utf8"),
);
const pool = createPool(config.targets.find((t) => t.id === "local"));
try {
  for (let sample = 0; sample < 3; sample++) {
    const start = performance.now();
    const result = await searchNpcs(pool);
    console.log(
      JSON.stringify({
        sample,
        rows: result.length,
        milliseconds: Math.round(performance.now() - start),
      }),
    );
  }
} finally {
  await pool.end();
}
