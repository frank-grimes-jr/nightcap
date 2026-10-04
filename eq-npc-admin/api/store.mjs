import { mkdir, readFile, writeFile, rename, readdir } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import path from "node:path";
import { assert, UserError } from "./domain.mjs";

export async function atomicJson(file, value) {
  await mkdir(path.dirname(file), { recursive: true });
  const temporary = `${file}.${randomUUID()}.tmp`;
  await writeFile(temporary, JSON.stringify(value, null, 2) + "\n", {
    mode: 0o600,
    flag: "wx",
  });
  await rename(temporary, file);
}
export class DraftStore {
  constructor(root) {
    this.root = root;
    this.queue = Promise.resolve();
  }
  file(id) {
    assert(
      /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/.test(
        id,
      ),
      "Invalid draft ID",
    );
    return path.join(this.root, `${id}.json`);
  }
  async exclusive(work) {
    const next = this.queue.then(work, work);
    this.queue = next.catch(() => {});
    return next;
  }
  async create(title, source) {
    assert(
      typeof title === "string" &&
        title.trim().length > 0 &&
        title.length <= 120 &&
        !/[\x00-\x1f]/.test(title),
      "Use a title of 1–120 characters",
    );
    const draft = {
      format: 1,
      id: randomUUID(),
      title: title.trim(),
      source,
      revision: 1,
      createdAt: new Date().toISOString(),
      changes: [],
      receipts: [],
    };
    await atomicJson(this.file(draft.id), draft);
    return draft;
  }
  async get(id) {
    try {
      return JSON.parse(await readFile(this.file(id), "utf8"));
    } catch (e) {
      if (e.code === "ENOENT") throw new UserError("Draft not found", 404);
      throw e;
    }
  }
  async save(draft, expectedRevision) {
    return this.exclusive(async () => {
      const current = await this.get(draft.id);
      assert(
        current.revision === expectedRevision,
        "Draft changed in another window. Reload before editing.",
        409,
      );
      const updated = {
        ...draft,
        revision: current.revision + 1,
        updatedAt: new Date().toISOString(),
      };
      await atomicJson(this.file(draft.id), updated);
      return updated;
    });
  }
  async list() {
    await mkdir(this.root, { recursive: true });
    const files = (await readdir(this.root)).filter((f) => f.endsWith(".json"));
    const drafts = await Promise.all(
      files.map((f) => this.get(f.slice(0, -5))),
    );
    return drafts.sort((a, b) =>
      (b.createdAt ?? b.startedAt).localeCompare(a.createdAt ?? a.startedAt),
    );
  }
}
