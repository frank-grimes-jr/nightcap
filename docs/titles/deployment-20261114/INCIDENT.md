# Stopped-world occupancy guard

The original immutable operator is retained as `release-original.py`, SHA256
`2b79e458de54e2edd4140a116373ff4a997f0a9422ec3cf6ceb3770ec206cba3`,
from main `b824e0d2`. Its stopped-backup hook called the native player-count RPC
after a clean whole-game stop. That RPC needs the world process and failed.
The first attempt held safely with the game/gateway stopped, a completed backup,
and **no** title SQL-started/installed receipts. No title migration or player
snapshot restore occurred in that attempt. Private diagnostic evidence is retained
in `artifacts/titles-live-20261114/hold.json` and the production deploy log.

The diagnosed hold is `held-1794691016729160326.json`, exact SHA256
`5a9fb9bf2460d2fe2a4aad86d2435194de987f165250a1a61e782bb32d727cdc`.
The source fix checks clean stopped process state instead of calling world RPC.
Recovery uses the real count whenever the game is running and clean stopped
state only while it is stopped. Twelve release fault controls cover both cases.

`resume.py` is a separate, bounded continuation. It verifies this exact hold,
absence of migration/terminal receipts, original image, clean stopped state,
all old player state/content/startup guards, and integrity of the first backup.
It takes a second fresh stopped backup under an exclusive new path, then invokes
the same rehearsed schema installer. Native saved-state expiry, one market
rotation, all twelve binaries, content/caches/client and error checks gate
reopening. The exact old hold is archived as resolved only after closed
verification passes. Any other/new hold remains blocking. Seven checkpoint
tests and independent fresh review found no forward-continuation blocker.

The original stage's operator/manifest are not rewritten. `resume-staged.json`
pins the separately staged continuation. `release.py` contains the corrected
reference implementation for future planning; its bytes differ from the original
immutable stage. Never replay the terminal deployment/continuation or invoke an
old recovery CLI after opening or title activity. Later issues require forward
repair and preserved awards/counters, with a fresh stopped backup if restarting.
