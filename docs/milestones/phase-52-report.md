# Phase 52: Winged Paladin helmet live QA release

October 4, 2026. This phase delivers the assets, item and Camil appearance to
main and OVH under the owner's live-testing instruction. Native acceptance
is still open; publication does not establish reference fidelity or wear.

Built: a 56-object editable Blender source, Unity FBX inspection, a reduced
3,765-triangle game mesh, original EQ texture reuse, 24 Classic race/gender
fits, strict WLD encoding and archive preservation checks, signed local QA
installation, and guarded item 990500 with balanced Classic endgame stats.
A full database backup and rolled-back insertion rehearsal preceded creation.

Cut from scope by the owner: Iksar, Vah Shir, Froglok and Drakkin. The earlier
later-model experiment is superseded. No quest or loot acquisition was added.

Verified: thirteen helmet Python tests, five gameplay-generator tests, three PFS
tests, the Go package tests, decoded native fit-sheet
inspection, Unity import, signed installation and native startup/bootstrap.
Original archive fragments and textures remain unchanged. No source-client
files were modified. The public client channel is now 2026100401.
The packed standalone Blender source reproduces the exact candidate game mesh
when reopened and exported in a separate process.

Open: native equip/unequip and all-race testing, native reference-image
verification, Camil's rendered appearance, and representative crowded-zone
performance. The item is verified
in SQL and in the live shared-memory cache after the approved game restart.

The owner explicitly approved the restart and main/server promotion after
Codex confirmation. The restart completed with unchanged world, zone and
shared_memory binaries, all twelve zone processes refreshed, healthy game
service, and the gateway reopened. This resolves the earlier automatic-review
restart rejection. An unrelated player-record query was rejected and omitted;
the owner elected to test directly on the live server.

Production release 2026100401 is published and independently verified over HTTPS
against the shipped launcher public key: 48 files, 160,550,091 bytes, all 46
baseline files unchanged, only two global archives added. Camil now uses material
90. A fresh full backup, rolled-back SQL rehearsal, exact content comparison
and unchanged runtime hashes establish deployment; his cache row was retained.
Independent review caught and resolved the canonical asset generator's missing
helmet integration. A full generation now reproduces all 44 gameplay files
exactly, including the two helmet archives; it does not depend on the original
one-off release composition script.

The operational guide and exact in-game checks are in
[winged-paladin.md](../helmets/winged-paladin.md).
[Deployment and recovery](../releases/winged-helmet-20261004/README.md).
