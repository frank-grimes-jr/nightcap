# Client delivery and parity work — September 15, 2026

Goal: deliver the client patcher and client capabilities required by the open
Nightcap issues. The full [approved multiclass contract](../superpowers/specs/2026-07-28-true-multiclass-production-spec.md)
remains the acceptance standard. This plan does not reduce it to a download tool.

## Current evidence and work order

| Issues | Evidence | Work and completion proof |
|---|---|---|
| #13 | Proxy caster/mana path and scoped Monk attacks exist; equip attempt still client-blocked | Prove exact equip/scribe/memorize call sites; patch only local eligibility, retain server rejection and truthful tooltips; normal UI positive/negative tests in all held slots |
| #36 | Positive server skills and trainer checks exist; Skills/trainer client gates remain | Locate client list and trainer paths using RoF2 symbols/disassembly; exact-build patches plus natural skill progression/held trainer QA |
| #4 | AA class column requested | Implement actual AA class column using authoritative eligibility metadata; prefixes alone do not satisfy this issue |
| #16 | Missing-title audit preserves owned/system AAs | Verify names/effects and ship curated strings through asset inventory; no blanket disablement |
| #17 | Merchant routing fixed independently; global widening remains | Replace client scribe/memorize eligibility rejection before retiring widened spell/item data with guarded rollback |
| #14 | Wails expansion switcher available; no trusted delta sync | Build signed manifest verifier, inventory/diff, staged downloads, journal/rollback, exact client preflight, Wails shell and Play |
| #15 | DLL hash/site checks exist; config/unload/startup health and release pipeline incomplete | Required patch health/config, signed release/rotation/rollback, Authenticode, updater recovery and clean-install QA |
| #10/#11/#19/#37 | Parent parity and server/gameplay acceptance remain | Keep full matrix and server/client regression requirements; do not close from launcher unit tests |

Reviewed current GitHub issue bodies on September 15; the local dated snapshot
is in `artifacts/client-issues-20260915.json` (not a release artifact).

## Architecture and alternatives

Use `eq-launcher/` as requested by #14: a Go core with a Wails shell adapted from
the existing expansion switcher. Its downloader currently writes directly to
the destination without content/signature validation, so copying that path would
violate the approved release contract. Build the trust and staging boundary
first; reuse the shell/config concepts after the core is proven.

Retain `eq-client-dll/` for build-exact parity hooks. The existing `mq-rof2/`
package supplied useful named exports and runtime inspection; its exports are
MQ2 RVAs, not eqgame offsets. Current upstream MacroQuest documents a modern
64-bit build. An emulator-specific source/build must be pinned and checked
against our 32-bit May 10 2013 client before a plugin becomes a runtime dependency.
The local MQ package includes proprietary components; do not assume its entire
archive is redistributable because it also includes a GPL text. Evaluate an
open-source RoF2 build/plugin for diagnostics and any UI features it simplifies.
A fresh full game-client rewrite is not justified while supported RoF2 hooks
remain available; packaged Nightcap-owned assets plus the player's client are
the delivery target, with all requested parity gates still required.

## Implementation sequence and trust boundaries

1. `eq-launcher/internal/manifest`: signed canonical bytes, trusted-key validity,
   monotonic release identity, minimum launcher version, bounded exact inventory,
   Windows-safe paths and HTTPS hosts. Tests reject tampering and alias paths.
2. Asset diff and exact executable/patch metadata preflight, then bounded staging
   downloads. No live client mutation until whole-release recovery is tested.
3. Journaled generation install/repair/tombstones and running-process exclusion;
   exercise failures at every replacement and recovery on restart.
4. Runtime parity: prove and implement equipment, Skills/trainers and native
   spell eligibility; connect release configuration and required patch health.
5. Wails player shell, settings/path selection, patch notes and guarded Play;
   signed releases/self-update, key rotation and signed rollback authorization.
6. Clean disposable-client installation plus all-class/slot game acceptance,
   fresh test promotion and owner sign-off before any new main promotion.

Trust boundaries: unsigned network metadata to trusted inventory; downloaded
bytes to staging; staged files to client paths; client-side submission to server
authority. Required assets include proxy, spells, AA strings, owned UI XML,
configuration and patch metadata. Unknown paths, keys, builds or required health
must block activation/Play. Developer fixtures are not production release keys.

## Sources

- [MacroQuest source/build documentation](https://github.com/macroquest/macroquest)
- [MacroQuest plugin development](https://docs.macroquest.org/plugins/developing/)
- [Go Ed25519 API](https://pkg.go.dev/crypto/ed25519)
- [Go JSON parsing semantics](https://pkg.go.dev/encoding/json)
- Local `eq-client-dll/docs/offsets.md`, proxy source and exact-client verifier.

## Verification status

Research and implementation in progress. No new client patch is deployed; the
binary client directory remains unchanged. Full goal remains open until client
parity, trusted delivery and in-game acceptance are proven.

### First implemented slice

`eq-launcher/internal/manifest` and the read-only `nightcap-check` diagnostic are
implemented. Go tests and vet pass. Independent review tightened null tombstone
rejection and total-release/file-count/input-size boundary tests. The diagnostic
identified the local 8,774,656-byte RoF2 executable with SHA256
`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`;
`ready_to_play` remains false because installed assets and runtime health are
not yet certified. The existing proxy's exact-site verifier also passed.

Official MQ `emu` source pinned for research:
`f4b77136b0b8e095814c41c26404595393273304`. Its `src/eqlib` dependency must
be inspected for RoF2 compatibility before any runtime adoption.
