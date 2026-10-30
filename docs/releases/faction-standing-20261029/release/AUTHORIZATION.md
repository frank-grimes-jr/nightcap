# Faction display release authorization — October30, 2026

The reviewed faction feature merged to main in PR378/3c3d815e after the owner
initially selected “Merge main only for now”. The owner subsequently instructed
“Deploy to server”, renewing authorization for the scoped OVH deployment and
its necessary controlled whole-game restart. Native gameplay acceptance is open.

Automatic review previously rejected a private source/inventory export. The
revised preparation keeps detailed metadata and receipts on-host, returning only
aggregate checks; the private export was not performed. Automatic review also
required explicit consent before replacing unused staging binaries with archives.
The owner approved: “Approve archiving and removing verified originals”, scoped
to at most six verified unused staging binaries with round-trip hashes, retained
archives/restoration receipts, and untouched active images/backups/player data.
Five files were archived; their detailed restoration receipts remain on-host.

Only the faction display is authorized here. Preserve newer live content,
world/shared_memory, quests, caches and signed client. Do not ship the earlier
integrated test binary containing augment work or the separate capacity change.
No faction data migration or client update is needed. Native startup registers
the single new command_settings row at access0; all existing command settings
and privileged faction reset access are guarded. No player snapshot restoration.
