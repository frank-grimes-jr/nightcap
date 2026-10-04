import express from "express";
import path from "node:path";
import { readdir } from "node:fs/promises";
import {
  assert,
  tables,
  makeChange,
  changeIdentity,
  equalRows,
  validKey,
  sqlPreview,
  parseLocation,
  UserError,
} from "./domain.mjs";
import {
  createPool,
  rows,
  searchNpcs,
  zones,
  items,
  npcDetails,
  readRecord,
  insertDefaults,
  impact,
  requireTransactional,
} from "./database.mjs";
import { DraftStore, atomicJson } from "./store.mjs";
import {
  assess,
  deploy,
  portableDraft,
  validateDraft,
  rollbackDraft,
} from "./changes.mjs";
import { publishDraft } from "./git.mjs";

const summary = (receipt) => ({
  id: receipt.id,
  draftId: receipt.draftId,
  title: receipt.draft?.title,
  revision: receipt.revision,
  target: receipt.target,
  direction: receipt.direction,
  status: receipt.status,
  startedAt: receipt.startedAt,
  finishedAt: receipt.finishedAt,
  activation: receipt.activation,
  message: receipt.message,
});
const previewSummary = (plan) => ({
  ...plan,
  states: plan.states.map((s) => ({
    id: s.id,
    npc_id: s.npc_id,
    zone_id: s.zone_id,
    instance_id: s.instance_id,
    spawn2_id: s.spawn2_id,
  })),
});
function textQuery(value = "", max = 100) {
  assert(
    typeof value === "string" && value.length <= max,
    "Invalid search text",
  );
  return value;
}
function numericId(value) {
  assert(
    /^\d+$/.test(value) &&
      Number.isSafeInteger(Number(value)) &&
      Number(value) > 0 &&
      Number(value) <= 2147483647,
    "Invalid numeric ID",
  );
  return Number(value);
}

