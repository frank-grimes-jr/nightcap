# Production zone build

The stock worn ATK production receipt records zone SHA-256 `a0506a169cd2481350f02b24468230825c52cd003936042f15d21b8addff7823`. The Nov 12 raid release retained the matching source, objects, libraries, compiler command lines and shipping binary in the local game container under `/tmp/nightcap-raid-augments-shipping-20261112-v3`. The unmodified Ninja link reproduced its original 53,374,232-byte unstripped ELF. GNU `objcopy --strip-debug` reproduced the deployed ELF byte for byte. The four untouched translation units independently recompiled to their original object hashes. [Build receipt](build.json) · [144 reference link inputs](link-inputs.json)

The shipping source applies the seven tested native diffs from `862eb1ac..dceb54bd` to those retained files with GNU patch at zero fuzz. The offsets in `spells.cpp` and `spell_effects.cpp` preserve intervening production changes. A new PCH compiled against the candidate headers. Clang rebuilt `mob.cpp`, `spells.cpp`, `spell_effects.cpp` and `special_attacks.cpp` with the parent’s security, Perl, Lua and optimization flags. The final link used all the other retained inputs. The shipping ELF is 53,331,744 bytes with SHA-256 `b462f5fce2f6e2a38e25ec4d3eda81c9efac16b59f39c764fa5a4d1bdd52d7f2`. Its dynamic libraries resolve, with the same dependency names as its parent. The release payload uses this zone alongside the retained world and shared-memory loader.

The Mob header adds nonvirtual method declarations and a forward declaration. The compiled sizes of Mob, Client and NPC match the parent. The shipping-header cache probe returned an item size of 1,332 bytes and spell size of 1,088 bytes, together with the six item offsets used in cache verification. [Actor sizes](actor-layout.json) · [Cache layout](layout.json)

## Reproduce locally

From the release checkout, run `python -B docs/releases/sympathetic-clicks-20261113/native/stage.py`. This reads the feature delta from the recorded Git revisions and copies the inputs to `/tmp/nightcap-sympathetic-shipping-20261113` inside `akk-stack-eqemu-server-1`. Run the following commands from that directory inside the container.

```sh
python3 build.py
python3 verify_layout.py
python3 verify_actor_layout.py
SYMPATHETIC_ZONE="$PWD/source/zone" python3 -B -m unittest -v test_sympathetic_cast
python3 cast_probe.py build
```

The two cast regression tests passed against the seven overlaid production sources. They compile and run the fixture for cast outcomes and check delivery receipts against the retained engine’s target, resist, worn proc, HP and periodic-effect code. The separate engine probe uses the four shipping objects and replaces the zone entry point with a fixture-bound diagnostic entry. It disables the world and QueryServ connections and enforces the fixture database identity before running the engine.

The engine probe equipped and clicked the real Ascended Moonstone Ring and Runed Lava Pendant, waited for each buff and removed each item. With matched random state, Minor Healing restored 21 HP before the ring click and 22 HP afterward. Ice Comet dealt 1,058 then 1,106 damage with 250 worn Spell Damage. This exercised the 5% floor for a small heal and the 48-point limit on a large hit. Both post-click casts ran after the user’s synthetic character unequipped the item. [Native cast result](cast.json)

For the engine replay, use the previously documented disposable MariaDB 10.11 content fixture. Create `nightcap-sympathetic-balance` on `akk-stack_backend` with `nightcap.fixture=sympathetic-classic`, at least 2.5 GiB of tmpfs at `/var/lib/mysql`, local-only root, the database `nightcap_sympathetic_balance` and zero published ports. Run the two host preparation commands from the feature’s balance instructions. They require the pinned September 21 offline dump, consume allowlisted game-content rows, and leave account and character tables empty. Run `python3 cast_probe.py run` from the shipping directory. It generates fresh item and spell caches with the production loader. [Disposable fixture preparation](../../../items/sympathetic-clicks/balance/README.md)

On the host, `python -B docs/releases/sympathetic-clicks-20261113/native/collect.py shipping` checks the copied zone and places it under `artifacts/sympathetic-prod/zone`. Run the same command with `cast` to export the synthetic click results. Interactive client display, player casts and encounter acceptance are separate player checks.
