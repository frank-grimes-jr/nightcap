"""Validate current-engine measurements and report their explicit limits."""
import collections,gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def pairs(rows):
    groups=collections.defaultdict(dict)
    for r in rows:
        assert r['stage'] not in groups[r['id']]
        groups[r['id']][r['stage']]=r
    for key,v in groups.items():
        assert set(v)=={'before','after'}
        yield key,v['before'],v['after']
def main():
    raw=(HERE/'results.json').read_bytes();d=json.loads(raw);inp=json.loads((HERE/'input.json').read_bytes())
    for kind in ('cases','defense_cases','offense_cases'):assert len(d[kind])==2*len(inp[kind])
    for ident,a,b in pairs(d['defense_cases']):
        x,y=a['stats'],b['stats']
        for k,cap in [('hp_regen_item','hp_regen_cap'),('mana_regen_item','mana_regen_cap')]:
            assert 0<=y[k]-x[k]<=2,(ident,k)
            assert 0<=y[k]<=y[cap]
        assert y['dodge'] in (x['dodge'],max(x['dodge'],10))
        for k in ('block','parry'):assert y[k] in (x[k],max(x[k],8))
        x,y=a['offense'],b['offense']
        assert 0<=y['item_atk']-x['item_atk']<=15
        assert y['item_haste'] in (x['item_haste'],max(x['item_haste'],10),max(x['item_haste'],20))
        assert y['accuracy']==x['accuracy']
    for ident,a,b in pairs(d['cases']):
        x,y=a['metrics'],b['metrics']
        for k in ('hp','mana','heal_amount','spell_damage','channeling'):assert x[k]==y[k],(ident,k)
        assert y['healing_sample']>=x['healing_sample'],(ident,'healing reduced')
        assert y['cast_ms']<=x['cast_ms'],(ident,'cast slower')
        assert y['mana_cost_sample']<=x['mana_cost_sample'],(ident,'mana increased')
        for r in (a,b):
            assert r['damage']>0 and r['attempts']>0 and r['landed_casts']>0
            assert r['metrics']['hp']+r['healing']+r['hp_regen']-r['damage']==r['hp_end']
        assert not (a['result']=='duration' and b['result']=='player_death'),ident
        if ident.startswith('full_dodging'):assert x['defensive']['dodge']==y['defensive']['dodge']==10
    offense={}
    for ident,a,b in pairs(d['offense_cases']):
        offense[ident]=(a,b)
        for x,y in zip(a.get('spells',[]),b.get('spells',[]),strict=True):
            assert x['spell']==y['spell'] and x['base']==y['base']
            assert abs(y['amount'])>=abs(x['amount']),(ident,'damage reduced')
            if ident.startswith('full-caster-aug1'):assert x==y,(ident,'augment focus stacked')
        if 'melee' in a:
            for r in (a,b):
                m=r['melee'];assert m['damage']>0 and m['swings']==m['duration_ms']//m['interval_ms']
            assert b['melee']['interval_ms']<=a['melee']['interval_ms']
    for level in (20,35,50):
        for kind in ('direct','area','dot_lifetap'):
            for effect in ('damage','dot'):
                a=offense[f'spell-{level}-{kind}-{effect}'][1]['spells']
                b=offense[f'spell-{level}-{kind}-{effect}_duplicate'][1]['spells']
                assert [s['focus'] for s in a]==[s['focus'] for s in b]
    x,y=offense['haste-control-no_haste'];assert x['offense']['item_haste']==0 and y['offense']['item_haste']==20
    assert y['melee']['interval_ms']<x['melee']['interval_ms'] and y['melee']['swings']>x['melee']['swings']
    x,y=offense['haste-control-stronger_haste'];assert x['offense']['item_haste']==y['offense']['item_haste']==36
    assert x['melee']['interval_ms']==y['melee']['interval_ms']
    crit=[r['spells'][0]['amount'] for r in d['offense_cases'] if r['id'].startswith('full-caster-aug1-aa1-seed') and r['stage']=='after']
    assert len(set(crit))>1,'Critical-roll controls did not exercise more than one damage outcome'
    summary={'passed':True,'pressure_pairs':len(inp['cases']),'defense_pairs':len(inp['defense_cases']),'offense_pairs':len(inp['offense_cases']),
        'pressure_outcomes':{state:dict(collections.Counter(r['result'] for r in d['cases'] if r['stage']==state)) for state in ('before','after')},
        'haste_controls':{k:[v['melee'] for v in offense[k]] for k in ('haste-control-no_haste','haste-control-stronger_haste')},
        'caster_aug_aa_damage_outcomes':sorted(set(crit)),
        'input_sha256':hashlib.sha256((HERE/'input.json').read_bytes()).hexdigest(),
        'limits':'Native spell formula samples, not landed casts/resists/ticks. Timed primary-hand throughput resets HP between swings; not a survival encounter. Incoming pressure includes combat regen/self-heals but no full AI, bash or raid AEs. Player acceptance remains open.'}
    packed=gzip.compress(raw,mtime=0);(HERE/'validated-results.json.gz').write_bytes(packed);summary['results_sha256']=hashlib.sha256(packed).hexdigest()
    (HERE/'validation.json').write_text(json.dumps(summary,indent=2)+'\n',encoding='utf8');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