export function createApp(config, localRoot) {
  const app = express();
  const drafts = new DraftStore(path.join(localRoot, "drafts"));
  const receipts = new DraftStore(path.join(localRoot, "receipts"));
  const pools = new Map();
  const previews = new Map();
  let actionQueue = Promise.resolve();
  const exclusive = (work) => {
    const next = actionQueue.then(work, work);
    actionQueue = next.catch(() => {});
    return next;
  };
  function target(id) {
    const found = config.targets.find((t) => t.id === id);
    assert(found, "Target profile not found", 404);
    return found;
  }
  function pool(id) {
    const t = target(id);
    if (!pools.has(id)) pools.set(id, createPool(t));
    return pools.get(id);
  }
  const route = (fn) => (req, res, next) =>
    Promise.resolve()
      .then(() => fn(req, res))
      .catch(next);
  const mutating = (fn) => route((req, res) => exclusive(() => fn(req, res)));
  const getDraft = async (req) => {
    const draft = await drafts.get(req.params.id);
    assert(
      req.body.revision === draft.revision,
      "Draft changed. Reload before continuing.",
      409,
    );
    return draft;
  };
  function rememberPreview(key, plan) {
    previews.set(key, { hash: plan.hash, expires: Date.now() + 10 * 60000 });
    for (const [k, v] of previews)
      if (v.expires < Date.now()) previews.delete(k);
    return previewSummary(plan);
  }
  function checkPreview(key, hash) {
    const preview = previews.get(key);
    assert(
      preview && preview.expires > Date.now() && preview.hash === hash,
      "Preview is missing or expired. Review a fresh preview.",
      409,
    );
  }

  app.disable("x-powered-by");
  app.use((req, res, next) => {
    const port = req.socket.localPort;
    const hosts = [`127.0.0.1:${port}`, `localhost:${port}`];
    if (
      !hosts.includes(req.headers.host) ||
      (req.headers.origin &&
        req.headers.origin !== `http://${req.headers.host}`) ||
      req.headers["sec-fetch-site"] === "cross-site"
    )
      return res.status(403).json({ error: "Local, same-origin access only" });
    res.set({
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
      "Referrer-Policy": "no-referrer",
      "Cache-Control": "no-store",
      "Content-Security-Policy":
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self' ws://127.0.0.1:* ws://localhost:*; frame-ancestors 'none'; base-uri 'none'",
    });
    if (
      !["GET", "HEAD"].includes(req.method) &&
      (!req.is("application/json") || req.headers["x-npc-admin"] !== "1")
    )
      return res
        .status(403)
        .json({ error: "Use the NPC Admin application to submit changes" });
    next();
  });
  app.use(express.json({ limit: "3mb", strict: true }));
  app.get("/api/meta", (req, res) =>
    res.json({
      tables,
      targets: config.targets.map((t) => ({
        id: t.id,
        label: t.label,
        production: !!t.production,
      })),
      configured: config.targets.length > 0,
    }),
  );
  app.get(
    "/api/targets/:target/status",
    route(async (req, res) => {
      const [status] = await rows(
        pool(req.params.target),
        "SELECT DATABASE() AS databaseName, VERSION() AS version",
      );
      res.json({ connected: true, ...status });
    }),
  );
  app.get(
    "/api/targets/:target/zones",
    route(async (req, res) => res.json(await zones(pool(req.params.target)))),
  );
  app.get(
    "/api/targets/:target/npcs",
    route(async (req, res) => {
      target(req.params.target);
      const offset = req.query.offset ?? "0";
      assert(
        typeof offset === "string" &&
          /^\d+$/.test(offset) &&
          Number(offset) <= 1000000,
        "Invalid page offset",
      );
      res.json(
        await searchNpcs(pool(req.params.target), {
          q: textQuery(req.query.q),
          zone: textQuery(req.query.zone, 32),
          offset: Number(offset),
        }),
      );
    }),
  );
  app.get(
    "/api/targets/:target/npcs/:id",
    route(async (req, res) =>
      res.json(
        await npcDetails(pool(req.params.target), numericId(req.params.id)),
      ),
    ),
  );
  app.get(
    "/api/targets/:target/items",
    route(async (req, res) =>
      res.json(await items(pool(req.params.target), textQuery(req.query.q))),
    ),
  );
  app.get(
    "/api/targets/:target/record/:table",
    route(async (req, res) => {
      let key;
      try {
        key = JSON.parse(req.query.key);
      } catch {
        throw new UserError("Invalid record key");
      }
      validKey(req.params.table, key);
      res.json({
        row: await readRecord(pool(req.params.target), req.params.table, key),
        impact: await impact(pool(req.params.target), {
          table: req.params.table,
          key,
        }),
      });
    }),
  );
  app.post(
    "/api/parse-location",
    route((req, res) => res.json(parseLocation(req.body.text))),
  );
  app.get(
    "/api/drafts",
    route(async (req, res) =>
      res.json(
        (await drafts.list()).map((d) => ({
          id: d.id,
          title: d.title,
          source: d.source,
          revision: d.revision,
          count: d.changes.length,
        })),
      ),
    ),
  );
  app.get(
    "/api/drafts/:id",
    route(async (req, res) => res.json(await drafts.get(req.params.id))),
  );
  app.post(
    "/api/drafts",
    mutating(async (req, res) => {
      target(req.body.source);
      res.json(await drafts.create(req.body.title, req.body.source));
    }),
  );
  app.post(
    "/api/import",
    mutating(async (req, res) => {
      target(req.body.source);
      const imported = validateDraft(req.body.draft);
      const draft = await drafts.create(imported.title, req.body.source);
      res.json(
        await drafts.save(
          { ...draft, changes: imported.changes },
          draft.revision,
        ),
      );
    }),
  );
  app.post(
    "/api/drafts/:id/changes",
    mutating(async (req, res) => {
      const draft = await getDraft(req);
      const { table, key, patch, mode = "update", expected } = req.body;
      const identity = changeIdentity({ table, key });
      const current = draft.changes.find((c) => changeIdentity(c) === identity);
      assert(
        current || draft.changes.length < 200,
        "This draft has reached its 200-record limit",
      );
      assert(
        !current ||
          (current.before !== null &&
            current.after !== null &&
            mode === "update"),
        "Remove the staged operation before replacing its action",
      );
      const actual =
        current?.after ?? (await readRecord(pool(draft.source), table, key));
      assert(
        equalRows(actual, expected),
        "The record changed since you opened it. Reopen the editor.",
        409,
      );
      let change = makeChange(table, key, actual, patch, mode);
      if (mode === "insert")
        change.after = await insertDefaults(
          pool(draft.source),
          table,
          change.after,
        );
      if (current) change.before = current.before;
      const changes = draft.changes.filter(
        (c) => changeIdentity(c) !== identity,
      );
      if (!equalRows(change.before, change.after)) changes.push(change);
      const next = { ...draft, changes };
      validateDraft(next);
      res.json(await drafts.save(next, draft.revision));
    }),
  );
  app.post(
    "/api/drafts/:id/remove-change",
    mutating(async (req, res) => {
      const draft = await getDraft(req);
      const identity = changeIdentity(req.body);
      res.json(
        await drafts.save(
          {
            ...draft,
            changes: draft.changes.filter(
              (c) => changeIdentity(c) !== identity,
            ),
          },
          draft.revision,
        ),
      );
    }),
  );
  app.get(
    "/api/drafts/:id/export",
    route(async (req, res) => {
      const draft = await drafts.get(req.params.id);
      res
        .set(
          "Content-Disposition",
          `attachment; filename="npc-change-${draft.id}.json"`,
        )
        .json(portableDraft(draft));
    }),
  );
  app.get(
    "/api/drafts/:id/sql",
    route(async (req, res) =>
      res
        .type("text/plain")
        .send(sqlPreview((await drafts.get(req.params.id)).changes)),
    ),
  );
  app.post(
    "/api/drafts/:id/preview",
    mutating(async (req, res) => {
      const draft = await getDraft(req);
      const plan = await assess(pool(req.body.target), draft, req.body.target);
      res.json(rememberPreview(`draft:${draft.id}:${req.body.target}`, plan));
    }),
  );
  app.post(
    "/api/drafts/:id/apply",
    mutating(async (req, res) => {
      const draft = await getDraft(req),
        selected = target(req.body.target);
      assert(
        req.body.confirmTarget === selected.label,
        "Type the exact target name before applying",
      );
      checkPreview(`draft:${draft.id}:${selected.id}`, req.body.previewHash);
      const receipt = await deploy({
        pool: pool(selected.id),
        draft,
        targetId: selected.id,
        previewHash: req.body.previewHash,
        maintenanceConfirmed: req.body.maintenanceConfirmed,
        backupRoot: receipts.root,
      });
      previews.delete(`draft:${draft.id}:${selected.id}`);
      res.json(summary(receipt));
    }),
  );
  app.post(
    "/api/drafts/:id/publish",
    mutating(async (req, res) =>
      res.json(
        await publishDraft(
          config,
          path.join(localRoot, "git-worktrees"),
          await getDraft(req),
        ),
      ),
    ),
  );
  app.get(
    "/api/receipts",
    route(async (req, res) => {
      const all = await receipts.list();
      res.json(all.map(summary));
    }),
  );
  app.post(
    "/api/receipts/:id/recover",
    mutating(async (req, res) => {
      const receipt = await receipts.get(req.params.id);
      assert(
        ["prepared", "uncertain"].includes(receipt.status),
        "This receipt does not need recovery",
      );
      const db = await pool(receipt.target).getConnection();
      let ledger;
      try {
        const [{ acquired }] = await rows(
          db,
          "SELECT GET_LOCK(CONCAT('npc-admin:', DATABASE()), 0) AS acquired",
        );
        assert(
          Number(acquired) === 1,
          "A deployment is still running. Recover after it finishes.",
          409,
        );
        await requireTransactional(db, "npc_admin_deployments");
        ledger = await rows(
          db,
          "SELECT payload_hash FROM npc_admin_deployments WHERE id = ?",
          [receipt.id],
        );
      } finally {
        await db
          .query("SELECT RELEASE_LOCK(CONCAT('npc-admin:', DATABASE()))")
          .catch(() => {});
        db.release();
      }
      assert(
        ledger.length === 0 || ledger[0].payload_hash === receipt.payloadHash,
        "Receipt ledger does not match local evidence",
        409,
      );
      receipt.status = ledger.length ? "applied" : "failed";
      receipt.message = ledger.length
        ? "Committed deployment recovered from database ledger."
        : "Database ledger confirms this attempt was not committed.";
      await atomicJson(receipts.file(receipt.id), receipt);
      res.json(summary(receipt));
    }),
  );
  app.post(
    "/api/receipts/:id/preview-rollback",
    mutating(async (req, res) => {
      const receipt = await receipts.get(req.params.id);
      const plan = await assess(
        pool(receipt.target),
        rollbackDraft(receipt),
        receipt.target,
        false,
        { restore: true },
      );
      res.json(rememberPreview(`rollback:${receipt.id}`, plan));
    }),
  );
  app.post(
    "/api/receipts/:id/rollback",
    mutating(async (req, res) => {
      const receipt = await receipts.get(req.params.id),
        selected = target(receipt.target);
      assert(
        req.body.confirmTarget === selected.label,
        "Type the exact target name before rolling back",
      );
      checkPreview(`rollback:${receipt.id}`, req.body.previewHash);
      const reverted = await deploy({
        pool: pool(selected.id),
        draft: rollbackDraft(receipt),
        targetId: selected.id,
        previewHash: req.body.previewHash,
        maintenanceConfirmed: req.body.maintenanceConfirmed,
        backupRoot: receipts.root,
        direction: "rollback",
        priorReceipt: receipt,
      });
      previews.delete(`rollback:${receipt.id}`);
      res.json(summary(reverted));
    }),
  );
  app.use("/api", (req, res) =>
    res.status(404).json({ error: "API route not found" }),
  );
  app.use((error, req, res, next) => {
    if (res.headersSent) return next(error);
    const status = error.status ?? 500;
    const message =
      error instanceof UserError
        ? error.message
        : error.type === "entity.parse.failed"
          ? "Invalid JSON"
          : "Operation failed. Check the target connection, schema and local configuration. No success was confirmed.";
    console.error(
      `[npc-admin] ${req.method} ${req.path}: ${error.code ?? error.name}`,
    );
    res.status(status).json({ error: message });
  });
  return {
    app,
    close: () => Promise.all([...pools.values()].map((p) => p.end())),
  };
}
