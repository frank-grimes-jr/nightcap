import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, mkdir, writeFile, readFile, rm } from "node:fs/promises";
import os from "node:os";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { publishDraft } from "../api/git.mjs";
const exec = promisify(execFile);
const git = async (cwd, ...args) =>
  (await exec("git", args, { cwd })).stdout.trim();
test("publishes only the selected content without disturbing a dirty, staged checkout", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "npc-git-"));
  t.after(() => rm(root, { recursive: true, force: true }));
  const repo = path.join(root, "source"),
    remote = path.join(root, "remote.git");
  await mkdir(repo);
  await git(root, "init", "--bare", remote);
  await git(repo, "init", "-b", "main");
  await git(repo, "config", "user.name", "NPC Admin Test");
  await git(repo, "config", "user.email", "npc-admin-test@example.invalid");
  await writeFile(path.join(repo, "existing.txt"), "original");
  await git(repo, "add", "existing.txt");
  await git(repo, "commit", "-m", "Initial");
  await git(repo, "remote", "add", "origin", remote);
  await git(repo, "push", "origin", "main");
  await writeFile(path.join(repo, "existing.txt"), "private staged work");
  await git(repo, "add", "existing.txt");
  await writeFile(path.join(repo, "untracked.txt"), "do not publish");
  const before = await git(repo, "status", "--porcelain");
  const draft = {
    format: 1,
    id: "459e7f8b-3144-4976-bb5b-18aad387af04",
    title: "Move guard",
    revision: 1,
    source: "local",
    changes: [
      {
        table: "spawn2",
        key: { id: 42 },
        before: { id: 42, x: 1 },
        after: { id: 42, x: 2 },
      },
    ],
  };
  const result = await publishDraft(
    { repository: repo, gitRemote: "origin", gitBase: "main" },
    path.join(root, "work"),
    draft,
  );
  assert.match(result.branch, /^feature\/npc-change-/);
  assert.equal(await git(repo, "status", "--porcelain"), before);
  assert.equal(await git(repo, "branch", "--show-current"), "main");
  assert.equal(
    await readFile(path.join(repo, "existing.txt"), "utf8"),
    "private staged work",
  );
  assert.equal(
    await git(remote, "show", `${result.branch}:existing.txt`),
    "original",
  );
  assert.match(
    await git(
      remote,
      "show",
      `${result.branch}:${result.directory}/change-set.json`,
    ),
    /Move guard/,
  );
  assert.equal(
    (
      await publishDraft(
        { repository: repo, gitRemote: "origin", gitBase: "main" },
        path.join(root, "work"),
        draft,
      )
    ).commit,
    result.commit,
  );
  const checkout = path.join(root, "work", `${draft.id}-r${draft.revision}`);
  await writeFile(path.join(checkout, "unrelated.txt"), "never publish this");
  await git(checkout, "add", "unrelated.txt");
  await git(checkout, "commit", "-m", "Unselected content");
  await assert.rejects(
    publishDraft({ repository: repo }, path.join(root, "work"), draft),
    /Publication.*(commit|content|tree)/,
  );
  assert.equal(await git(remote, "rev-parse", result.branch), result.commit);
  const second = { ...draft, id: "bc6dca6d-6ab6-4fb8-8a79-316858d10128" };
  const hooks = path.join(root, "failing-hooks");
  await mkdir(hooks);
  await writeFile(path.join(hooks, "pre-commit"), "#!/bin/sh\nexit 1\n", {
    mode: 0o755,
  });
  await git(repo, "config", "core.hooksPath", hooks);
  await assert.rejects(
    publishDraft({ repository: repo }, path.join(root, "work"), second),
    /Git commit failed/,
  );
  await git(repo, "config", "--unset", "core.hooksPath");
  await git(repo, "config", "diff.ignoreSubmodules", "all");
  const partial = path.join(root, "work", `${second.id}-r${second.revision}`);
  const base = await git(repo, "rev-parse", "main");
  await git(
    partial,
    "update-index",
    "--add",
    "--cacheinfo",
    `160000,${base},dep`,
  );
  await assert.rejects(
    publishDraft({ repository: repo }, path.join(root, "work"), second),
    /unrelated pending|Unexpected staged/,
  );
  await git(partial, "update-index", "--force-remove", "dep");
  const resumed = await publishDraft(
    { repository: repo },
    path.join(root, "work"),
    second,
  );
  assert.equal(await git(remote, "rev-parse", resumed.branch), resumed.commit);
  assert.equal(await git(repo, "status", "--porcelain"), before);
});
