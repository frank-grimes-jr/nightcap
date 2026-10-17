# Raid & Grind patcher announcement — October 17, 2026

The owner requested a prominent Latest Update announcement for the deployed
dungeon feature. Signed game metadata **2026101701** leads with Raid & Grind,
all seven dungeons, solo/group entry, twelve-hour runs, difficulty and respawns,
personal clear credit, shared and exclusive custom gear, durable claims and the
repaired boss checklist. The eleven bullets fit the existing notes contract.

This is a notes-only publication. All 106 complete client file records and URLs,
the thirteen prior summaries, tombstones, expiry and minimum launcher 0.6.0 are
preserved from freshly verified game release 2026101501. No desktop, client DLL,
server binary, database, item cache or gameplay restart is required. The native
dungeon release and the scoped Befallen journal acceptance remain separately
recorded in [dungeons](../../dungeons/README.md).

## Verification and publication

`sign-notes.go` uses the launcher's actual manifest parser and shipped production
public key to verify the previous envelope, validate/sign the exact new summary,
and verify public HTTPS metadata and every referenced asset after publication.
The private seed stays local and outside the repository/publication directory.
The publisher and seven recovery tests are the reviewed AA notes publisher with
only release numbers, file count and staging names adapted. Under the shared
deployment lock, it checks fresh public-file and service preimages, all 106
assets, complete metadata preservation, and a durable previous-channel backup;
it fsyncs and atomically replaces only the signed channel.

The manifest and packager tests pass, including the updated fourteen-entry
history fixture. All seven publication/recovery tests pass on Windows and Linux.
Chrome renders the actual Vue launcher with the new notes at 1120×820 and its
780×620 minimum: all eleven bullets and thirteen historical summaries are
present, no horizontal overflow or page errors, and Play Nightcap is reachable.
This browser preview uses a simulated native status bridge; it does not establish
owner acceptance of the installed desktop. See `layout-verification.json`.

Signed/staged channel SHA-256:
`794a2611083fb3f9289ced3e3d9a87da7b1e5b3a6f40d07f9db064fba12fdaa7`.
Origin staging and Linux recovery tests pass; public activation is pending.
The read-only baseline found all five services running, with game/database
healthy. An initial SSH failure was caused by the stopped local Windows
ssh-agent; starting the existing service restored the saved key. Server access
and keys were unchanged.

## Recovery and player check

The staged operator is retained at
`/opt/nightcap/releases/dungeon-patcher-20261017/`. It accepts only the reviewed
old or candidate public channel and exact other-file/service preimages. Drift
requires a fresh assessment. A retry preserves the original backup; after any
client could observe this release, corrections use a higher signed counter,
never a rollback of the public release number.

Reopen the normal patcher shortcut or choose **Check for updates**. Latest update
should show **Oct 17, 2026**, patch **2026101701**, and begin **Raid & Grind dungeons
are live!** Expand Previous patches to find the earlier equipment fix. The usual
Play flow remains available. Installed desktop confirmation is pending.

## Whole-wiki assessment

The public dungeon guide already explains the seven modes, every required boss,
reward qualities, Keeper actions, progress and claims. Features, home, travel,
commands, item/zone catalogs, equipment, Recent changes and the remaining guides
need no content change for this announcement. Live testing remains the correct
feature label: reward, all-mode, restoration geometry and balance checks remain
open. The scoped journal confirmation does not accept those unrelated checks.
No website publication is needed for a patcher-only summary.
