# Phase 42: Launcher Play incident repair

Fixed the classic-model PFS version/block-size mismatch that aborted RoF2 while
reading `ncm01_chr.wld`. Repacked 22 archives with native 8 KiB blocks and rebuilt
their matching proxy/hash contracts. All 14,858 extracted entries and the current
gameplay inventory are preserved. Added independent regression tests and a
reader guard so a permissive zlib round-trip cannot hide this failure again.

[Incident, release evidence and exact QA](../releases/launcher-play-20261001/README.md).
The owner explicitly authorized main and production publication. Remaining gate:
visible Play and post-login model loading on the owner desktop, which was locked
during automated verification. The signed QA controller reached login UI and
stopped cleanly after 120 seconds; it does not establish rendered gameplay.

Cut: launcher redesign, model-policy changes, server restart and gameplay/data
rollback. None is needed for this archive-format repair.
