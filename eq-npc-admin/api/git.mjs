import { execFile } from "node:child_process";
import { promisify } from "node:util";
import { mkdir, readFile, writeFile, stat } from "node:fs/promises";
import path from "node:path";
import { assert, sqlPreview, reverseChange, UserError } from "./domain.mjs";
import {
  validateDraft,
  portableDraft,
  activationSteps,
  digest,
} from "./changes.mjs";
import { atomicJson } from "./store.mjs";

const exec = promisify(execFile);
async function git(cwd, args) {
  try {
    return (
      await exec("git", args, {
        cwd,
        windowsHide: true,
        timeout: 60000,
        maxBuffer: 2 * 1024 * 1024,
        env: { ...process.env, GIT_TERMINAL_PROMPT: "0" },
      })
    ).stdout.trim();
  } catch (error) {
    // Never return stderr: it can contain credential-bearing remote URLs.
    const safe = new UserError(
      `Git ${args[0]} failed. Check repository permissions, Git identity and remote authentication locally. Retry after fixing the cause.`,
      409,
    );
    safe.code = error.code;
    throw safe;
  }
}
const readOptional = (filename) =>
  readFile(filename, "utf8").catch((error) => {
    if (error.code === "ENOENT") return null;
    throw error;
  });
const lines = (text) => (text ? text.split("\n") : []);

