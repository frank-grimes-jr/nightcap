# Nightcap — Next Steps / Backlog

Living task list. Most urgent first. Updated 2026-07-28.

Branch flow: `feature/*` → `dev` → `test` (in-game QA) → `main` (user sign-off).
`akk-stack/` and `Client_RoF2_Dev/` are gitignored (live source / client); tracked
mirror is `server-mods/`. Audit trail is `CHANGES.md`.

---

## 1. QA GATE — stable DLL mana gauge (#12/#13)

**Status:** fixed, regression-tested, manually accepted on the dev client, and
promoted through `dev` to `test`. Awaiting user sign-off before `main`.

**Root cause:** `CPlayerWnd` refreshes the HUD every 500 ms using a separate
base-class mana predicate. It repeatedly hid `PlayerMana` after the old
`Max_Mana` detour forced the child visible.

**Fix:** redirect only the exact guarded predicate call to report whether the
authoritative `pinstLocalPlayer+0x354` server maximum is positive. The stock
HUD now owns visibility continuously; the competing direct `SetVisible` call
is gone.

**Accepted on dev:** Pups's gauge stays visible and tracks casting/regeneration
through zoning and relogging; a true zero-mana melee character remains hidden;
Done's stock caster HUD and both clients' spell windows remain stable.

**Test QA:** repeat the focused spike in
`docs/qa/2026-07-28-mana-gauge-test-qa.md`. A black world with responsive UI
recovered by switching the client to fullscreen; treat that as a renderer
recovery, not a mana regression.

---

## 2. TACKLE NEXT — no DLL dependency

Waypoints #32, multiclass skills #36/#39, AA XP #37, and the completed B2 mana
path are already present on `dev`, `test`, and `main`. Equip #38 remains
client-blocked as expected. Start #16 after the test promotion is verified.

---

## 3. GitHub issue audit (from 2026-07-18)

I cannot post/close on GitHub (auto-mode classifier blocks the write) — user closes, or
lift the restriction and I'll action.

**Close — verified shipped:** #8 (heroic stats), #25 (item scaling), #24 (stat example, ref),
#9 (vendor dupes), #21 (spell-vendor 500-cap split), #11 (M1 mana/HP).

**Needs a decision:**
- **#4** AA class column — RoF2 can't add a window column; the 2026-06-22 name-prefix
  workaround was likely dropped in the Chronicler v2 rewrite. Close as client-limited /
  superseded by DLL, or re-add prefixes.
- **#32** waypoints — now fixed on `test`, but was reverted on `main` (`6b44430`/`789e410`).
  Reconcile: the fix supersedes the revert; re-land to main with the rest of the batch.

**#38 comment** — post server-ready + DLL-blocked note on the issue (text drafted in chat;
was classifier-blocked).

---

## 4. DEVELOPMENT BACKLOG

Priority order:
1. **#16 AA "Unknown DB String"** — data-only fix, no rebuild. Safety check done: **0 of the
   broken AAs are purchased**. Finalize the discriminator (name-pattern = 29 rows vs the
   issue's title_sid-not-in-client-strings = 193), then `UPDATE aa_ability SET enabled=0`
   for that set + zone restart (loader filters `enabled=1`). Durable script in
   `eq-solo-gm/scripts/`.
2. **#22** bag vendor prices — small SQL, scale realistically (plat via vendor sales).
3. **#23** features HTML page for GitHub Pages — static site, no server.
4. **#26** augments (one per zone, scaling) — design already at
   `docs/superpowers/specs/2026-07-16-zone-augments-design.md`; large content build.
5. **#19 / #20** bard songs (movement speed / won't land while running) — #19 diagnosed
   (needs in-game instrument_mod reading); capture during a login session.

---

## 5. HOUSEKEEPING

- **Unpushed:** `dev`/`test` are several commits ahead of `origin` (all local this session).
  Decide whether to push.
- **Merged branch:** `feature/mana-gauge-flicker` is in `dev`/`test`; delete
  after the promotion is verified.
- **Deferred (user's call, DLL milestone):** activated combat skills mask-aware in
  `special_attacks.cpp` (kick/flying-kick/bash gate on base `GetClass()`; add to epic #10
  Track A scope).
- **Minor cleanup:** I added `Client::SetAAExperiencePercent` but `SetAAEXPPercentage`
  (client.cpp:13112) already existed — dedupe to the existing one.
- **Client-folder deployments (untracked):** survey `dinput8.dll` (+ `.b1bak`), and
  `MQUI_CastTimerWnd.xml` copied into `uifiles/default` to stop the MQ2CastTimer spam.
- **Known trap documented:** `global_player.pl` is inert (Lua wins load precedence) — a stub
  now warns against editing it; live global-player logic goes in `global_player.lua`.
