"""Conservative component reachability; existence is never treated as availability."""
import collections,gzip,json
from pathlib import Path
from analyze import reason
HERE=Path(__file__).resolve().parent
def read(name):
    raw=(HERE/name).read_bytes()
    return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
def audit():
    a=read('acquisition.json.gz');d=read('production.json.gz');c=read('components.json.gz');s=read('craft-support.json.gz')
    flags={r['flag_name'] for r in d['content_flags'] if r['enabled']}
    conditions={(r['zone'],r['id']):r['value'] for r in read('supplement.json')['spawn_conditions']}
    excluded={'arena','cshome','tutoriala','tutorialb','shadowrest'}
    def gate(r,prefix=''):
        return r[prefix+'min_expansion']<=0 and r[prefix+'max_expansion']>=-1 and set(filter(None,(r[prefix+'content_flags'] or '').split(',')))<=flags and not set(filter(None,(r[prefix+'content_flags_disabled'] or '').split(',')))&flags
    def condition(r):return not r['condition'] or conditions.get((r['zone'],r['condition']),0)>=r['condition_value']
    reached={};drop=collections.defaultdict(list)
    for r in c['routes']:
        why=reason(r,flags)
        if r['zone'] not in excluded and (why=='active stock route' or why=='conditional spawn: review separately' and condition(r)):
            drop[r['item']].append(r)
            reached.setdefault(r['item'],{'kind':'drop','zone':r['zone'],'npc':r['npc'],'npc_name':r['npc_name']})
    merchants={r['merchant']:r for r in c['merchant_spawns'] if r['zone'] not in excluded and r['chance']>0 and gate(r,'s_') and gate(r,'e_') and condition(r)}
    for r in a['merchants']:
        if r['merchantid'] in merchants and gate(r) and r['probability']>0 and r['min_status']==0 and r['level_required']<=50 and not r['bucket_name']:
            reached.setdefault(r['item'],{'kind':'merchant','merchant':r['merchantid'],'zone':merchants[r['merchantid']]['zone'],'level_required':r['level_required'],'faction_required':r['faction_required'],'classes_required':r['classes_required']})
    entries=collections.defaultdict(list)
    for r in a['entries']:entries[r['recipe_id']].append(r)
    items={r['id']:r for r in a['items']}
    # Container type IDs <1000 are world container types, not item definitions.
    containers={r['type'] for r in s['objects'] if r.get('version',0)==0 and gate(r)}
    recipes=[r for r in a['recipes'] if gate(r) and not r['must_learn'] and not r['quest']]
    accepted={};pending=True
    while pending:
        pending=False
        for spell in s['spells']:
            # Only reviewed, ordinary enchant/imbue ingredient conversions.
            if not spell['name'].startswith(('Enchant ','Imbue ')):continue
            scroll=next((r for r in s['scrolls'] if r['scrolleffect']==spell['id'] and r['id'] in reached),None)
            ingredients=[spell['components'+str(i)] for i in range(1,5) if spell['components'+str(i)]>0]
            if not scroll or not ingredients or not all(i in reached for i in ingredients):continue
            for n in range(1,13):
                k=spell['effect_base_value'+str(n)]
                if spell['effectid'+str(n)]==32 and k>0 and k not in reached:
                    reached[k]={'kind':'spell','spell':spell['id'],'name':spell['name'],'scroll':scroll['id'],'components':ingredients,'classes':{str(i):spell['classes'+str(i)] for i in range(1,17) if spell['classes'+str(i)]<=50}};pending=True
        for r in recipes:
            k=r['id'];ee=entries[k];components=[e['item_id'] for e in ee if e['componentcount']];kits=[e['item_id'] for e in ee if e['iscontainer']]
            kit=next((x for x in kits if x in reached or x<1000 and x in containers),None)
            if k in accepted or not components or kit is None or not all(i in reached for i in components):continue
            accepted[k]={'components':components,'container':kit,'trivial':r['trivial'],'name':r['name']}
            for e in ee:
                if e['successcount'] and e['item_id'] not in reached:
                    reached[e['item_id']]={'kind':'recipe','recipe':k};pending=True
    finished={k:v for k,v in reached.items() if k in items and items[k]['itemclass']==0 and items[k]['slots'] and items[k]['reqlevel']<=50}
    outputs={e['item_id'] for e in a['entries'] if e['successcount'] and e['item_id'] in items and items[e['item_id']]['slots'] and items[e['item_id']]['itemclass']==0}
    return dict(captured_utc=a['captured_utc'],scope='Conservative reachability from gated stock drops/merchants and reachable recipe components/containers. Vendor faction/class requirements retained. Spell-created, forage, ground-spawn and quest ingredients need explicit review; not silently seeded.',counts=dict(captured_recipes=len(a['recipes']),captured_finished_outputs=len(outputs),reachable_recipes=len(accepted),reachable_finished_outputs=len(outputs&set(reached))),reached={str(k):v for k,v in reached.items()},recipes={str(k):v for k,v in accepted.items()},finished={str(k):{'name':items[k]['Name'],**v} for k,v in finished.items()},unresolved_outputs=sorted(outputs-set(reached)))
if __name__=='__main__':
    out=audit();(HERE/'acquisition-audit.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out['counts']))
