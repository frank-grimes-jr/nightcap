"""Classify every captured stock route; emit compact coverage and candidate views."""
import collections,gzip,json
from pathlib import Path
HERE=Path(__file__).resolve().parent

def load():return json.loads(gzip.decompress((HERE/'production.json.gz').read_bytes()))

def reason(r,flags):
    for a in ('s','e','lt','ld','l'):
        if r[a+'_min_expansion']>0:return 'later expansion'
        # -1 is unrestricted; zero includes Classic.
        if r[a+'_max_expansion'] not in (-1,None) and r[a+'_max_expansion']<0:return 'invalid expansion'
        required={x.strip() for x in (r[a+'_content_flags'] or '').split(',') if x.strip()}
        disabled={x.strip() for x in (r[a+'_content_flags_disabled'] or '').split(',') if x.strip()}
        if not required<=flags or disabled&flags:return 'content flags'
    if any(r[k]<=0 for k in ('chance','probability','lt_multiplier','ld_multiplier','spawn_chance')):return 'zero chance'
    if r['npc_min_level'] and r['npc_level']<r['npc_min_level']:return 'NPC level'
    if r['npc_max_level'] and r['npc_level']>r['npc_max_level']:return 'NPC level'
    if r['trivial_min_level']>50 or (r['trivial_max_level'] and r['trivial_max_level']<1):return 'player level'
    if r['condition']:return 'conditional spawn: review separately'
    if r['zone'] in ('cshome','arena','tutoriala','tutorialb','shadowrest'):return 'service/tutorial zone: not progression'
    return 'active stock route'

def active(data):
    flags={r['flag_name'] for r in data['content_flags'] if r['enabled']}
    items={r['id']:r for r in data['items']}
    return [r for r in data['routes'] if reason(r,flags)=='active stock route' and items[r['item']]['reqlevel']<=50]

def main():
    d=load();items={r['id']:r for r in d['items']};spells={r['id']:r['name'] for r in d['spells']}
    flags={r['flag_name'] for r in d['content_flags'] if r['enabled']};routes=active(d);by=collections.defaultdict(list)
    for r in routes:by[r['item']].append(r)
    gear=[]
    for key,rr in sorted(by.items()):
        row=items[key]
        gear.append(dict(id=key,name=row['Name'],slots=row['slots'],classes=row['classes'],min_npc_level=min(r['npc_level'] for r in rr),
            zones=sorted({r['zone'] for r in rr}),focus=spells.get(row['focuseffect'],''),worn=spells.get(row['worneffect'],''),
            hp=row['hp'],mana=row['mana'],heal=row['healamt'],damage=row['spelldmg']))
    out=dict(captured_utc=d['captured_utc'],captured_routes=len(d['routes']),route_dispositions=dict(collections.Counter(reason(r,flags) for r in d['routes'])),
        active_routes=len(routes),base_families=len(by),tier_definitions=sum(k%200000 in by for k in items),
        focus_families=dict(collections.Counter(r['focus'] or 'none' for r in gear)),gear=gear)
    supplement=json.loads((HERE/'supplement.json').read_bytes())
    conditions={(r['zone'],r['id']):r['value'] for r in supplement['spawn_conditions']}
    conditional=[r for r in d['routes'] if reason(r,flags)=='conditional spawn: review separately']
    enabled=[r for r in conditional if conditions.get((r['zone'],r['condition']),0)>=r['condition_value'] and items[r['item']]['reqlevel']<=50]
    combined={r['item'] for r in routes+enabled}
    glob=[r for r in supplement['global_equipment'] if r['enabled'] and all(r[k]<=0 for k in ('global_min_expansion','lt_min_expansion','ld_min_expansion','l_min_expansion'))]
    out['supplement']=dict(global_equipment_routes=len(supplement['global_equipment']),classic_global_routes=len(glob),
        global_extra_items=sorted({r['item'] for r in glob}-set(items)),
        conditional_routes=len(conditional),conditional_enabled_routes=len(enabled),
        combined_base_families=len(combined),combined_focus_families=dict(collections.Counter(spells.get(items[k]['focuseffect'],'none') for k in combined)),
        conditional_only_gear=[dict(id=k,name=items[k]['Name'],focus=spells.get(items[k]['focuseffect'],'none')) for k in sorted(combined-set(by))])
    (HERE/'coverage.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in out.items() if k!='gear'},indent=2))
if __name__=='__main__':main()
