# Client delivery and parity work — September 15, 2026

Goal: deliver the client patcher and client capabilities required by the open
Nightcap issues. The full [approved multiclass contract](../superpowers/specs/2026-07-28-true-multiclass-production-spec.md)
remains the acceptance standard. This plan does not reduce it to a download tool.

## Current evidence and work order

| Issues | Evidence | Work and completion proof |
|---|---|---|
| #13 | Proxy caster/mana path and scoped Monk attacks exist; scoped equip candidate built, in-game QA pending | Prove exact equip/scribe/memorize call sites; patch only local eligibility, retain server rejection and truthful tooltips; normal UI positive/negative tests in all held slots |
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
MQ2 RVAs, not eqgame offsets. The pinned official `emu` branch and eqlib match the 32-bit May 10 2013
client; equipment function addresses were confirmed against our executable. A
reproducible build/plugin and compatibility test remain required before runtime
adoption.
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
`f4b77136b0b8e095814c41c26404595393273304`, with eqlib
`db5c8806f86d1f9b5496842c2fd38fdabd1f659c`. The equipment candidate now
redirects the proven equip/class calls with item/thread scope. Native tests,
exact client checks and x86 build pass;
[equipment QA](../../eq-client-dll/docs/equipment-qa.md) is pending.

### Verified asset staging

`eq-launcher/internal/assets` now verifies metadata before inspection, computes
size/hash differences and assembles complete candidate generations. Tests cover
corrupt/missing/current files, user-file preservation, bounded HTTPS streams,
partial-release failure, redirect host/scheme limits, cancellation, Windows
junctions, client/staging separation and cleanup failure reporting. Current local
files are copied and rehashed; tombstones remain unapplied. A completion marker
never substitutes for content revalidation or required runtime health. Journaled asset
installation, process exclusion and restart recovery are now implemented in
`internal/installer` and `internal/installguard`; production activation still
requires configuration semantics and the remaining release/runtime health gates.

### Guarded installation and recovery

The native Windows guard and complete asset transaction core now pass tests,
including actual subprocess exit during installation and recovery. Immutable
backups and pending state restore the full prior file generation. Local monotonic
checkpointing supports repair and rejects ordinary downgrades. Protocol, evidence
and explicit limits: [ADR 0031](../adr/0031-journal-client-generation-recovery.md).
The real game remains unmodified. Next delivery work is Wails orchestration and
installed-generation/configuration/patch health before Play, with production
signing/rotation/rollback/self-update still required. Remaining client parity
hooks and in-game acceptance retain their original scope.

### Wails shell and release orchestration

The Windows preview now builds with folder selection, inventory, update/repair,
recovery, cancellation and session activity. A serialized Go controller repeats
signed checks for every update and never accepts policy from the UI. Read-only
local inspection reports active metadata/content and pending recovery. Core and
desktop Go checks plus six real-browser fixture tests pass. Native interaction
QA is pending; no production keys or Play authorization are present. See
[phase 12](../milestones/phase-12-report.md) for build evidence, failed native smoke
limits and the full remaining release/parity work. Next work should implement
required config/patch/runtime health and remaining client gates, alongside native
manual acceptance; a functional browser fixture is not the release end state.

### Shared static preflight

Public installation now verifies required signed configuration/catalog assets
and all 22 recorded original PE sites before mutation, using the exclusive
executable handle. C++ original-byte declarations and the Go embedded catalog are
generated from the same versioned input. The real-client diagnostic passes;
Play stays false. [ADR 0032](../adr/0032-share-client-patch-catalog-and-preflight.md)
records exact semantics and the remaining DLL config/runtime-health work.

### Runtime activation and health

The candidate proxy now consumes required config, serializes first-export
initialization, pins its lifetime and terminates on required failure. Atomic
health identifies process creation, nonce, config/catalog hashes and applied
feature mask. Go rejects stale/incomplete reports. Native failure tests and
cross-language agreement pass; [phase 14](../milestones/phase-14-report.md).
Next: prove startup ordering relative to every patched consumer, then implement
actual launcher process/nonce/health orchestration. Complete remaining parity and
production release requirements from the original contract; Play remains disabled.

### Before-entry bootstrap

The initial system-breakpoint experiment stalled under loader startup; the exact
executable-entrypoint gate now passes native fixtures and actual proxy failure
before fixture main. It retains checked process/job ownership and exposes an
explicit proxy initializer. [Phase 15](../milestones/phase-15-report.md).
Next: turn the primitive into the signed x86 helper, connect verified installation
locks, PE export validation, private nonce and Go health approval, then prove the
supported-game startup path and remaining parity. This supersedes reliance on
ordinary first-DirectInput timing; the launcher still does not expose Play.

### Verified launch lease

`installer.PrepareLaunch` now verifies the cached signed generation using held
Windows read locks, pinning directory paths and excluding updater writes. Public
preparation passes for a disposable supported-client copy; no game is started.
[Phase 16](../milestones/phase-16-report.md). Validated PE entry/export metadata
now comes from the retained executable/proxy handles;
[phase 17](../milestones/phase-17-report.md). Next: connect the signed x86 helper
and private health exchange, then keep lease/process/job ownership through sessions.
The production and full parity contract above remains unchanged.

### Native helper protocol

The x86 helper wraps the entry gate with bounded inherited-pipe messages and
retains the owned process/job through session exit. Parent loss and stdin closure
terminate its owned session. [Phase 18](../milestones/phase-18-report.md).
The Go owner now requires signed helper inventory, validates process-bound health
before ACK and retains the launch lease through termination.
The unsigned native fixture success is not Play or supported-game acceptance.

### Go session ownership

`session.Start` now joins offline preparation to the native helper with private
nonce/handles, strict ordered responses and health approval. An outer Windows job
contains unreported children; cleanup confirms all owned processes terminated
before releasing files. Startup context is separate from established-session
Close/Wait. [Phase 19](../milestones/phase-19-report.md).
Next: wire this backend into Wails session state/cancellation, provision a trusted
candidate release, prove supported-game bootstrap and complete the remaining
parity/release/owner-acceptance contract. Default Play remains disabled.
