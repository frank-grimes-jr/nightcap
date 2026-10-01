# Character-selection startup incident — October 1, 2026

High-impact continuation of the owner-authorized main/server Play repair.
The player reaches login and selects Nightcap, then gets a Visual C++ abnormal
termination before the character screen. At the reported failure, the installed
release was 2026100102, including the spell-inspection correction. The earlier PFS block-size
repair is working: this log successfully reads the first three custom archives.

## Root cause

The preserved dump fails in the original `EQGraphicsDX9.dll` at RVA `0x13680`,
reading `[ecx+0x3c]` with `ecx=0`. Its caller at `0x16b9c` dereferences the first
material in a palette. The native importer at `0x1cfa0` filters bitmap (03),
material (30) and palette (31) fragments by the selected actor's first three
letters, then resolves the palette's references without checking for null.

The first affected import is `zcs,ncm04_chr` (original DER, race 100). Its palette
references generic shared weapon materials whose names fail that filter.
The same audit finds missing dependencies for ZET, ZGE, ZIO, ZKY, ZMJ and ZNN.
An intact WLD from a zone archive is not necessarily safe as a per-actor import.
Archive round-trips and inverse renaming could not detect this native constraint.

## Repair contract

`tools/classic_model_materials.py` clones only the necessary shared dependency
chains into each importing actor's namespace. Existing actor-owned materials
retain their names for skin variations; only dependency references change.
Original geometry, animation and actor fragments remain byte-identical after
the established rename. Ordered palette/render data and texture-file payloads
remain equivalent. Numeric and named references are validated by type and bounds;
valid untextured materials retain their zero texture reference.

Signed repair **2026100103** contains **46 files / 149,786,199 bytes**, using the
existing production signing key. Proxy **0.7.2-dev** binds the corrected hashes.
Seven archives, the proxy and the catalog's version field change; the other
37 files, all 67 patch sites, model mappings/imports and gameplay content remain
unchanged. Starter/desktop replacement, server restart and database writes are
not needed. The original RoF2 client remains read-only.

Channel SHA256:
`a16273c7be18f1c0dc0258abd71b517adac0b6687af708f59147e8043ecbb46c`.
Expires **2026-10-31 22:02:15 UTC**.

## Verification and publication

All 22 generated archives pass native material closure and independent
geometry/animation/material/texture preservation checks. Full Go tests and
rebuilt x86 proxy/native fixtures pass, including actual PE bootstrap and
native configuration/health agreement. Twelve publisher recovery and drift
tests pass (Windows locking/directory-fsync stubs; real Linux staging separately
verified). Signed local packaging verifies against the shipped production key.

The independent read-only review approved the fix with no blocking findings.
It independently confirmed native scan bounds include appended clones and all
22 transformations are idempotent. Six focused regressions cover two actors,
numeric/named references, valid zero texture references, deterministic output,
unchanged owned names and rejected corruption. Replaying the old identity
transformation fails specifically because the native filter skips `SKULL_MDF`;
the corrected transformation passes. Executable tests and red/green output are
retained in the local evidence directory below. A prior write of the managed
regression test was cancelled; it was not retried, so these focused tests are
not committed in the source tree. Generator and release-verifier checks are.

Signed release **2026100103** is now published on OVH. The guarded
[publisher](publish.py) installed immutable files and switched the channel last,
under the shared deployment lock and captured service/public baseline.
All 46 remote files matched the signed stage and verified independently over
HTTPS against the public key shipped in launcher 0.3.1; all five services, launcher channel,
starter and guide were unchanged, with no service restarts or database writes.
The existing production updater installed 2026100103 into `E:/Nightcap` and
verified all 46 managed files. All 33 INI files and the game, graphics DLL and
launcher executables retained their hashes. No game process was launched.
[Machine-readable publication/verification](verification.json).

Detailed local evidence: `E:/EQ_Local_Dev/artifacts/character-select-crash-20261001/`.
Crash dumps and logs stay local; the upload contains only public assets and
publication metadata, with no signing seed or player credentials.

Recovery is forward-only: retain the prior channel as evidence, then publish
any further corrected generation with a higher release counter. Reinstalling
the known-broken model archives is not a playable rollback.

## Required player acceptance

1. Close the failed client, reopen the usual Nightcap shortcut, and click Play.
   The patcher must install game release **2026100103** automatically.
2. Log in, select **Nightcap**, and wait for the character screen. All custom
   actor imports must finish without the material access violation. A proxy
   `ready` state or a timed stay at the login screen is insufficient.
3. Select a character and enter **East Commonlands**, then camp and repeat Play.
   Confirm normal world rendering and launcher return to idle after closing.
4. Retain the separate classic-model appearance/animation and spell-inspection
   QA gates. Record the fresh `Logs/dbg.txt`, installed generation and result.

Rendered/post-login acceptance remains open until this actual player path passes.
