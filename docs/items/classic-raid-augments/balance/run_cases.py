"""Generate level-50 legal AA fixtures on the host; run paired cases inside the isolated game container."""
import argparse
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile

R=Path('/tmp/nightcap-balance-raid-augs-20261112')
DB='nightcap_raid_aug_balance_20261112'
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3] if os.name=='nt' else None
IDS={'melee':97101,'spell':97102,'hybrid':97103,'pet':97104}
HUNT={'melee':940227,'spell':940563,'hybrid':940227,'pet':940483}
ALT={'melee':940483,'spell':940483,'hybrid':940483,'pet':940563}
NPCS=[32040,72003,76007,71065]
SEEDS=[1112,1113,1114]


def templates():
    sys.path.insert(0,str(ROOT/'tools'/'balance'))
    from aa_allocations import Purchases
    base=json.loads((ROOT/'docs/balance/native-aa-inputs.json').read_text())['builds']
    pet=json.loads((ROOT/'docs/balance/pet-support-inputs.json').read_text())['cases'][0]['input']['pet_probe']
    inputs={}
    for role,profile,classes in [('melee','war-clr-mnk',[1,2,7]),('spell','war-clr-wiz',[1,2,12]),('hybrid','war-pal-mnk',[1,3,7]),('pet','mag-nec-shm',[13,11,10])]:
        b=copy.deepcopy(next(x for x in base if x['profile']==('war-clr-mnk' if role=='hybrid' else profile)))
        if role=='hybrid':
            with tarfile.open(ROOT/'docs/releases/thj-parity-20261018/evidence/native-results.tar.gz') as archive:
                b=json.load(archive.extractfile('wpm-classic50-zero-input.json'))['builds'][0]
        b.update(test_character_id=IDS[role],profile=profile,classes=classes,aa_budget=0,aa_rank_ids=[])
        for key in ('aa_stage','raw_item_totals','total_score','capped_spell_damage','capped_heal_amount','casting_stat_scored','melee_ratio_scored'):
            b.pop(key,None)
        b['tier']='Ascended worn gear'
        b['equipment']=[{'slot':x['slot'],'id':602814 if x['slot']==17 and role=='hybrid' else x['id']} for x in b['equipment']]
        inputs[role]={'builds':[b],'export_equipment':True}
        if role=='pet':
            inputs[role]['pet_probe']=copy.deepcopy(pet)
            inputs[role]['pet_probe'].update(retry_native_fizzles=True)
            inputs[role]['pet_probe']['combat'].update(capture_terminal=True,approach_policy='native_spell_range')
        else:
            inputs[role]['encounter']={'npc_id':32040,'npc_position':[-871,-1395,104.879997,45],'duration_ms':900000,'return_to_melee':True,'melee_specials':role!='spell','combat_policy':{'melee':'melee_heal','spell':'caster_heal','hybrid':'wpm'}[role]}
        # Each profile buys the native eligibility-filtered catalog in priority order up to 500 points.
        if (HERE/(role+'-catalog.json')).exists():
            rows=json.loads((HERE/(role+'-catalog.json')).read_text())
            state=Purchases(rows)
            state.free_closure()
            priority=[28,33,34,20,224,18,19,30,189,108,23,114,215,397,398]
            while True:
                available=[r for r in state.ranks.values() if not state.reasons(r) and state.spent+r['cost']<=500]
                if not available:break
                state.buy(min(available,key=lambda r:(priority.index(r['ability_id']) if r['ability_id'] in priority else 100,r['cost'],r['rank'],r['rank_id'])))
            b.update(aa_budget=500,aa_rank_ids=state.ids,aa_policy='native legal level-50 purchases; defense and sustain priority')
    out=HERE/'fixtures.json'
    out.write_text(json.dumps(inputs,indent=2)+'\n')


def native(name, data, seed, prefix=''):
    assert Path.cwd()==R
    role=prefix+name.split('/')[0]
    case=R/(role+'-input.json')
    case.write_text(json.dumps(data))
    out=R/(role+'-result.json')
    if out.exists():out.unlink()
    logpath=R/(role+'-case.log')
    with logpath.open('w') as log:
        p=subprocess.run([str(R/'balance-zone'),'tests:balance',str(case),str(out)],env=dict(os.environ,NIGHTCAP_BALANCE_RNG_SEED=str(seed)),stdout=log,stderr=subprocess.STDOUT)
    if p.returncode or not out.is_file():raise RuntimeError(name+' '+logpath.read_text()[-950:])
    return json.loads(out.read_text())


