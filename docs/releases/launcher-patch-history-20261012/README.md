# Launcher patch summaries — published October 12, 2026

The owner explicitly authorized main and server publication. [PR #186](https://github.com/frank-grimes-jr/nightcap/pull/186)
merged at `c76c139a8d0750f6b898b89f6eeb378834bc4305`. Desktop **0.6.0**,
launcher channel **2026101201**, and game channel **2026101202** are published.

The launcher shows concise Feature/Bug fix bullets for the latest verified patch
and expandable dated previous patches above client/file details. History remains
usable during patching and afterward. The signed catalog includes the new notes
feature and five recent client releases: merchant Sell All, pet-summon crash,
stock loot icons, loot-row controls and loading artwork. Missing current summaries
do not borrow older patch descriptions. Notes are rendered as plain text.

## Delivery and preservation

The game package is metadata-only: all **105** client assets, **211,935,357** bytes,
match the captured 2026101201 release exactly. No game/DLL rebuild, database,
quest, player-file or server-runtime change was made by this publication. The
existing starter ZIP and guide are byte-identical. All five service identities,
images, start times, restart counts and health states match the baseline.

The obsolete pre-final asset folder contained a different DLL; pre-signing hash
validation stopped that attempt. The final published 2026101201 files passed
all 105 size/hash checks and were used instead. The signed release preserves
the published DLL `c3823ec3af4a7d49de42e9c4753c83d256ce7ed8246758923872402462c7e24b`.
Concurrent early-scribing source was merged from main, but its separate native
and client release was not deployed by this task.

The desktop build preserves the 0.5.0 shipped trust policy and recovery inventory,
changing only its launcher version. Keys, allowed hosts, retirement preimages
and protocol trust remain. Notes-bearing manifests require 0.6.0. The unchanged
starter verifies the separate desktop channel and downloads the new desktop
before it checks the game channel. Existing legacy manifests remain supported.

## Verification and evidence

- Full default and production-tagged Go suites passed, including the merged
  main preflight catalog. Frontend build and dependency audit passed with zero
  reported vulnerabilities; Wails production desktop compilation passed.
- All 11 Chrome tests passed. Additional actual-catalog checks verified minimum
  window width, keyboard scrolling during patching, all five historical entries,
  persistence after patching and missing-current-summary behavior. Rendered
  normal/minimum-window layouts were inspected.
- Three publication regression groups passed, including interruptions after
  immutable staging and each channel commit, idempotent resume, concurrent drift
  rejection and signed-hash checks before reusing hosted assets.
- Independent signature/size/hash checks passed for the local game package and
  compiled desktop channel against the previously shipped public key.
- The host staged a seven-file upload, reused all 105 existing game assets after
  verification, and switched desktop then game channels under `.deployment.lock`.
  The private signing seed remained local and was excluded from the upload.
- Public HTTPS verification downloaded and checked both exact channel envelopes,
  all 105 game files and the desktop executable. Both signatures verify against
  the previously shipped production public key; sizes/hashes match the candidate.
  Post-publication capture confirms service continuity and starter/guide retention.

Compact receipts are stored beside this document. Operational artifacts and
test scripts are retained in
`C:/Users/verre/Documents/Codex/2026-10-12/th/work/release/`.
The exact publisher is retained on-host under
`/opt/nightcap/releases/launcher-patch-history-2026101202/`, alongside
`previous-channel.json`, `previous-launcher-channel.json` and `published.json`.

Game channel SHA-256:
`350d2e7833013705395e6d24f9792720533a49a7f4e66c44ed563e5fc6f224c2`.
Desktop channel SHA-256:
`67a94a6d56fca08d21c0d808a2929855ec9e20bf8891ccd390f23cf1f18c3e8e`.
Desktop executable SHA-256:
`ce16849764fe15996d01dc69276db175ac512e56b4091d9326a9382da9045a33`.

## Player check and recovery

Fully close EverQuest and the launcher, then reopen the normal Nightcap shortcut.
Confirm launcher 0.6.0, latest patch 2026101202 and the Previous patches section.
Expand history before/during patching and confirm progress, Cancel and normal Play
still work. Review wrapping and keyboard access at the minimum window size.
Automated delivery checks do not claim native visual/player acceptance.

Keep both prior channels and immutable release trees. After clients have observed
this release, rollback must use higher signed counters. Retain a notes-aware
desktop (0.6.0+) to recover journals containing the new signed metadata. Restore
older content only under a new higher game counter; never rewind checkpoints.
No service restart is part of this release or its static-publication recovery.
