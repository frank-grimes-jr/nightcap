import { open, realpath } from "node:fs/promises";
import path from "node:path";
import { assert } from "./domain.mjs";

const MAX_BYTES = 8 * 1024 * 1024,
  MAX_LINES = 120000,
  MAX_LABELS = 5000;
const validName = (value) =>
  typeof value === "string" && /^[a-z0-9_]{1,64}$/.test(value);
const coordinate = (value) =>
  Number.isFinite(value) && Math.abs(value) <= 10000000;

export function parseMap(text, layer = 0) {
  const lines = [],
    labels = [];
  let invalid = 0;
  for (const raw of text.split(/\r?\n/)) {
    const record = raw.trim();
    if (!/^[LP]\s/.test(record)) continue;
    const fields = record
      .slice(1)
      .trim()
      .split(",")
      .map((s) => s.trim());
    const count = record[0] === "L" ? 9 : 7;
    const numbers = fields
      .slice(0, count)
      .map((s) => (s === "" ? NaN : Number(s)));
    if (
      fields.length < (record[0] === "L" ? 9 : 8) ||
      numbers.length !== count ||
      !numbers.every(coordinate)
    ) {
      invalid++;
      continue;
    }
    if (record[0] === "L") lines.push([...numbers.slice(0, 6), layer]);
    else
      labels.push({
        x: numbers[0],
        y: numbers[1],
        z: numbers[2],
        layer,
        text: fields
          .slice(7)
          .join(",")
          .replaceAll("_", " ")
          .replace(/[\x00-\x1f\x7f]/g, "")
          .slice(0, 160),
      });
    assert(
      lines.length <= MAX_LINES && labels.length <= MAX_LABELS,
      "Map contains too many records",
    );
  }
  return { lines, labels, invalid };
}

export class MapStore {
  constructor(directory) {
    this.directory = directory;
    this.cache = new Map();
  }
  async get(zone, version = 0, aliases = {}) {
    assert(validName(zone), "Invalid map zone");
    assert(
      Number.isInteger(version) && version >= -1 && version <= 32767,
      "Invalid zone version",
    );
    assert(
      aliases && typeof aliases === "object" && !Array.isArray(aliases),
      "Invalid map aliases",
    );
    const name = Object.hasOwn(aliases, `${zone}:${version}`)
      ? aliases[`${zone}:${version}`]
      : zone;
    assert(validName(name), "Invalid map alias");
    const empty = (reason) => ({
      available: false,
      zone,
      version,
      name,
      reason,
      files: [],
      lines: [],
      labels: [],
      invalid: 0,
    });
    if (!this.directory)
      return empty(
        "No client map folder is configured. See the map setup in README.",
      );
    let root;
    try {
      root = await realpath(this.directory);
    } catch (e) {
      if (e.code === "ENOENT")
        return empty("The configured client map folder is unavailable.");
      throw e;
    }
    const handles = [];
    try {
      let total = 0;
      for (let layer = 0; layer < 4; layer++) {
        const file = `${name}${layer ? `_${layer}` : ""}.txt`;
        let resolved;
        try {
          resolved = await realpath(path.join(root, file));
        } catch (e) {
          if (e.code === "ENOENT") continue;
          throw e;
        }
        const relative = path.relative(root, resolved);
        assert(
          relative &&
            !relative.startsWith(`..${path.sep}`) &&
            relative !== ".." &&
            !path.isAbsolute(relative),
          "Map file is outside the configured folder",
        );
        const handle = await open(resolved, "r");
        handles.push({ handle, file, layer });
        const stat = await handle.stat();
        assert(stat.isFile(), "Map source must be a regular file");
        total += stat.size;
        assert(total <= MAX_BYTES, "Map files exceed the 8 MB limit");
        handles.at(-1).size = stat.size;
        handles.at(-1).stamp =
          `${file}:${stat.size}:${stat.mtimeMs}:${stat.ctimeMs}`;
      }
      if (!handles.length) return empty(`No client map found for ${name}.`);
      const signature = handles.map((f) => f.stamp).join("|");
      const cached = this.cache.get(name);
      if (cached?.signature === signature)
        return { ...cached.data, zone, version };
      const data = {
        available: true,
        name,
        files: [],
        lines: [],
        labels: [],
        invalid: 0,
      };
      for (const f of handles) {
        // Bounded reads also protect against files growing after stat().
        const bytes = Buffer.alloc(f.size + 1);
        let used = 0,
          read;
        while (
          used < bytes.length &&
          (read = await f.handle.read(bytes, used, bytes.length - used, null))
            .bytesRead
        )
          used += read.bytesRead;
        assert(
          used === f.size,
          "Map file changed while reading. Retry the map.",
        );
        const parsed = parseMap(
          bytes.subarray(0, used).toString("utf8"),
          f.layer,
        );
        data.files.push(f.file);
        data.lines = data.lines.concat(parsed.lines);
        data.labels = data.labels.concat(parsed.labels);
        data.invalid += parsed.invalid;
        assert(
          data.lines.length <= MAX_LINES && data.labels.length <= MAX_LABELS,
          "Map contains too many records",
        );
      }
      if (!data.lines.length)
        return empty(`No usable map outlines found for ${name}.`);
      this.cache.delete(name);
      this.cache.set(name, { signature, data });
      while (this.cache.size > 4)
        this.cache.delete(this.cache.keys().next().value);
      return { ...data, zone, version };
    } finally {
      await Promise.all(handles.map((f) => f.handle.close()));
    }
  }
}
