"""Coverage of obtainable stock families, not a claim every drop needs an effect."""
import collections,json
from analyze import load,reason,HERE
RAIDS={'airplane','fearplane','hateplane','hateplaneb'}
CASTERS={2:'Cleric',3:'Paladin',4:'Ranger',5:'Shadowknight',6:'Druid',10:'Shaman',11:'Necromancer',12:'Wizard',13:'Magician',14:'Enchanter',15:'Beastlord'}
def routes(data):
    flags={r['flag_name'] for r in data['content_flags'] if r['enabled']}
    items={r['id']:r for r in data['items']}
    conditions={(r['zone'],r['id']):r['value'] for r in json.loads((HERE/'supplement.json').read_bytes())['spawn_conditions']}
    result=[]
    for r in data['routes']:
        why=reason(r,flags)
        valid=why=='active stock route' or (why=='conditional spawn: review separately' and conditions.get((r['zone'],r['condition']),0)>=r['condition_value'])
        if valid and r['zone'] not in ('cshome','arena','tutoriala','tutorialb','shadowrest') and items[r['item']]['reqlevel']<=50:result.append(r)
    return result

def stage(r):
    if r['zone'] in RAIDS or r['npc_level']>50:return 'raid'
    return 'early' if r['npc_level']<=20 else 'mid' if r['npc_level']<=35 else 'pre_raid'

def main():
    d=load();it={r['id']:r for r in d['items']};sp={r['id']:r for r in d['spells']};rr=routes(d)
    policy=json.loads((HERE/'policy.json').read_bytes())['families'];by=collections.defaultdict(list)
    for r in rr:by[r['item']].append(r)
    def kind(effect):
        if effect not in sp:return None
        effects={sp[effect]['effectid'+str(i)] for i in range(1,13)}
        return next((name for spa,name in [(127,'haste'),(125,'healing'),(132,'mana'),(174,'dodge'),(175,'parry_block'),(0,'hp_regen'),(15,'mana_regen')] if spa in effects),None)
    matrix=[]
    for era in ('early','mid','pre_raid','raid'):
        for cl,name in CASTERS.items():
            for category in ('haste','healing','mana','dodge','parry_block','hp_regen','mana_regen'):
                row={'stage':era,'class':name,'category':category}
                for state in ('before','after'):
                    ids=[];slots=set();zones=set()
                    for key,rs in by.items():
                        matches=[r for r in rs if stage(r)==era]
                        if not matches or not it[key]['classes']&(1<<(cl-1)):continue
                        fields={'focus':it[key]['focuseffect'],'worn':it[key]['worneffect']}
                        if state=='after':fields.update({k:v for k,v in policy.get(str(key),{}).items() if k in fields})
                        if not any(kind(e)==category for e in fields.values()):continue
                        ids.append(key);slots|={s for s in range(1,22) if it[key]['slots']&(1<<s)};zones|={r['zone'] for r in matches}
                    row[state]={'families':len(ids),'slots':sorted(slots),'zones':sorted(zones),'ids':sorted(ids)}
                matrix.append(row)
    target=[]
    for k,e in policy.items():
        key=int(k);assert key in by,(key,'no active route')
        target.append(dict(id=key,**e,classes=it[key]['classes'],slots=it[key]['slots'],sources=sorted({(r['zone'],r['npc_name'],r['npc_level']) for r in by[key]})))
    out={'captured_utc':d['captured_utc'],'base_families':len(by),'target_families':len(policy),'target_definitions':4*len(policy),'targets':target,'matrix':matrix,'scope':'Class-mask access; actual skills, held-class spell level and haste minimum cast times still govern benefits. Stages describe drop-source level, not guaranteed player acquisition. Includes current enabled conditional spawns.'}
    (HERE/'coverage-after.json').write_text(json.dumps(out,indent=2)+'\n')
    print(json.dumps({k:v for k,v in out.items() if k not in ('targets','matrix')}))
if __name__=='__main__':main()
