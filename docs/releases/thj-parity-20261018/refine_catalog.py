"""Record screenshot precedence and quarantine inconsistent workbook attributes."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
p=ROOT/'config/thj-item-parity.json'
data=json.loads(p.read_text(encoding='utf-8'))
deferred={609289:['aagi','adex','heroic_agi','heroic_dex'],
          628904:['astr','asta','heroic_str','heroic_sta'],
          628997:['astr','asta','heroic_str','heroic_sta'],
          613673:['heroic_str','heroic_sta'],628664:['heroic_agi','heroic_dex']}
decisions=[]
import sys
sys.path.insert(0,str(ROOT/'tools'))
from thj_item_parity import snapshot
baseline=snapshot()
for item in data['items']:
    # Preserve the extracted fields separately so this review is reproducible.
    item.setdefault('source_fields',dict(item['fields']))
    item['fields']=dict(item['source_fields'])
    if item['id']==626549:
        corrections={'astr':0,'asta':40,'heroic_str':0,'heroic_sta':10}
        decisions.append({'id':item['id'],'action':'screenshot precedence','before':{f:item['fields'][f] for f in corrections},'after':corrections,
          'source':'image-089.png; empty sockets; Stamina40+10, no Strength line. Workbook Items row assigns STR instead.'})
        item['fields'].update(corrections)
        item['review']='Visible image089 overrides conflicting workbook STR/STA and associated heroics.'
    if item['id']==608364:
        corrections={f'heroic_{f}':8 for f in ('str','sta','agi','dex','int','wis','cha')}
        decisions.append({'id':item['id'],'action':'screenshot precedence','before':{f:item['fields'][f] for f in corrections},'after':corrections,
          'source':'Clean image093 shows all seven attributes30+8; workbook X47:AD47 says40. Screenshot independently inspected.'})
        item['fields'].update(corrections)
        item['review']='Visible image093 overrides all seven conflicting workbook heroic attributes.'
    if item['id'] in deferred:
        removed={f:item['fields'].pop(f) for f in deferred[item['id']] if f in item['fields']}
        decisions.append({'id':item['id'],'action':'defer uncorroborated attribute relocation','fields':removed,
          'reason':'Workbook removes a native ordinary attribute or assigns its heroic bonus to a different attribute; no clean screenshot resolves it. Preserve current fields.'})
        item['review']='Preserve ambiguous ordinary/heroic attribute pairs; see catalog-decisions.json.'
    for field,value in list(item['fields'].items()):
        if field not in ('delay','range') and value<baseline[item['base_id']][field] and item['id']!=626549:
            decisions.append({'id':item['id'],'action':'defer below-Normal field','field':field,'target':value,
                'normal':baseline[item['base_id']][field],'reason':'Do not create an upgrade inversion from workbook-only evidence.'})
            del item['fields'][field]
p.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
(Path(__file__).with_name('catalog-decisions.json')).write_text(json.dumps(decisions,indent=2)+'\n',encoding='utf-8')
