"""Check that native encounter prototypes exercised real combat, not idle targets."""
import argparse
import json
from collections import Counter
from pathlib import Path


def verify(report, *, require_player_melee=False):
    encounter = report['encounter']
    state = encounter['initial_state']
    player,boss = encounter['player_entity_id'],encounter['npc_entity_id']
    assert player != boss and player and boss
    for key in ('zone_loaded','npc_ai','npc_engaged','npc_has_spells','can_combat',
                'npc_can_attack','player_can_attack'):
        assert state[key], f'Invalid initial state: {key}'
    assert state['npc_hate_target'] == player, 'Boss has no native hate target'
    assert not any(state[k] for k in ('player_dead','player_zoning','player_destroying'))
    trace = encounter['trace']
    assert trace[0]['npc_hp'] == 32000 and trace[0]['ms'] == 0
    assert any(s['player_hp'] < trace[0]['player_hp'] for s in trace), 'Player never took damage'
    assert any(s['npc_hp'] < 32000 for s in trace), 'Boss never took damage'
    assert any(s['npc_target'] == player for s in trace)
    events = encounter['events']
    def count(source,kind,spell,positive=False):
        return sum(e['source']==source and e['type']==kind and e['spell']==spell
                   and (not positive or e['damage'] > 0) for e in events)
    boss_melee = count(boss,'damage',65535,True)
    player_melee = count(player,'damage',65535,True)
    assert boss_melee > 0, 'Missing boss melee'
    if require_player_melee:
        assert player_melee > 0, 'Missing weapon-equipped player melee'
    spells = Counter(e['spell'] for e in events if e['source']==boss and e['type']=='begin_cast')
    breath = 861 if encounter['npc_id']==32040 else 952
    assert spells[breath] > 0 and spells[981] > 0, 'Missing native breath/roar casting'
    if encounter['npc_id']==73057:
        assert any(spells[s] for s in (13,1518,1519)), 'Missing Vox healing'
        assert trace[-1]['npc_mana'] < trace[0]['npc_mana'], 'Vox never consumed mana'
    assert encounter['result'] in ('timeout','player_death','npc_death')
    if encounter['result']=='player_death':
        assert trace[-1]['player_hp'] <= 0
    if encounter['result']=='npc_death':
        assert trace[-1]['npc_hp'] <= 0
    assert trace[-1]['ms']==encounter['elapsed_ms']
    return {'passed':True,'npc_id':encounter['npc_id'],'result':encounter['result'],
            'elapsed_ms':encounter['elapsed_ms'],'boss_positive_melee_events':boss_melee,
            'player_positive_melee_events':player_melee,'boss_casts':dict(spells),
            'sampled_fear_states':sum(s['feared'] for s in trace),
            'player_moved':any(s['player_position'] != trace[0]['player_position'] for s in trace),
            'scope':'Native combat activity control only; not certified BiS, optimal controller, full AA activation, or balance conclusion'}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--require-player-melee',action='store_true')
    args=parser.parse_args()
    result=verify(json.loads(args.native.read_text()),require_player_melee=args.require_player_melee)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__=='__main__':
    main()
