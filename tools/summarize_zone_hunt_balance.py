"""Validate paired native stat diagnostics and render the measured balance table."""
import argparse
import json
from pathlib import Path


def summarize(release):
    builds = json.loads((release / 'balance-results.json').read_text())['builds']
    assert len(builds) == 24
    rows = []
    for baseline, augmented in zip(builds[::2], builds[1::2]):
        assert baseline['profile'] == augmented['profile']
        assert baseline['tier'].endswith('/ baseline') and augmented['tier'].endswith('/ augmented')
        assert all(b['aa_spent'] == b['aa_budget'] == 0 for b in (baseline, augmented))
        assert [(x['slot'], x['id']) for x in baseline['equipped_items']] == [(x['slot'], x['id']) for x in augmented['equipped_items']]
        assert sum(len(x['augments']) for x in baseline['equipped_items']) == 0
        assert sum(len(x['augments']) for x in augmented['equipped_items']) == 6
        assert all(augmented[key] <= 280 for key in ('spell_damage', 'heal_amount'))
        assert baseline['ac_sum'] == augmented['ac_sum']
        tier = baseline['tier'].split(' / ')[0].replace('Ascended', 'Ascension')
        hp = 100 * (augmented['hp'] / baseline['hp'] - 1)
        mana = 100 * (augmented['mana'] / baseline['mana'] - 1)
        rows.append(f"| {baseline['profile']} | {tier} | {baseline['hp']:,} → {augmented['hp']:,} (+{hp:.1f}%) | {baseline['mana']:,} → {augmented['mana']:,} (+{mana:.1f}%) | {baseline['spell_damage']} → {augmented['spell_damage']} | {baseline['heal_amount']} → {augmented['heal_amount']} |")
    text = '''# Native equipped-stat measurements

The isolated native engine evaluated 24 synthetic level-50 loadouts: three multiclass profiles, four gear qualities, and identical equipment before/after six band-6 augments of matching quality. These are endgame augment controls even in the Base gear row; they do not represent a low-level character. Every profile spent **0 AA**, with no active buffs or pets. The captured production cap rules were applied to a content-only local PEQ fixture; no production player rows were copied.

Warrior/cleric/wizard and magician/necromancer/shaman use six Abyssal Thoughtpearls (heroic INT/STA). Warrior/cleric/monk uses six Ghoulheart Opals (heroic WIS/STA). The raw diagnostic calls the legacy top gear tier `Ascended`; the table uses the approved new-item label `Ascension`.

| Classes | Quality | HP before → after | Mana before → after | Spell Damage | Healing Amount |
|---|---|---:|---:|---:|---:|
'''
    text += '\n'.join(rows) + '''

The equipped AC sum did not change in these selected augment profiles. Other catalog profiles with AC, avoidance, shielding, regeneration or different heroics require their own encounter checks. Spell Damage/Healing Amount reached 280 at the top tier as designed. The focused native cap tests separately verify that headroom never grants missing raw stats and that level, recommended scaling and eligibility gates apply.

Six endgame augments add roughly 23–38% HP and 25–32% mana in these zero-AA controls. That is material combined power, including native heroic effects, even though the output cap increase is bounded. The approved values are retained for test QA; these results do **not** establish acceptable solo encounter difficulty. Before main, compare legal-AA builds, pet contribution, healing/sustain, resource use, failure rates and kill times using the exact encounters in [QA.md](QA.md). No NPC HP or additional cap tuning has been applied to conceal the gain.

Evidence: [inputs](balance-inputs.json), [raw results](balance-results.json), [fixture scope](balance-setup.json), [diagnostic build](balance-build-manifest.json). Reproduce this table with `python tools/summarize_zone_hunt_balance.py --release docs/releases/zone-loot-20261009`. The diagnostic links the actual candidate zone objects; it is not installed as a game server.
'''
    (release / 'BALANCE.md').write_text(text, encoding='utf-8')
    print('Validated 12 paired native measurements and wrote BALANCE.md')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--release', type=Path, required=True)
    summarize(p.parse_args().release)
