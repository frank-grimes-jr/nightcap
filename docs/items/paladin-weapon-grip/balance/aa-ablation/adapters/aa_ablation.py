"""Local-only whole-AA ablation. Uses unchanged native binary and original fixtures."""
from pathlib import Path
import json,gzip,copy,hashlib,subprocess,time,argparse
import run_matrix as base
from setup_database import DB,SERVER,RUNTIME,sql,insert,run
HERE=Path(__file__).resolve().parent
OUT=HERE/'aa-ablation';OUT.mkdir(exist_ok=True)
RESULTS=OUT/'results';RESULTS.mkdir(exist_ok=True)
FIXTURES=OUT/'fixtures';FIXTURES.mkdir(exist_ok=True)
public=json.loads(gzip.decompress((HERE/'public-combat-reference.json.gz').read_bytes()))['tables']
def table(name):return [dict(zip(public[name]['columns'],r)) for r in public[name]['rows']]
abilities={r['name']:r for r in table('aa_ability')}
WU=abilities['[MNK] Technique of Master Wu']['first_rank_id']
STEEL=abilities['[MNK] Way of Steel']['first_rank_id']
assert WU==611
ARMS={'baseline':set(),'wu_off':{WU},'steel_off':{STEEL},'both_off':{WU,STEEL}}
EXPECTED_BINARY='88de63cddae472679f944f04df3662e508c4af125994d0f05adb03b20df8eb47'

def reset(arm):
    queries=['START TRANSACTION;']
    for table,key in [('character_skills','id'),('character_alternate_abilities','id'),('character_spells','id'),('character_memmed_spells','id'),('character_buffs','character_id')]:
        queries.append(f'DELETE FROM `{DB}`.`{table}` WHERE `{key}`=1;')
        rows=base.private[table]
        if table=='character_alternate_abilities':rows=[r for r in rows if r['aa_id'] not in ARMS[arm]]
        queries.extend(insert(table,{**r,key:1}) for r in rows)
    queries.extend([f'DELETE FROM `{DB}`.timers WHERE char_id=1;','COMMIT;'])
    sql('\n'.join(queries))
    actual=sql(f'SELECT aa_id FROM `{DB}`.character_alternate_abilities WHERE id=1 ORDER BY aa_id;')
    assert {int(v) for v in actual.splitlines()}=={r['aa_id'] for r in base.private['character_alternate_abilities']}-ARMS[arm]

def make(c,arm,mode,pulse):
    payload=json.loads((HERE/'fixtures'/(c['id']+'-'+mode+'.json')).read_text())
    modified=copy.deepcopy(c)
    expected=[r for r in c['build']['saved_aa'] if r['aa_id'] not in ARMS[arm]]
    modified['build']['saved_aa']=expected
    payload['builds'][0]['saved_aa']=expected
    if mode=='combat':payload['encounter']['pulse_ms']=pulse
    return payload,modified

def execute(c,arm,mode='combat',seed=101,pulse=32,suffix=''):
    payload,modified=make(c,arm,mode,pulse)
    label=f"{arm}-{c['id']}-{mode}-{seed}-{pulse}{suffix}"
    fixture=FIXTURES/(label+'.json');dest=RESULTS/(label+'.json')
    if dest.exists():raise RuntimeError('Refusing to overwrite retained ablation '+label)
    fixture.write_text(json.dumps(payload,indent=2)+'\n')
    reset(arm)
    run(['docker','cp',str(fixture),SERVER+':'+RUNTIME+'/ablation-input.json'])
    start=time.monotonic()
    p=subprocess.run(['docker','exec','-e',f'NIGHTCAP_BALANCE_RNG_SEED={seed}','-w',RUNTIME,SERVER,RUNTIME+'/balance-zone','tests:balance',RUNTIME+'/ablation-input.json',RUNTIME+'/ablation-output.json'],capture_output=True)
    (RESULTS/(label+'.log')).write_bytes(p.stdout+p.stderr)
    if p.returncode:raise RuntimeError('Native ablation failed: '+label+'\n'+(p.stdout+p.stderr).decode(errors='replace')[-2500:])
    run(['docker','cp',SERVER+':'+RUNTIME+'/ablation-output.json',str(dest)])
    data=json.loads(dest.read_text());b=base.validate(modified,data)
    old=json.loads((base.RESULTS/f"{c['id']}-stats-101-32.json").read_text())['builds'][0]
    assert b['fixture_state']==old['fixture_state'],('Unexpected fixture state change',label)
    before={r['first_rank']:r for r in old['aa_purchases']}
    after={r['first_rank']:r for r in b['aa_purchases']}
    assert after=={k:v for k,v in before.items() if k not in ARMS[arm]},('Unrelated active AA changed',label)
    expected_wpm=copy.deepcopy(old['wpm_state'])
    if STEEL in ARMS[arm]:expected_wpm['special_damage']=[v-200 for v in expected_wpm['special_damage']]
    assert b['wpm_state']==expected_wpm,('Unexpected AA bonus projection',label)
    for k,v in old.items():
        if k not in ['aa_purchases','wpm_state','final_fixture_state']:assert b[k]==v,('Unrelated initial stat changed',label,k)
    if mode=='combat':
        e=data['encounter'];initial=e['initial_state'];trace=e['trace']
        assert e['result'] in ['npc_death','player_death','timeout']
        assert (e['npc_id'],e['pulse_ms'],data['native_rng_seed'])==(73057,pulse,seed) and data['native_seed_hook_calls']>0
        assert all(initial[k] for k in ['zone_loaded','npc_ai','npc_engaged','can_combat','npc_can_attack','player_can_attack','npc_has_spells'])
        assert not any(initial[k] for k in ['player_zoning','player_destroying','player_dead'])
        assert initial['npc_hate_target']==e['player_entity_id']
        assert trace[0]['npc_hp']==32000 and trace[0]['player_hp']==b['hp'] and trace[0]['player_mana']==b['mana']
        assert 0<trace[-1]['ms']-trace[0]['ms']<=900000 and e['damage_ledger'] and e['player_ledger']['incoming']
        if arm=='baseline':
            old_run=json.loads((base.RESULTS/f"{c['id']}-combat-{seed}-{pulse}.json").read_text())
            assert old_run==data,('Baseline replay drift',label)
    else:e={}
    print(json.dumps({'case':label,'wall_s':round(time.monotonic()-start,2),'result':e.get('result','stats_pass'),'seconds':e.get('elapsed_ms',0)/1000}),flush=True)
    return data

