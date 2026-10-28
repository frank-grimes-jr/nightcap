# Paired Paladin repair release — October 28 live QA

The owner-approved release is on main and OVH; admissions are open. Source head
703adec3cfee5f155a3f86cfaf1647b3199c8c99 was merged through
[PR352](https://github.com/frank-grimes-jr/nightcap/pull/352) at
979ec08b0ed1d1e855040fdbab8a95d4a80d01fd. See AUTHORIZATION.md.

## Deployed pair

- Runtime image: `sha256:2913f609ee2865fe9753269c633f13c7d484984842341ec4ffc35778c6cc5050`.
  Started 2026-10-28T15:49:42.136389293Z; three matching native binaries and seven
  quests. All 12 workers, 51 schema checks, 565 content checks and 102 saved-state
  tables passed. Runtime native/quest/database errors were zero. Fresh stopped
  backup and exact quest preimages retained privately; player data was preserved.
- Signed client **2026102801**, proxy 0.13.1. Four changed assets: DLL,
  catalog, config and the coordinated Bazaar XML parser repair. The other 137
  descriptors, patch history and tombstones are retained. All 141 HTTPS assets,
  signature and actual DLL/catalog pair passed verification. Channel SHA256:
  `9eee0052b203db71a18bcc2bf1ce62089b50fbd34d95a77deb41134b74c6c709`.
- Wiki **20261028-paladin-bazaar-repair-v1**: all 40 source articles reviewed,
  seven guides and search changed; 491 files preserved. All 499 public files,
  security headers and five denied private routes verified. Publication rehearsed
  pointer rollback and preserved service IDs/start times and nginx configuration.
- Approved owned weapon profiles and Ascended quest rewards are installed.
  Existing normal Defender owners have the free instance-preserving exchange.
  Other classes keep their paid recipe. Monk AAs are unchanged. Raw SQL/base
  catalog definitions and existing item/spell caches remain unchanged.

## Evidence

`deployed.json`, `preflight-receipt.json`, `production-reference-deploy.json`,
`client/{published,public-verification}.json`, `wiki-publication.json` and
`wiki-public-verification.json` are the completed release receipts.
`evidence.json` pins their hashes. `bundle.json` and native identity proofs bind
the original 29-member approval archive to the final stripped binaries; the
coordinated Bazaar XML is the fourth client asset in the final signed package.
Original debug binaries are retained. `disk-preservation.json` records lossless
archival of two unused historical staging binaries, with restoration receipts;
no production images, volumes, backups or active executables were removed.

Final checks: 11 client runtime groups, 117 executable guards, three Go suites,
80 native animation selections, four fresh quest-dispatch preflight groups,
16 Bazaar/UI regressions, 30 rollout and 17 client publisher fault tests on Linux,
19 wiki source tests and 16 Linux wiki publisher tests. Earlier native/MariaDB,
Lua and Perl progression checks remain in ../progression/. Independent review
closed the dispatch, payload authentication and fresh wiki target-gate findings.

## Player confirmation still required

Fully exit EQ and use launcher Play to install **2026102801**. Test SoulFire 1HS
with a shield without zoning, then empty-offhand swings and both toggle directions.
Check two same-ID copies with opposite grips, all weapon families and qualities,
quest rewards, free exchange and persistence after zone/relog/Bazaar restoration.
The cache defect has native regression proof; rendered animation and actual
equipment acceptance remain open. See ../../QA.md and ../README.md.

## Recovery

Do not replay completed activation/open/publication scripts. Any uncertain action
holds admissions closed for reviewed forward recovery; preserve newly earned
state and grip-aware code. Never restore an old player snapshot or mass-rewrite
inventory. Keep the native exchange binding, seven quests and client paired.
Client recovery requires a higher signed generation; the prior proxy restores
the known cache defect. Authenticate current channel/wiki/runtime preimages
before continuation. An old archived staging binary must be restored and hashed
from its adjacent preserved gzip before that historical stage can be used.
