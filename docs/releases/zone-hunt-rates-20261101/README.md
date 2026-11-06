# Per-zone Hunt drop rates

Live on OVH since 2026-11-02 00:31 UTC. Owner approved the plan and a 1.5% augment
default, then authorized main and OVH on November 1 ("Merge to main and OVH").
In-game drop QA is open.

## OVH rollout — November 2, 00:31 UTC

`rollout.py preflight|activate|open` (and `rollback` after a held activation),
staged at `/opt/nightcap/releases/zone-hunt-rates-20261101-v1` by `stage.py`. It
chains SSF's deployed guards (SSF → placeholder loot → Hate boss).

- Main PR #396 (`b7c53b3c`); dev integration PR #395.
- `build.py`: zone built in `akk-stack-eqemu-server-1` at
  `/tmp/nightcap-zone-hunt-rates-20261101-v1` from the deployed SSF source plus only
  `zone_hunt.cpp`/`zone_hunt_policy.h` (both checked against the patch base first;
  the deployed `zone_hunt.cpp` is CRLF and stays CRLF). Unstripped `8bb96c04…`;
  `package.py` strip → `90717ac7…` (53,084,304 bytes), ELF runtime identity PASS
  ([native-identity.json](native-identity.json)). World and shared_memory unchanged.
- Preflight: image `b821548e…` over base `e67956fa` (SSF); columns absent; 56 rows.
- Activate: stopped backup 66,091,903 bytes (gzip integrity passed); `rates.sql`
  added both columns and set all 56 rows to 150/50. Only `nightcap_zone_hunt_zones`
  changed among 103 saved-state tables; saved state matched the boot model after
  boot. All 12 zones run `90717ac7`; 51 schema / 671 content checks pass; zero MySQL
  errors. No Hunt zone booted in the window, so the exact new `Load()` query was run
  against production for The Hole: one row, `940280 940284 46 0 150 50`.
- Open: gateway up. No client update. Free disk afterwards: **678 MB**, below the
  ~778 MB the next release's preflight reserve needs; reclaim space first.

## Wiki — 20261101-hunt-rates-v1

Built from the live source (`feature/hate-density` `b6204eef` + SSF's
`wiki_edit.py`, rebuilt and matched to all 499 live hashes) plus this release's
`wiki_edit.py`. Exactly 244 public files changed: 48 zone pages, their 192 augment
item pages, `zone-hunt`, `equipment`, `recent-changes` and `search-index.json`
(gear pages already said 0.5%). `publish_wiki.py` ran the Linux updater tests and
switched the pointer: PASS ([wiki-publication.json](wiki-publication.json)). Public
`zone-hole.html` shows 1.5%/0.5%.

Not verified: in-game drops at the new rate.

## What changes

The 48 Classic Hunt zones' family chances move from the compiled
`NightcapHunt::FamilyChance` (0.5%) to two columns on `nightcap_zone_hunt_zones`:
`augment_chance` and `gear_chance`, out of 10000. A MariaDB `CHECK` bounds both to
0–10000, so the zone code reads them as-is. Quality weights (60/30/8/2), the forge,
eligibility and sources are unchanged. Chapterhouse and Ashen Compact keep their own
separate 0.5% rolls.

Source of truth is `config/zone-hunt-rates.json` (a default plus per-zone
overrides keyed by short name). `tools/zone_hunt_rates.py` turns it into
[rates.sql](rates.sql), and `wiki/catalog.py` prints the same numbers on every zone
and item page. Never hand-edit the columns: the wiki would silently disagree.

## Defaults and kill math

Augment 1.5% (150), gear 0.5% (50, unchanged). One Ascension costs 48 Base copies
(3 → Polished, 4 → Exalted, 4 → Ascension); an average drop is worth 3.42 Base.

| Augment chance | Kills per drop | Kills per forged Ascension |
|---:|---:|---:|
| 0.5% (before) | 200 | ~2,800 |
| 1.5% (default) | ~67 | ~940 |

Balance: augment power arrives about three times sooner; item stats and caps are
unchanged. Encounter acceptance for Hunt rewards was already open and stays open.

## Activation

The deployed source differs from main's mirror; build from the deployed source plus
only this patch (`server-mods/code/zone/zone_hunt.cpp`,
`server-mods/code/common/zone_hunt_policy.h`).

1. Back up PEQ with the documented stopped-writer procedure.
2. Apply `rates.sql`. The ALTER is safe under the current binary, which ignores the
   new columns. It refuses to run if any of the 56 installed zone rows is missing.
3. Install the rebuilt zone and restart the whole game runtime through the
   supervisor (never single zones). Order matters: the new binary's config query
   needs the columns, and without them it disables Hunt drops in that zone.
4. Verify: every zone log still prints `Zone hunt [<zone>]: [N] approved native
   sources`, and `SELECT augment_chance,gear_chance,COUNT(*) FROM
   nightcap_zone_hunt_zones GROUP BY 1,2` returns `150 50 56`.
5. Rebuild and publish the wiki.

Retuning later: edit the config, regenerate (`python tools/zone_hunt_rates.py
--output docs/releases/<release>/rates.sql`), apply, restart the game runtime
(rates load at zone boot), publish the wiki. No rebuild.

## Rollback

Rates only: set the default back to 50/50, regenerate and apply, restart the
runtime. Binary: the previous image ignores the columns; leave them in place. Do not
drop the columns while the new binary runs.

## Evidence

- `tools/tests/test_zone_hunt_native.py`: the actual `Award` body compiled with
  `-Werror`, with new cases for a per-family chance (149 hits, 150 misses) and 0
  never dropping. A deliberate `>=`→`>` mutation fails it.
- `tools/tests/test_zone_hunt_rates.py`: all 56 rows rated, Hole is zone 39, every
  wiki slug is known, overrides merge, invalid values fail, committed SQL matches
  the config.
- `wiki/test_wiki.py`: Hole zone and item pages publish 1.5%/0.5%.
- Disposable MariaDB 10.5.4 rehearsal: apply and rerun both succeed (56 rows at
  150/50), 10001 is rejected by the CHECK, a missing zone row aborts the run.

Not yet verified: in-game drops at the new rate.