export async function publishDraft(config, workRoot, draft) {
  validateDraft(draft);
  assert(draft.changes.length > 0, "Stage at least one edit before publishing");
  assert(/^[0-9a-f-]{36}$/.test(draft.id), "Invalid draft ID");
  const { repository, gitRemote = "origin", gitBase = "main" } = config;
  assert(
    /^[a-zA-Z0-9][a-zA-Z0-9._-]*$/.test(gitRemote),
    "Invalid configured Git remote",
  );
  assert(
    /^[a-zA-Z0-9][a-zA-Z0-9/_.-]*$/.test(gitBase) && !gitBase.includes(".."),
    "Invalid configured Git base",
  );
  const name = `${draft.id}-r${draft.revision}`;
  const branch = `feature/npc-change-${name}`;
  const checkout = path.join(workRoot, name);
  const manifestFile = path.join(workRoot, `${name}.json`);
  const directory = `content/npc-changes/${draft.id}/r${draft.revision}`;
  const document = portableDraft(draft);
  const files = {
    "change-set.json": JSON.stringify(document, null, 2) + "\n",
    "forward.review.sql": sqlPreview(draft.changes),
    "rollback.review.sql": sqlPreview(
      [...draft.changes].reverse().map(reverseChange),
    ),
    "README.md": `# NPC content change\n\n${draft.title}\n\nRevision ${draft.revision}. Source profile: ${draft.source}.\n\n## Apply\n\nImport change-set.json into NPC Admin, select the target, and review the current preflight. SQL files are for review only. Git publication does not apply this change to any server.\n\n## Activation and QA\n\n${activationSteps(
      draft.changes,
    )
      .map((s) => `- ${s}`)
      .join(
        "\n",
      )}\n\nInspect each changed NPC in every affected zone and version. Verify placement, heading, pathing, combat, merchant stock or loot as applicable. Record results before promoting gameplay to main.\n`,
  };
  const allowed = Object.keys(files)
    .map((f) => `${directory}/${f}`)
    .sort();
  let manifest = JSON.parse((await readOptional(manifestFile)) ?? "null");
  if (!manifest) {
    assert(
      !(await stat(checkout).catch((e) => {
        if (e.code === "ENOENT") return null;
        throw e;
      })),
      "Publication checkout exists without its manifest. Inspect it locally.",
      409,
    );
    assert(
      !(await git(repository, ["branch", "--list", branch])),
      "Publication branch already exists without its manifest. Inspect it locally.",
      409,
    );
    const base = await git(repository, [
      "rev-parse",
      "--verify",
      `${gitBase}^{commit}`,
    ]);
    assert(
      /^[0-9a-f]{40,64}$/.test(base),
      "Git base did not resolve to a commit",
    );
    manifest = {
      base,
      branch,
      repository: path.resolve(repository),
      remote: gitRemote,
      payload: digest(document),
      files: digest(files),
      commit: null,
    };
    await atomicJson(manifestFile, manifest);
  }
  assert(
    manifest.payload === digest(document) && manifest.files === digest(files),
    "Published revision content differs. Save a new draft revision.",
    409,
  );
  assert(
    manifest.repository === path.resolve(repository) &&
      manifest.remote === gitRemote &&
      manifest.branch === branch,
    "Publication configuration changed. Inspect its retained manifest.",
    409,
  );
  if (
    !(await stat(path.join(checkout, ".git")).catch((e) => {
      if (e.code === "ENOENT") return null;
      throw e;
    }))
  ) {
    const exists = await git(repository, ["branch", "--list", branch]);
    if (exists) {
      assert(
        (await git(repository, ["rev-parse", branch])) === manifest.base,
        "Publication branch moved before checkout creation.",
        409,
      );
      await git(repository, ["worktree", "add", checkout, branch]);
    } else
      await git(repository, [
        "worktree",
        "add",
        "-b",
        branch,
        checkout,
        manifest.base,
      ]);
  }
  assert(
    (await git(checkout, ["branch", "--show-current"])) === branch,
    "Publication checkout moved to a different branch",
    409,
  );
  let head = await git(checkout, ["rev-parse", "HEAD"]);
  if (manifest.commit)
    assert(
      head === manifest.commit,
      "Publication commit changed. Unselected commits cannot be published.",
      409,
    );
  if (head === manifest.base) {
    const pending = [
      ...lines(
        await git(checkout, [
          "diff",
          "--ignore-submodules=none",
          manifest.base,
          "--name-only",
        ]),
      ),
      ...lines(
        await git(checkout, ["ls-files", "--others", "--exclude-standard"]),
      ),
    ];
    assert(
      pending.every((f) => allowed.includes(f)),
      "Publication checkout contains unrelated pending files. Inspect it locally.",
      409,
    );
    await mkdir(path.join(checkout, directory), { recursive: true });
    for (const [name, content] of Object.entries(files)) {
      const filename = path.join(checkout, directory, name),
        previous = await readOptional(filename);
      assert(
        previous === null || previous.replaceAll("\r\n", "\n") === content,
        "Publication content was edited. Inspect it locally.",
        409,
      );
      if (previous === null) await writeFile(filename, content);
    }
    await git(checkout, ["add", "--", directory]);
    assert(
      JSON.stringify(
        lines(
          await git(checkout, [
            "diff",
            "--ignore-submodules=none",
            "--cached",
            "--name-only",
          ]),
        ).sort(),
      ) === JSON.stringify(allowed),
      "Unexpected staged files in publication checkout",
      409,
    );
    await git(checkout, ["commit", "-m", `content: ${draft.title}`]);
    head = await git(checkout, ["rev-parse", "HEAD"]);
  }
  // Retry after a crash between commit and manifest persistence is safe only for
  // exactly one child of the pinned base containing these four expected files.
  assert(
    (await git(checkout, ["rev-list", "--parents", "-n", "1", head])) ===
      `${head} ${manifest.base}`,
    "Publication commit ancestry changed",
    409,
  );
  assert(
    JSON.stringify(
      lines(
        await git(checkout, [
          "diff",
          "--ignore-submodules=none",
          manifest.base,
          head,
          "--name-only",
        ]),
      ).sort(),
    ) === JSON.stringify(allowed),
    "Publication tree includes unselected content",
    409,
  );
  for (const [name, content] of Object.entries(files))
    assert(
      (await git(checkout, ["show", `${head}:${directory}/${name}`])) ===
        content.trim(),
      "Publication content differs from the selected draft",
      409,
    );
  assert(
    !(await git(checkout, ["status", "--porcelain"])),
    "Publication checkout has pending files. Inspect it before retrying.",
    409,
  );
  manifest.commit = head;
  await atomicJson(manifestFile, manifest);
  // Push the verified immutable object, never a mutable HEAD ref.
  await git(checkout, ["push", gitRemote, `${head}:refs/heads/${branch}`]);
  const remoteRef = await git(checkout, [
    "ls-remote",
    gitRemote,
    `refs/heads/${branch}`,
  ]);
  assert(
    remoteRef.split(/\s/)[0] === head,
    "Remote branch verification did not match the published commit",
    409,
  );
  return { branch, commit: head, directory };
}
