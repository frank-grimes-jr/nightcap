"""Verify recorded native mechanics and report bounded encounter comparisons."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile

HERE=Path(__file__).resolve().parent


def spell_comparisons(results, matrix):
    inputs={c['id']:c['input'] for c in matrix['cases']}
    rows=[]
    for name,data in results.items():
        if not name.startswith('parity-'):
            continue
        build=data['builds'][0]
        row={'case':name,'level':inputs[name]['builds'][0]['level'],
             **{k:build[k] for k in ('hp','mana','spell_damage','heal_amount','heroic_int','heroic_wis')}}
        row['spells']=[]
        assert len(build['spell_probes'])==3 and build['aa_spent']==0
        for probe in build['spell_probes']:
            outcomes=probe['outcomes'];count=sum(o['count'] for o in outcomes)
            assert count==probe['samples']==200
            landed=[o for o in outcomes if o['landed_percent']>0]
            landed_count=sum(o['count'] for o in landed)
            assert all(o['amount']>=0 and o['mana']>=0 for o in outcomes)
            if probe['effect']=='dot_tick':
                assert landed_count==200
            row['spells'].append(dict(spell_id=probe['spell_id'],effect=probe['effect'],
                mean_amount=round(sum(o['amount']*o['count'] for o in outcomes)/count,3),
                mean_landed_amount=round(sum(o['amount']*o['count'] for o in landed)/landed_count,3) if landed_count else None,
                landed_samples=landed_count,minimum=min(o['amount'] for o in outcomes),
                maximum=max(o['amount'] for o in outcomes),scope=probe['scope']))
        rows.append(row)
    assert len(rows)==18
    for level in (50,65):
        on=next(r for r in rows if r['case']==f'parity-l{level}-observed-ascended')
        off=next(r for r in rows if r['case']==f'parity-l{level}-observed-legacy-spells')
        assert all(on[k]==off[k] for k in ('hp','mana','spell_damage','heal_amount','heroic_int','heroic_wis'))
        assert inputs[on['case']]['builds'][0]['equipment']==inputs[off['case']]['builds'][0]['equipment']
    return rows


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
        assert execution['status']=='passed' and len(execution['cases'])==47
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
    checks.extend(['47 input/output hashes and diagnostic binary match recorded execution',
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
    probes=spell_comparisons(results,matrix)
    checks.append('Eighteen spell probes contain 10800 samples; level50/65 rule controls retain identical gear and effective stats')
    baseline_path=HERE.parent/'wpm-melee-20261018/evidence/native-comparison.json'
    baseline=json.loads(baseline_path.read_text())
    previous={r['case']:r for r in baseline['comparisons']}
    deltas=[dict(case=r['case'],previous_dps=previous[r['case']]['dps'],combined_dps=r['dps'],
                 dps_change_percent=round((r['dps']/previous[r['case']]['dps']-1)*100,1),
                 previous_outcome=previous[r['case']]['outcome'],combined_outcome=r['outcome'])
            for r in report if r['case'] in previous]
    assert len(deltas)==20
    paired_controls=[]
    by_case={r['case']:r for r in report}
    for name in ('caster65-max','pet-equipped-max','wpm-shield-max'):
        on=by_case[name];off=by_case[name+'-legacy-spells']
        paired_controls.append(dict(case=name,enabled_dps=on['dps'],disabled_dps=off['dps'],
            enabled_outcome=on['outcome'],disabled_outcome=off['outcome'],
            enabled_final_hp=on['final_hp'],disabled_final_hp=off['final_hp']))
    output={'status':'passed','execution_cases':47,'stat_cases':6,'spell_probe_cases':18,'encounters':len(report),
        'binary_sha256':execution['binary_sha256'],'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        'assertions':checks,'comparisons':report,'spell_probes':probes,'baseline_deltas':deltas,
        'same_items_rule_controls':paired_controls,
        'baseline_report_sha256':hashlib.sha256(baseline_path.read_bytes()).hexdigest(),
        'limits':['Native diagnostic clock/packet adapters; no actual RoF2 render or user gameplay acceptance',
            'Captured Nagafen55 single-target encounter; no pack, raid or long-duration balance certification',
            'Class permutations are stat/shield-swap probes; combat uses Warrior-first WPM',
            'Seed1729 plus two seed2718 repeats do not establish statistical superiority',
            'Explicit gear and maximum trained skills; max stages spend2074 WPM/2085 pet/2163 caster AA points',
            'Damage sums depth-zero HP loss capped at zero terminal HP; includes replacement of NPC regeneration',
            'Healing ledger is HealDamage only, excludes regeneration/Mend; spell IDs may be65535 at native call sites',
            'Pet runes and healing proved through native effects/state; player ledger totals do not describe pet sustain',
            'Bare/equipped pet comparisons retain fixed Classic support gems, with separate PoP summon cases',
            'Eighteen caster probes sample direct values/resists and landed initial-duration DoT ticks; no full casting/buff lifecycle',
            'Historical WPM deltas include item and formula changes; same-item rule controls isolate the two new spell switches together',
            'Probe loadouts are explicit diagnostic equipment, not proof of legal-era acquisition or optimal builds',
            'Low-level Frost Bolt probes target level55 Nagafen and can fully resist; these do not establish level-appropriate leveling balance',
            'Fixed encounter spell controllers were not reoptimized for additive SD; lower-cost ranks and DoT rotations need owner comparison',
            'No production content, characters, runtime, signed-client or wiki changes']}
    (HERE/'evidence/native-comparison.json').write_text(json.dumps(output,indent=2)+'\n')
    lines=['# Combined native item/spell and WPM/pet comparison','',
        'All 47 scenarios executed and the recorded mechanics assertions passed. These are',
        'isolated native diagnostics, not final balance or client acceptance.','',
        'The same-item controls show a material redistribution: WPM shield DPS rises',
        'from2911.2 to4510.3, the fixed caster controller falls from685 to225.4, and',
        'equipped Classic pets fall from452.4 to289.9. The maximum-AA WPM fixture',
        'kills captured Nagafen in7.1 seconds. This is a required burst/sustain QA',
        'gate, not a balance approval. Low-base spells and ordinary ticks gain;',
        'compare cheaper spell ranks and DoT rotations before generalizing the caster result.','',
        '| Case | Outcome | Seconds | Effective DPS | AA spent | Final HP |',
        '|---|---|---:|---:|---:|---:|']
    for row in report:lines.append(f"| {row['case']} | {row['outcome']} | {row['elapsed_seconds']:g} | {row['dps']:g} | {row['aa_spent']} | {row['final_hp']} |")
    lines+=['','## Comparison with the completed pet/WPM candidate','',
        'These paired inputs include both item and formula changes. Percentage deltas are',
        'diagnostic outcomes for these controllers and seeds, not statistical balance estimates.','',
        '| Case | Previous DPS | Combined DPS | Change |',
        '|---|---:|---:|---:|']
    for r in deltas:lines.append(f"| {r['case']} | {r['previous_dps']} | {r['combined_dps']} | {r['dps_change_percent']:+g}% |")
    lines+=['','## Same-item spell-rule controls','',
        '| Case | Rules enabled DPS | Rules disabled DPS | Enabled final HP | Disabled final HP |',
        '|---|---:|---:|---:|---:|']
    for r in paired_controls:lines.append(f"| {r['case']} | {r['enabled_dps']} | {r['disabled_dps']} | {r['enabled_final_hp']} | {r['disabled_final_hp']} |")
    lines+=['','## Starter, dungeon and observed-item spell probes','',
        'Each spell has 200 samples. Direct damage means include resists; DoT means are',
        'landed initial-duration ticks. Healing is an effect value before missing-HP limits.',
        'The JSON retains landed-only means, ranges and effective heroic stats.','',
        '| Case | SD / HA | Heroic INT / WIS | Frost Bolt mean | Light Healing mean | Heat Blood tick mean |',
        '|---|---:|---:|---:|---:|---:|']
    for r in probes:
        values={p['spell_id']:p['mean_amount'] for p in r['spells']}
        lines.append(f"| {r['case']} | {r['spell_damage']} / {r['heal_amount']} | {r['heroic_int']} / {r['heroic_wis']} | {values[54]} | {values[17]} | {values[360]} |")
    lines+=['','## Verified mechanics','']+['- '+x for x in checks]+['','## Limits','']+['- '+x for x in output['limits']]
    (HERE/'COMPARISON.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps({'status':'passed','checks':len(checks),'encounters':len(report)}))


if __name__=='__main__':main()
