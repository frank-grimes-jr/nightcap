import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import path from "node:path";
import os from "node:os";
import http from "node:http";
import { createApp } from "../api/app.mjs";

test("local API rejects cross-origin mutations, rebound hosts and secret disclosure", async (t) => {
  const root = await mkdtemp(path.join(os.tmpdir(), "npc-api-"));
  await writeFile(
    path.join(root, "poknowledge.txt"),
    "L -484,-447,-124,-480,-447,-124,0,0,0\n",
  );
  const { app, close } = createApp(
    {
      mapDirectory: root,
      targets: [
        {
          id: "test",
          label: "Test",
          database: {
            host: "127.0.0.1",
            database: "test",
            password: "never-return-this",
          },
        },
      ],
    },
    root,
  );
  const server = app.listen(0, "127.0.0.1");
  await new Promise((resolve) => server.once("listening", resolve));
  t.after(async () => {
    await new Promise((resolve) => server.close(resolve));
    await close();
    await rm(root, { recursive: true, force: true });
  });
  const url = `http://127.0.0.1:${server.address().port}`;
  const meta = await (await fetch(`${url}/api/meta`)).text();
  assert.ok(!meta.includes("never-return-this"));
  assert.ok(meta.includes("Test"));
  const map = await (
    await fetch(`${url}/api/targets/test/maps/poknowledge?version=0`)
  ).json();
  assert.equal(map.available, true);
  assert.ok(!JSON.stringify(map).includes(root));
  assert.equal(
    (await fetch(`${url}/api/targets/missing/maps/poknowledge`)).status,
    404,
  );
  assert.equal(
    (await fetch(`${url}/api/targets/test/maps/poknowledge?version=oops`))
      .status,
    400,
  );
  assert.equal(
    (await fetch(`${url}/api/targets/test/maps/bad%2Fname`)).status,
    400,
  );
  assert.equal(
    (await fetch(`${url}/api/targets/test/maps/poknowledge?version=99999`))
      .status,
    400,
  );
  const post = {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-NPC-Admin": "1" },
    body: JSON.stringify({ title: "Draft", source: "test" }),
  };
  assert.equal(
    (
      await fetch(`${url}/api/drafts`, {
        ...post,
        headers: { ...post.headers, Origin: "https://evil.example" },
      })
    ).status,
    403,
  );
  const reboundStatus = await new Promise((resolve, reject) => {
    const request = http.get(
      `${url}/api/meta`,
      { headers: { Host: "evil.example" } },
      (response) => {
        response.resume();
        resolve(response.statusCode);
      },
    );
    request.on("error", reject);
  });
  assert.equal(reboundStatus, 403);
  assert.equal(
    (
      await fetch(`${url}/api/drafts`, {
        ...post,
        headers: { "Content-Type": "application/json" },
      })
    ).status,
    403,
  );
  const created = await fetch(`${url}/api/drafts`, post);
  assert.equal(created.status, 200);
  assert.equal((await created.json()).title, "Draft");
  assert.equal((await fetch(`${url}/api/targets/missing/npcs`)).status, 404);
  assert.equal(
    (await fetch(`${url}/api/targets/test/npcs?offset=0;DROP`)).status,
    400,
  );
  const changes = Array.from({ length: 200 }, (_, i) => ({
    table: "spawn2",
    key: { id: i + 1 },
    before: { id: i + 1, x: 1 },
    after: { id: i + 1, x: 2 },
  }));
  const imported = await (
    await fetch(`${url}/api/import`, {
      ...post,
      body: JSON.stringify({
        source: "test",
        draft: { format: 1, title: "Full draft", revision: 1, changes },
      }),
    })
  ).json();
  const revised = await fetch(`${url}/api/drafts/${imported.id}/changes`, {
    ...post,
    body: JSON.stringify({
      revision: imported.revision,
      table: "spawn2",
      key: { id: 1 },
      expected: { id: 1, x: 2 },
      patch: { x: 3 },
    }),
  });
  assert.equal(revised.status, 200);
  assert.equal((await revised.json()).changes.length, 200);
});
