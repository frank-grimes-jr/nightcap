# QA activation evidence — September 20, 2026

Active on the development server; manual acceptance and main promotion remain
pending. Feature commits: `30a4ea2` (retirement/recovery), `daf5b06` (hub). The
candidate was promoted through dev/test; main remains `b620beb`.

- Full verified backup: SHA256 `5cf899245ea4297465912f2100bb7c13644d7403194d494ec4fd67aa74b141c4`,
  46,395,786 compressed / 441,569,249 uncompressed bytes.
- All zones exited gracefully before final capture. No forced zone termination.
- Exact stopped-server `hub-v4` rehearsal: **28 passed checks**,
  disposable schema removed. Forward normalized SQL SHA256
  `0c4a5fcc93c56e040cacfca8a2afd1656122ddc1b31943c6980190482f20dce3`; immediate rollback
  `03db6888501fa0e827db0c6307a3b89308da28291296d84f5d6b4bcb6dba0673`.
- Applied rows match the complete expected afterimage. All nine checked player
  tables have unchanged row counts and SHA256 fingerprints: characters, binds,
  AA ownership, multiclass, inventory, pet info/buffs/inventory/armor.
- Existing class merchants retain **1747 listings / 1229 unique items**. Original
  20 door templates, merchant definitions, appearance and stock remain intact.
- Shared memory regenerated. World PID67074 and all eight zone PIDs were verified
  at 2026-09-20T12:28:44.363932+00:00. Seven installed code/quest files match their source.
  Fourteen current startup logs contain **zero Error/Fatal lines**.
- World SHA256 `f7db30da4c3c337637b6a42dce82dc0290818e7c692584652a4bb99fc13149cd`.
  Zone SHA256 `503578413dfaaa4a9acc57499d9f53bb073b96d35aa2e4ac602ae2dd977912a6`.
- Classic expansion0, AA minimum1 and saved-state policy remain unchanged.

Client release **2026092002** has20signed files plus one pinned retirement. The
separate QA copy completed installation and verified all20hashes. Actual client
startup reported proxy0.4.2, ready, all12required features active (mask4095).
Original `Client_RoF2_Dev` files were not changed by this activation.

Launcher: `E:/EQ_Local_Dev/artifacts/ecommons-hub-20260920/launcher/nightcap-launcher-qa.exe`.
SHA256 `1cc2b19b4fcc42feb4d2da8d6c07a88ba9e63133fa15028b6a9486021258dd4d`. The old launcher at the usual `launcher-final`
location remains open and Windows refused replacement; use this new executable
until that process is closed. Previous executable was copied to the release's
`usual-launcher-before` directory before the attempted replacement.

Verification includes both normal and qacandidate Go suites,12client Python tests,
2hub policy tests, five Perl syntax checks, successful native zone and Wails builds,
grounded service/portal footprints and clear paths for all ten return approaches.
Independent review found and resolved AA visibility/hotkey, topology, retirement
race and interrupted-recovery defects. No remaining code-review blocker was reported.

These are automation/startup checks. They do not establish in-game rendered models,
click behavior, travel, recall cooldown, new-character starts or pet transitions.
Run [the exact owner QA checklist](README.md) before promotion to main.

Local full evidence: `E:/EQ_Local_Dev/artifacts/ecommons-hub-20260920/activation/`.
Post-activity rollback requires a fresh scoped capture; see the release checklist.
