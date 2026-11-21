"""Validate measurements against bounded content policy; no formula mocks."""
import collections,gzip,json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent

def main():
    d=json.loads(gzip.decompress((HERE/'validated-results.json.gz').read_bytes()))
    inp=json.loads((HERE/'input.json').read_bytes())
    assert len(inp['policy'])==476 and len(d['cases'])==2*len(inp['cases'])==376
    assert len(d['defense_cases'])==2*len(inp['defense_cases'])==518
    def paired(rows):
        x=collections.defaultdict(dict)
        for r in rows:
            assert r['stage'] not in x[r['id']]
            x[r['id']][r['stage']]=r
        for key,v in x.items():assert set(v)=={'before','after'};yield key,v['before'],v['after']
    for ident,a,b in paired(d['defense_cases']):
        for r in (a,b):
            st=r['stats'];assert 0<=st['hp_regen_item']<=st['hp_regen_cap'];assert 0<=st['mana_regen_item']<=st['mana_regen_cap']
            assert len(r['rolls'])==4 and all(x['counts']['rolls']==20000 for x in r['rolls'])
        x,y=a['stats'],b['stats']
        assert 0<=y['hp_regen_item']-x['hp_regen_item']<=3
        assert 0<=y['mana_regen_item']-x['mana_regen_item']<=3
        assert y['dodge'] in (x['dodge'],max(x['dodge'],10))
        for k in ('parry','block'):assert y[k] in (x[k],max(x[k],8))
    for ident,a,b in paired(d['cases']):
        x,y=a['metrics'],b['metrics']
        for k in ('hp','mana','heal_amount','spell_damage','channeling'):assert x[k]==y[k],(ident,k)
        assert y['healing_sample']>=x['healing_sample'],(ident,'healing reduced')
        assert y['cast_ms']<=x['cast_ms'],(ident,'cast slower')
        assert y['mana_cost_sample']<=x['mana_cost_sample'],(ident,'mana more expensive')
        if ident.startswith('full_dodging-'):assert x['defensive']['dodge']==y['defensive']['dodge']==10
        for r in (a,b):
            assert r['damage']>0 and r['swings']>0 and r['attempts']>0 and r['landed_casts']>0
            assert r['metrics']['hp']+r['healing']+r['hp_regen']-r['damage']==r['hp_end'],ident
    summaries={}
    for kind in ('ordinary','pressure'):
        summaries[kind]={}
        for state in ('before','after'):
            rows=[r for r in d['cases'] if r['stage']==state and r['id'].startswith('pressure-')==(kind=='pressure')]
            summaries[kind][state]={'runs':len(rows),'outcomes':dict(collections.Counter(r['result'] for r in rows)), 'landed_casts':sum(r['landed_casts'] for r in rows),'damage':sum(r['damage'] for r in rows),'elapsed_ms':sum(r['elapsed_ms'] for r in rows)}
    out={'passed':True,'pressure_pairs':188,'defense_pairs':259,'conditional_defensive_rolls':518*4*20000,'summary':summaries,'input_sha256':hashlib.sha256((HERE/'input.json').read_bytes()).hexdigest(),'result_sha256':hashlib.sha256((HERE/'validated-results.json.gz').read_bytes()).hexdigest(),'limits':'Actual native skill-roll checks and primary-hand pressure with six-second combat regen; not full NPC AI, special attack rounds, bash/stun or raid AE simulation. Conditional skill avoidance is not total incoming hit-rate reduction. Player acceptance remains open.'}
    (HERE/'validation.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
