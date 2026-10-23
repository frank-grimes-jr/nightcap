# Chapterhouse deployment — October 23, 2026

Deployed for owner live testing. Feature 8f4f7f1f promoted through PR #309 (dev),
PR #310 (test), PR #311 (main c0c9896e151999e7002a453594079dae7b83bc41).
The owner explicitly requested main and server activation. This is not completed
in-game acceptance. Start with Camil 999521 in East Commonlands; Keeper 998820
near Befallen in West Commonlands opens the level 50 expedition.

## Verified release

Production image `sha256:db570029805ba5145824529a4487de62536b207e86ab61054feab7d1a199579c` uses paired world 97403fda,
zone 2c9323e4 and shared_memory 375814fe plus 13 exact-ID scripts. Both campaign
tables, 35 managed spawns, Tasks 9800/9742/9743, curated rewards,zone exception,
waypoint and Keeper are installed. Campaign/dungeon admission is enabled.
All 12 workers, native health, 45 schema / 532 content checks and 427 cache definitions
pass. The actual loader preserves 309,844 existing item definitions and adds 13;
helmet 990500 and spells stay unchanged. Classic 50 and signed client 2026102301
remain; no client update is needed. The server has Chapterhouse map/nav assets.

A fresh stopped backup is retained on the host. 91 saved-state tables
were checked, with the rehearsed waypoint catalog addition and exact native
seven-day non-corpse expiry accounted for. Inventory, earned progress, corpses,
run UUIDs and receipts were not restored or reset. Public access is open.
See deployed.json,preflight-receipt.json and the original private host receipts.

Wiki 20261023-camil-chapterhouse-v1 publishes 483 files / 476 HTML pages, with a
Vigil guide and 14 reward pages (13 new definitions plus the existing helmet).
All public hashes/security headers and five private-route denials verify.
The existing 384 Hunt values, Build Lab, loot finder and private guide are preserved.
Wiki source: feature/chapterhouse-wiki in the aa-level-wiki managed checkout.

## Holds and recovery

Initial activation committed the guarded schema/content, then held closed.
The existing preservation list includes `nightcap_waypoints`; its expected
content addition was incorrectly treated as player-state drift. Exact inspection
found only checksum4261781391→2941369031 for that public catalog; all other
saved tables and all content contracts matched. The first continuation refused
the gateway's normal SIGTERM143 exit before any write; native game exit was0.
The tested resume-v2.py accepts those exact stopped states and only the
rehearsed waypoint checksum. It never replays SQL or restores a snapshot.
Original evidence and held receipts are retained. Successful continuation uses
`/opt/nightcap/releases/camil-chapterhouse-20261023/resume-evidence/`.
Do not replay activation or continuation. For later recovery, disable new Vigil
admission while retaining matching schema/content/runtime and earned claims.

The host initially had584MiBfree. Seventeen explicitly selected, unmounted
historical staging binaries were losslessly compressed with verified
decompressed SHA256,freeing3767819385bytes. No image,active file or database
backup was removed. Adjacent `.chapterhouse-recovery.gz` files and
storage-recovery.json retain restoration hashes/modes. Restore an old binary
copy before attempting its historical operator; do not roll back player data.

## Validation and owner QA

Five release test groups cover 16 injected activation failures, cache preservation,
campaign gating,waypoint-only state adjustment and exact stopped-state exits.
Chapterhouse5tests pass again; prior native, dungeon, Hunt, SQL, geometry and 48-case
maximum-legal-power arena evidence remains in the parent directory.
Wiki 68 Linux checks, 15 focused Windows checks,Build Lab and equipment Node suites
pass. Installation and visible gameplay acceptance remain separate.

Use [the exact in-game checklist](../QA.md): Camil eligibility and both journals,
Sered interruption,Elowen's three waves,Halvyr's adds,Vaelen/Shadow movement and
stuns,personal recovery/helmet delivery,waypoint/exits,era-safe drops and forging.
Test both modes with legal maximum power including Ascended Ghoulbane,Slay/proc/
critical AAs and other strong Paladin combinations. Full-clear difficulty,
pathing,client models and owner acceptance remain open.
