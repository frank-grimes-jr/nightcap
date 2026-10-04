# Classic NPC shared-animation repair — October 4, 2026

Status: separately signed QA release **2026100402** is installed in an isolated
copy; not published or accepted in game. All 48 managed files verify. The source
baseline includes current main e37b7fa and its published winged helmet assets.

## Ready-to-play isolated candidate

Close the normal game, then open:
`E:/EQ_Local_Dev/artifacts/npc-animation-20261003/qa/Play animation QA.cmd`.
The script refuses to launch while another eqgame process is open. It uses its
sibling client and launcher-state folders, connects to the normal public login
server and leaves the console open while the game runs. Exit the game normally.
The normal E:/Nightcap and original Client_RoF2_Dev installations were not edited.

The signed updater installed all 48 files and reports `can_play=true` with
runtime health pending. Startup and in-game checks are intentionally unclaimed:
the normal game was running during preparation. [Verification](verification.json)
records the manifest, proxy and launcher hashes and native red/green evidence.

## Report and cause

The owner reports level-1/2 Enchanter pets shaking in every zone, at rest and
while moving/fighting, and fire beetles sliding without walking or rolling
over on death. No timing or server-state workaround was assumed.

The pinned RoF2 executable (SHA256
`2a8702ad9f722704f01355c0750be7d6f164a8b9c9128ba0cf286ea32b405b0e`)
resolves animation families at RVA `0x6A60`, called at `0x7985`. The function
copies its input and applies native prefix-based sharing. For example:

| Actor | Stock result | Prior alias result | Candidate result |
|---|---|---|---|
| Beetle BET / ZEC | SPI, false | ZEC, false | imported SPI alias ZCH, false |
| Invisible man IVM / ZBB | ELM, true | ZBB, false | native ELM, true |
| Typed water elemental WEL / ZQV | source skeleton is ELE | ZQV, false | ZQV, false |

The last row is deliberately resolved from the archive skeleton, rather than
the registry's WEL race code. All four typed elemental archives clone ELE.
The beetle archive has no BET action tracks. Imported ZCH in ncm03 contains
locomotion L02 and death D05 tracks, among others. The IVM archive likewise
relies on shared humanoid actions. Reversible renaming and intact frame bytes
did not preserve the native lookup contract.

## Change and boundaries

The existing classic-model feature installs a six-byte guarded entry trampoline
over three complete, position-independent instructions. Only known alias
inputs are translated. The original client routine still chooses the parent
and returns its flag; imported parents use their matching alias, while native
player families remain native. Modern mode and native input codes pass through.
The generated catalog records each imported model's actual source skeleton.
Asset digests, appearance mappings, geometry, textures and animation data remain
unchanged. No gameplay balance, pet commands, server binary or SQL is changed.

Proxy candidate: `0.7.6-dev`, with 71 pinned catalog sites. The proxy and catalog
must ship together through a new signed release. Keep normal production and
the original Client_RoF2_Dev installation intact until authorized publication.

## Verification

- Regression red: execute the unpatched native resolver with ZEC; the assertion
  for imported spider-family inheritance fails. The candidate passes.
- `model-animation-native.cpp` hashes the exact executable before mapping it,
  applies its HIGHLOW relocations in an isolated process, substitutes only the
  CRT string comparison, and runs the actual native routine through the new
  entry trampoline. It never runs the game entry point or loads the candidate
  into a player process. Covers 288 family/flag comparisons, modern/native
  passthrough, explicit beetle/Enchanter cases and typed elemental identity.
- x86 proxy and runtime fixtures build; all five runtime test groups pass.
- Exact-client verification and both generated contracts agree; launcher
  preflight and package tests pass.
- These checks prove the lookup repair, not rendered animation acceptance.

From `eq-client-dll/`, build with `build.bat` and
`tests/build-runtime-tests.bat`, then run `python tests/test_runtime.py` and
`build/tests/model-animation-native.exe <read-only eqgame.exe path>`.
Add `--unpatched` to replay the failing baseline (expected exit 1).
Local evidence and build experiments: `E:/EQ_Local_Dev/artifacts/npc-animation-20261003/`.

## Exact in-game QA before main/publication

Use the isolated candidate with classic defaults. Confirm its proxy log says
`0.7.6-dev` and `Model policy: classic defaults`.

1. In East Commonlands, summon the first two available Enchanter animation pets
   (the owner's reported tiers). Watch each standing still for 30 seconds,
   following, guarding, attacking a suitable low-level target, and backing off.
   Expect stable floating weapons and coherent attack motion, with no continuous
   shaking. Repeat after zoning to Plane of Knowledge and back, and after
   camping/reconnecting. Confirm pet commands and ownership still work.
2. Find a fire beetle in East Commonlands. Observe it roaming, chase it, then
   kill it. Expect moving legs while travelling and a normal death animation
   ending in the flipped corpse pose. Inspect the corpse and repeat after zoning.
3. Check the same idle/movement/attack/death sequence for a skeleton, wolf,
   kobold, griffin and spider in their native zones (East Commonlands;
   Steamfont for kobolds). The affected family includes other shared-animation
   models; do not treat two successful models as acceptance of all 144.
4. Summon earth/fire/water/air Magician pets. Preserve all four classic palettes,
   stable idle, follow, casting/attack and death animations. Check a Necromancer
   skeleton alongside the Enchanter pet on a legal multiclass build.
5. Exit fully, enable `[Nightcap] UseModernModels=TRUE` in this QA copy, restart
   and repeat the reported pet/beetle checks. Confirm native behavior is retained.
   Remove the opt-in and restart to return to classic defaults.

Record zone, pet spell/NPC name, proxy log identity and observed action for
each failure. Native runtime health alone does not close these checks.

## Promotion and recovery

Follow feature → dev → test, then owner in-game sign-off before main. Historical
September release exceptions do not authorize this new publication. A rollback
after publication must use a higher signed release containing the prior reviewed
proxy/catalog; never lower the release counter. An isolated QA candidate can be
closed without changing the normal installation. Preserve its evidence.
