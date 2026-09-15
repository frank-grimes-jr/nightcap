"""Verify full native self-cast processing against the pinned direct-action control."""
import argparse
import json
from pathlib import Path


def verify(report, direct):
    probe = report['runtime_probe']
    if len(report['builds']) != 1:
        raise ValueError('Runtime control requires one build')
    build = report['builds'][0]
    keys = ('profile','tier','aa_stage','aa_policy')
    matches = [b for b in direct['builds'] if all(b.get(k) == build.get(k) for k in keys)]
    if len(matches) != 1 or build['aa_spent'] != 0:
        raise ValueError('Expected the pinned zero-spend control')
    spells = [p for p in matches[0]['spell_probes'] if p['spell_id'] == 9]
    if len(spells) != 1 or len(spells[0]['outcomes']) != 1:
        raise ValueError('Self-heal control needs a deterministic direct-action reference')
    action = spells[0]['outcomes'][0]
    clock = probe['clock']
    assert clock == {'at_1000_persistent':True,'at_1000_timer':False,
                     'at_1001_timer':True,'at_2000_persistent':True,
                     'seconds':1789171201,'time':1789171201}, 'Clock boundaries differ'
    assert probe['connected'] and probe['client_version_bit'] == 64
    assert probe['cast_accepted'] and probe['outgoing_packets'] > 0
    trace = probe['trace']
    start = trace[1]
    assert start['casting'] == 9 and start['mana'] == trace[0]['mana'] == build['mana']
    completion = next(s for s in trace[2:] if s['casting'] == 0)
    assert completion['ms'] - start['ms'] == action['cast_ms'] + 50, 'Native cast deadline differs'
    assert completion['hp'] - start['hp'] == action['amount'], 'Healing differs from direct native control'
    assert start['mana'] - completion['mana'] == action['mana'], 'Completion mana differs'
    for row in trace[2:]:
        if row['ms'] < completion['ms']:
            assert row['casting'] == 9 and row['hp'] == start['hp'] and row['mana'] == start['mana']
    assert trace[-1]['hp'] > completion['hp'] and trace[-1]['mana'] > completion['mana'], 'Missing native regeneration'
    damage = probe['damage_control']
    assert damage['client_finished_loading']
    assert damage['hp_before'] == trace[-1]['hp']
    assert damage['hp_before'] - damage['hp_after'] == damage['requested_damage'] == 100, 'Login protection or unexpected mitigation'
    return {'passed':True,'cast_finished_ms':completion['ms'],
            'heal_amount':action['amount'],'mana_spent':action['mana'],
            'post_cast_hp_regen':trace[-1]['hp']-completion['hp'],
            'post_cast_mana_regen':trace[-1]['mana']-completion['mana'],
            'damage_taken':100,'scope':'Native connected Client::Process clock/cast/resource/damage control; not a boss balance result'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--direct',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    result = verify(json.loads(args.native.read_text()),json.loads(args.direct.read_text()))
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