def run(stage,subset,only):
    assert Path.cwd()==R
    config=json.loads((R/'eqemu_config.json').read_text())['server']['database']
    assert config['host']=='nightcap-raid-aug-balance-20261112' and config['db']==DB and config['username']=='raid_aug_balance_261112'
    fixtures=json.loads((R/'fixtures.json').read_text())
    prefix={'controls':'control-','post':'post-','eye':'eye-'}.get(subset,'')
    if subset=='controls':
        for base in fixtures.values():base['builds'][0]['test_character_id']+=100
    if subset=='eye':fixtures['pet']['builds'][0]['test_character_id']+=100
    for role,base in fixtures.items():
        if stage=='catalog':
            o=native(role,{'builds':base['builds'],'export_aa_catalog':True},1112)
            (R/(role+'-catalog.json')).write_text(json.dumps(o['builds'][0]['aa_catalog']))
    if stage=='catalog':return
    path=R/(prefix+only+'-measured.jsonl')
    seen={(e['role'],e['npc'],e['seed'],e['item']) for e in [json.loads(x) for x in path.read_text().splitlines()]} if path.exists() else set()
    # First cover all four roles and bosses. Then fill the remaining seeds and stat alternatives.
    for seed in (range(1115,1121) if subset=='eye' else SEEDS):
        for npc in NPCS:
            for role,base in fixtures.items():
                if only!='all' and role!=only:continue
                if subset=='dragon' and npc!=32040:continue
                if subset=='post' and (role,npc) not in {('hybrid',71065),('pet',76007),('pet',32040),('spell',32040),('hybrid',72003)}:continue
                if subset=='eye' and (role,npc)!=('pet',71065):continue
                items=[HUNT[role],ALT[role],963213,963214,963215,*range(963200,963213)]
                if subset=='dragon':items=[0,940227,940483,940563,940507,940115,961023,963213,963214,963215]
                if subset=='post':items=[0,940227,940483,940563,940507,940115,961023,963213,963214,963215]
                if subset=='eye':items=[963204,0,940483,940507]
                if subset=='controls':
                    if role=='pet' and npc==32040:continue
                    items=[x for x in (0,940227,940483,940563,940507,940115,961023) if x not in (HUNT[role],ALT[role])]
                for item in ([HUNT[role]] if stage=='pilot' else items):
                    if subset=='finales' and item in range(963200,963213):continue
                    if (role,npc,seed,item) in seen:continue
                    value=copy.deepcopy(base)
                    b=value['builds'][0]
                    chest=next(r for r in b['equipment'] if r['slot']==17)
                    chest['augments']=[{'socket':0 if role=='hybrid' else 2,'id':item}] if item else []
                    value['expect_raid_id']=item if item>=963200 else 0
                    e=value.get('encounter') if role!='pet' else value['pet_probe']['combat']
                    e['npc_id']=npc
                    # Clear only this fixture's raid cooldown between independent combats.
                    subprocess.run(['mysql','-h',config['host'],'-u',config['username'],DB,'-e',f"DELETE FROM timers WHERE char_id={b['test_character_id']}"],env=dict(os.environ,MYSQL_PWD=config['password']),check=True)
                    o=native(f'{role}/{npc}/{item}',value,seed,prefix)
                    stat=o['builds'][0]
                    c=o['encounter'] if role!='pet' else o['pet_probe']['combat']
                    trace=c['trace']
                    hp=[t['player_hp'] if role!='pet' else t['player']['hp'] for t in trace]
                    mana=[t['player_mana'] if role!='pet' else t['player']['mana'] for t in trace]
                    leg=c.get('player_ledger')
                    elapsed=c.get('elapsed_ms',trace[-1]['ms'])
                    entry=dict(role=role,npc=npc,seed=seed,item=item,result=c['result'],ms=elapsed,min_sample_hp=min(hp),min_sample_mana=min(mana),final_hp=hp[-1],mana_zero_ms=next((t['ms'] for t,v in zip(trace,mana) if v==0),None),base_hp=stat['hp'],base_mana=stat['mana'],final_boss_hp=trace[-1].get('npc_hp',trace[-1].get('boss_hp')),aa_spent=stat['aa_spent'],spell_damage=stat['spell_damage'],heal_amount=stat['heal_amount'],raid=o['raid_effects'],pet_roster=len(trace[0]['pets']) if role=='pet' else 0)
                    if leg:
                        entry['owner_effective_spell_melee_healing']=sum(max(0,h['healed']) for h in leg['healing'])
                        entry['ordinary_rune_absorbed']=sum(h['rune_used'] for h in leg['incoming'])
                    if role=='pet':entry['initial_pet_ids']=[p['id'] for p in trace[0]['pets']]
                    entry['end_zero_ms']=next((t['ms'] for t in trace if t.get('player_endurance',t.get('player',{}).get('endurance'))==0),None)
                    entry['end_measured']=bool('player_endurance' in trace[0] or 'endurance' in trace[0].get('player',{}))
                    assert 'ordinary_owner_heals' in entry['raid']
                    with path.open('a') as w:w.write(json.dumps(entry)+'\n')
                    print(role,npc,item,seed,c['result'],elapsed,flush=True)
                if stage=='pilot' and npc==NPCS[0]:continue
            if stage=='pilot':return


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('stage',choices=['templates','catalog','pilot','combat'])
    parser.add_argument('--subset',choices=['all','finales','dragon','controls','post','eye'],default='all')
    parser.add_argument('--role',choices=['all',*IDS],default='all')
    a=parser.parse_args()
    if a.stage=='templates':templates()
    else:run(a.stage,a.subset,a.role)