def preflight():
    actual=run(['docker','exec',SERVER,'sha256sum',RUNTIME+'/balance-zone']).decode().split()[0]
    assert actual==EXPECTED_BINARY
    cfgcheck='import json; from pathlib import Path; s=json.loads(Path("'+RUNTIME+'/eqemu_config.json").read_text())["server"]; d=s["database"]; assert d["db"]=="'+DB+'" and d["username"]=="nightcap_palwar_vox" and d["host"]=="mariadb"; assert str(s["auto_database_updates"]).lower()=="false"; print("isolated-config-pass")'
    run(['docker','exec',SERVER,'python3','-c',cfgcheck])
    assert sql(f'SELECT COUNT(*) FROM `{DB}`.account; SELECT COUNT(*) FROM `{DB}`.character_data;').splitlines()==['0','0']

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['gates','matrix','controls','restore']);args=parser.parse_args();preflight()
    if args.mode=='gates':
        for ident in ['palwar-605504-1h-captured','palwar-810099-2h-captured','palwar-605504-2h-equalized']:
            execute(next(c for c in base.matrix['conditions'] if c['id']==ident),'baseline',suffix='-replay')
        for arm in ['wu_off','steel_off','both_off']:
            for c in base.matrix['conditions']:execute(c,arm,'stats')
            execute(next(c for c in base.matrix['conditions'] if c['id']=='palwar-605504-1h-captured'),arm,suffix='-pilot')
        (OUT/'gates.json').write_text(json.dumps({'stat_conditions':144,'exact_baseline_replays':3,'binary_sha256':EXPECTED_BINARY,'matrix_sha256':hashlib.sha256((HERE/'matrix-private.json').read_bytes()).hexdigest(),'removed_first_ranks':{a:sorted(v) for a,v in ARMS.items()},'spent_points':'1979 retained, no refunds or reallocation','scope':'Whole AA removal; Way of Steel skill proc also disabled'},indent=2)+'\n')
    elif args.mode=='matrix':
        gate=json.loads((OUT/'gates.json').read_text());assert gate['binary_sha256']==EXPECTED_BINARY and gate['matrix_sha256']==hashlib.sha256((HERE/'matrix-private.json').read_bytes()).hexdigest()
        for arm in ['wu_off','steel_off','both_off']:
            for c in base.matrix['conditions']:
                for seed in base.matrix['seeds']:execute(c,arm,seed=seed)
    elif args.mode=='controls':
        for arm in ['wu_off','steel_off','both_off']:
            for item in [605504,611050,10099,810099]:
                for grip,skill in [('1h','captured'),('2h','equalized')]:
                    c=next(c for c in base.matrix['conditions'] if c['id']==f'palwar-{item}-{grip}-{skill}')
                    for seed in base.matrix['seeds']:execute(c,arm,seed=seed,pulse=50)
            c=next(c for c in base.matrix['conditions'] if c['id']=='palwar-605504-1h-captured')
            data=execute(c,arm,seed=101,suffix='-replay')
            assert data==json.loads((RESULTS/f"{arm}-{c['id']}-combat-101-32.json").read_text())
    else:reset('baseline');print('Restored synthetic ID1 baseline; no live changes')
