# Nightcap — Next Steps / Backlog

Living task list. Most urgent first. Updated 2026-07-19.

Branch flow: `feature/*` → `dev` → `test` (in-game QA) → `main` (user sign-off).
`akk-stack/` and `Client_RoF2_Dev/` are gitignored (live source / client); tracked
mirror is `server-mods/`. Audit trail is `CHANGES.md`.

---

## 1. IN FLIGHT — DLL B2 offset survey (#12/#13)

**Status:** blocked on a good HITL capture. Branch `feature/dll-b2-offset-survey`
(commits `7a31c9b`, `83beceb`, `4a1b902`) — **not merged to dev** (kept separate until B2 is complete).

**What happened:** the survey harvests eqgame offsets out of MQ2's memory, but MQ2
**unlinks its own module** from the loader list, so `GetModuleHandle`/Toolhelp find
nothing. Two survey runs found no MQ2 at all in the process:
- Run 1: MQ2 not launched.
- Run 2 (20:02): full module dump, no MQ2 anywhere — and the wait loop exited in ~88ms
  (timing bug, now fixed).

**Fixes already deployed** (survey `dinput8.dll` is in `Client_RoF2_Dev/everquest_rof2/`,
B1 saved as `dinput8.dll.b1bak`):
- `FindMq2()` now falls back to a raw `VirtualQuery` memory scan matching a mapped image
  that exports `pinstCSpellBookWnd` — finds MQ2 even when hidden.
- Wait loop rewritten with a `GetTickCount` deadline (5 min) + per-poll elapsed logging.

**BLOCKER / open question for the user:** need the *working* MQ2 launch method. When the
cast-timer plugin spam appeared, MQ2 was demonstrably hooked — that launch is the one to
use. A resident `MacroQuest2.exe` did NOT hook a directly-launched `eqgame.exe`.

**Next when the log arrives (`nightcap_dll.log`):**
- If `MQ2 found at base=… ` + `OFFSET …` block + `watch:` lines → write the B2 patch.
- Key decision from the `watch:` lines: is `pinstCCastSpellWnd` **null on Pups (Rogue base)**
  (client never builds the window → B2 must trigger creation) vs **non-null** (force-show flag
  is enough)?
- If still no MQ2 → confirm launch method; consider fallbacks below.

**Fallbacks if the survey stays blocked:**
- Static extraction of the offset constants from `mq-rof2/MQ2Main.dll` (built for our exact
  May-10-2013 client). Init pattern: `INITIALIZE_EQGAME_OFFSET(var) => var = (var_x - 0x400000)
  + baseAddress`; the `var_x` immediates are in the DLL's init code. Deterministic, no HITL,
  but does NOT give the runtime window-null behavior (still need one live capture for that).
- Packet-illusion (epic #10 "safety net"): fake `pp.class_` to a caster in the outgoing
  player-profile so the client draws caster UI. No DLL/offsets, but affects `/who` and
  client-side class gating — weigh only if the DLL truly stalls.

**Then:** B2 patch (force-show / create spell-gem + spellbook windows behind the version
guard, size 8,774,656 / sha256 `2a8702ad…`), HITL verify (Warrior/Rogue base opens a
spell gem, mems + casts a scribed spell), merge B2 branch to dev.

---

## 2. QA GATE — promote `test` → `main` (needs user sign-off)

Everything below is committed on `dev` and `test`, deployed live, awaiting in-game QA.
Full step-by-step spike is in the chat; summary:

- **Waypoints #32** — walk onto marker in qeynos2 (~1032,1291) or nro (~265,-1814):
  expect "attune" + "N of 72", silent on re-entry, Waypoint Master recall works.
- **Multiclass skills #36 / trainers #39** — dual wield works in combat (passive);
  level-up grants secondary skills to value 1 (via Lua `event_level_up` + mask-aware
  `CanHaveSkill`). **Client-blocked, not bugs:** skills window won't list them, off-base
  trainer window won't open, activated attacks (kick/etc.) don't fire (deferred to DLL).
- **AA XP #37 (`#aaexp`)** — works at level 51+; **below 51 the client bounces it off**
  (chassis; DLL fixes it).
- **Equip #38** — still blocked client-side (expected; server allows it).

On sign-off: `git checkout main && git merge --no-ff test`, then run
`tools/apply-era.ps1 -Check` and take a backup per CLAUDE.md.

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

## 4. TACKLE NEXT — no DLL dependency (do while DLL is HITL-blocked)

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
- **Unmerged branch:** `feature/dll-b2-offset-survey` (see §1).
- **Deferred (user's call, DLL milestone):** activated combat skills mask-aware in
  `special_attacks.cpp` (kick/flying-kick/bash gate on base `GetClass()`; add to epic #10
  Track A scope).
- **Minor cleanup:** I added `Client::SetAAExperiencePercent` but `SetAAEXPPercentage`
  (client.cpp:13112) already existed — dedupe to the existing one.
- **Client-folder deployments (untracked):** survey `dinput8.dll` (+ `.b1bak`), and
  `MQUI_CastTimerWnd.xml` copied into `uifiles/default` to stop the MQ2CastTimer spam.
- **Known trap documented:** `global_player.pl` is inert (Lua wins load precedence) — a stub
  now warns against editing it; live global-player logic goes in `global_player.lua`.
