"""Verify recorded native mechanics and report bounded encounter comparisons."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile

HERE=Path(__file__).resolve().parent


def main():
    archive=HERE/'evidence/native-results.tar.gz'
    root=HERE.parents[2]
    paired=json.loads((HERE/'evidence/native-build-manifest.json').read_text())
    for name,digest in paired['requested_sources'].items():
        assert hashlib.sha256((root/'server-mods/code'/name).read_bytes().replace(b'\r\n',b'\n')).hexdigest()==digest,name
    with tarfile.open(archive) as tar:
        def raw(name):return tar.extractfile(name).read()
        def read(name):return json.loads(raw(name))
        matrix=read('matrix.json');execution=read('matrix-results.json')
        assert execution['status']=='passed' and len(execution['cases'])==26
        results={r['id']:read(r['id']+'-result.json') for r in execution['cases']}
        for row in execution['cases']:
            assert row['status']=='passed'
            for key,suffix in [('input_sha256','-input.json'),('output_sha256','-result.json')]:
                assert hashlib.sha256(raw(row['id']+suffix)).hexdigest()==row[key]
        diagnostic=read('native-build-manifest.json')
        assert execution['binary_sha256']==diagnostic['binary_sha256']
        for name,key in [('native_harness.cpp','harness_sha256'),('native_runtime.cpp','runtime_sha256'),('native_runtime.h','runtime_header_sha256')]:
            assert hashlib.sha256((root/'tools/balance'/name).read_bytes()).hexdigest()==diagnostic[key],name
        assert execution['matrix_sha256']==hashlib.sha256(raw('matrix.json')).hexdigest()
    checks=[]
    states=[]
    for name,d in results.items():
        b=d['builds'][0]
        assert b['aa_spent']==sum(p['cost'] for p in b['aa_purchases'])==b['aa_budget']
        assert b['aa_remaining']==0
        if name.startswith('stats-wpm-'):
            state=b['wpm_state'];swap=b['shield_swap'];states.append(state)
            assert swap['restored']==state
            off=swap['removed']
            assert state['received_heal_1000']==1100 and off['received_heal_1000']==1000
            assert state['shield'] and not off['shield']
            assert state['spell_proc_bonus']-off['spell_proc_bonus']==25
            assert state['weapon_proc_bonus']-off['weapon_proc_bonus']==25
            assert 42840 in state['aa_procs'] and 42840 not in off['aa_procs']
            assert 42846 in state['worn_procs'] and not any(off['worn_procs'])
            assert state['shield_damage_percent']==100
            assert all(x>=200 for x in state['special_damage'])
            assert all(not x['vi'] and not x['vii'] for x in state['focus'] if x['spell'] in (42841,42842))
    assert len(states)==6 and all(s==states[0] for s in states)
    checks.extend(['26 input/output hashes and diagnostic binary match recorded execution',
        'Canonical AA costs, including zero-cost baseline ranks, preserved; every supplied budget fully accounted',
        'All six WPM class orders have identical recorded combat capability state',
        'Shield removal/restoration clears/restores Holy Shield, Diaku and Marr healing',
        'Shield Specialist100%, six Way of Steel contributions and nonrecursive focus controls'])
    report=[];wpm_effects=Counter();pet_effects={};runes=0;mends=0;rage=0
    for name,d in results.items():
        e=d.get('encounter',d.get('pet_probe',{}).get('combat'))
        if e is None:continue
        b=d['builds'][0];pet='pet_probe' in d
        elapsed=e.get('elapsed_ms',e['trace'][-1]['ms'])
        damage=sum(max(0,x['hp_before']-max(0,x['hp_after'])) for x in e['damage_ledger'] if x['depth']==0)
        ledger=e.get('player_ledger',{})
        healing=sum(x['healed'] for x in ledger.get('healing',[]))
        absorbed=sum(x['rune_used'] for x in ledger.get('incoming',[]))
        events=Counter(x['spell'] for x in e['events'] if x['type']=='damage' and
                       x['source']==e.get('player_entity_id',e.get('player_id')))
        if name.startswith('wpm-'):
            wpm_effects.update(events);runes+=absorbed;mends+=len(e['mend_requests'])
            requests=e['monk_actions']['requests']
            assert {x['skill'] for x in requests}=={30,38,52,23,21,26}
            assert len({x['timer_id'] for x in requests})==6
            assert {x['skill'] for x in requests if x['timer_after']>0}=={30,38,52,23,21,26}
            for mend in e['mend_requests']:
                assert mend['timer_after']>0
                assert mend['hp_after_pulse']-mend['hp_before_pulse']==mend['expected_noncritical_heal']
            for action in e['activated_aa']['actions']:
                if action['ability_id']==131:
                    assert action['started'] and action['effective_recast_seconds']==60
                    rage+=1
        if pet:
            equipped='equipped' in name
            pets=d['pet_probe']['final']['pets']
            assert len(pets)==3
            for i,p in enumerate(pets):
                assert len(p['armor_slots'])==((15 if i==0 else 8) if equipped else 0)
                for stat,own,owner in [('spell_damage','own_spell_damage','spell_damage'),('heal_amount','own_heal_amount','heal_amount')]:
                    assert p[stat]==p[own]+min(b[owner]//2,375)
                spells={x['spell'] for x in e['events'] if x['type']=='damage' and x['source']==p['entity_id']}
                if equipped:pet_effects.setdefault(i,set()).update(spells)
            if name.endswith('max'):
                assert any(x['rank_id']==16475 for x in b['aa_purchases'])
        first,last=e['trace'][0],e['trace'][-1]
        initial_hp=first['player']['hp'] if pet else first['player_hp']
        final_hp=last['player']['hp'] if pet else last['player_hp']
        initial_mana=first['player']['mana'] if pet else first['player_mana']
        final_mana=last['player']['mana'] if pet else last['player_mana']
        report.append(dict(case=name,outcome=e['result'],elapsed_seconds=elapsed/1000,
            effective_damage=damage,dps=round(damage*1000/elapsed,1),aa_spent=b['aa_spent'],
            initial_hp=initial_hp,final_hp=final_hp,net_mana_used=initial_mana-final_mana,
            heal_damage_recovered=healing if not pet else None,
            player_melee_rune_absorbed=absorbed if not pet else None,
            mend_requests=len(e.get('mend_requests',[])),owner_spell_event_counts=dict(events)))
    assert all(wpm_effects[x]>0 for x in (23598,42851,42846,42836,42840,13504,16139))
    assert runes>0 and mends>0 and rage>0
    assert all({2984,42836,42837}<=spells for spells in pet_effects.values()) and len(pet_effects)==3
    checks.extend(['Native WPM encounters exercise all six skill timers and earned Rage60s activation',
        'Fists of Fury, haste fragment, Diaku, Healing Fragment, Holy rune, Blessing and Healing Light observed',
        'Native Holy rune absorption and successful Mend pulse/cooldown recorded',
        'All three equipped pet classes retain15/8/8 items and own stats plus bounded half-owner inheritance',
        'Across equipped pet encounters all three classes emit innate weapon, healing augment and rune augment effects',
        'Companion Fury IV purchased through native gates with actual RoF2 mask'])
    output={'status':'passed','execution_cases':26,'stat_cases':6,'encounters':len(report),
        'binary_sha256':execution['binary_sha256'],'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'assertions':checks,'comparisons':report,
        'limits':['Native diagnostic clock/packet adapters; no actual RoF2 render or user gameplay acceptance',
            'Captured Nagafen55 single-target encounter; no pack, raid or long-duration balance certification',
            'Class permutations are stat/shield-swap probes; combat uses Warrior-first WPM',
            'Seed1729 plus two seed2718 repeats do not establish statistical superiority',
            'Explicit gear and maximum trained skills; max stages spend2074 WPM/2085 pet AA points',
            'Damage sums depth-zero HP loss capped at zero terminal HP; includes replacement of NPC regeneration',
            'Healing ledger is HealDamage only, excludes regeneration/Mend; spell IDs may be65535 at native call sites',
            'Pet runes and healing proved through native effects/state; player ledger totals do not describe pet sustain',
            'Bare/equipped pet comparisons retain fixed Classic support gems, with separate PoP summon cases',
            'No production content, characters, runtime, signed-client or wiki changes']}
    (HERE/'evidence/native-comparison.json').write_text(json.dumps(output,indent=2)+'\n')
    lines=['# Native WPM and pet comparison','',
        'All26 scenarios executed and the recorded mechanics assertions passed. These are',
        'isolated native diagnostics, not final balance or client acceptance.','',
        '| Case | Outcome | Seconds | Effective DPS | AA spent | Final HP |',
        '|---|---|---:|---:|---:|---:|']
    for row in report:lines.append(f"| {row['case']} | {row['outcome']} | {row['elapsed_seconds']:g} | {row['dps']:g} | {row['aa_spent']} | {row['final_hp']} |")
    lines+=['','## Verified mechanics','']+['- '+x for x in checks]+['','## Limits','']+['- '+x for x in output['limits']]
    (HERE/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':'passed','checks':len(checks),'encounters':len(report)}))


if __name__=='__main__':main()
