"""Prepare current wiki guidance; publication waits for verified activation."""
import json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent
WIKI=Path('C:/Users/verre/.codex/worktrees/aa-level-wiki/EQ_Local_Dev/wiki')
NOTICES={
 'dungeon-modes':'Chapterhouse adds a level-50 Raid/Grind expedition with four named enemies and a separate personal Paladin story journal. There are now 22 dungeon choices: the 21 Classic dungeons plus this curated exception. Six final Raid variants bring the dungeon reward definitions to 420.',
 'equipment':'The Winged Helm of the Dawn is earned through Camil’s Vigil of the Dawn. Its existing stats and sockets remain unchanged. Chapterhouse also awards three miniboss items, six final Raid variants and a four-quality augment.',
 'features':'Camil’s level-50 Paladin story in Chapterhouse uses native Tasks, persistent personal chapters and a one-time helmet claim. Custom enemies and encounter mechanics support a demanding capstone, with era-curated rewards.',
 'index':'Camil’s Vigil of the Dawn is available for live testing. Begin in East Commonlands with a level-50 character holding Paladin, then visit the Keeper near Befallen in West Commonlands.',
 'item-upgrades':'Ember of the First Dawn uses #zoneforge: three Base copies or four Polished/Exalted copies make the next quality. Camil’s helmet receives no new socket. The miniboss and final Raid equipment do not use this augment recipe.',
 'recent-changes':'October 23: Camil’s Chapterhouse quest, level-50–53 encounters, custom rewards, Ember augment, waypoint and Keeper are deployed for live testing. Native Tasks track the story. Full encounter balance and player acceptance remain open.',
 'travel':'A dedicated Keeper near Befallen in West Commonlands opens Chapterhouse expeditions. The zone uses a scoped level-50 exception; Classic remains the global era. Exits return to West Commonlands.',
 'tunnel':'Camil Silvermist offers The Vigil of the Dawn to level-50 characters holding Paladin in any class slot. He starts the personal story and delivers the earned helmet. Make room in Tasks for both story and dungeon journals.',
 'unreleased':'The Vigil of the Dawn has moved into live testing. Combat, travel and recovery still require player acceptance; installation is not completed gameplay validation.',
 'waypoints':'Chapterhouse has a waypoint that recalls to its public service foyer. Its Keeper controls admission to private runs. Register the waypoint there before recalling to it.',
 'zone-hunt':'Chapterhouse adds Ember of the First Dawn, a level-50 type-22 armor augment with four qualities. It follows existing Hunt headroom and zone forging. Its curated static enemies have a 0.5% augment roll; summoned encounter shades do not.'}

for name,body in NOTICES.items():
 p=WIKI/'articles'/(name+'.json');d=json.loads(p.read_text(encoding='utf-8'))
 replacement='<h2 id="chapterhouse-candidate">The Vigil of the Dawn — live testing</h2><p>'+body+' <a href="camil-vigil.html">Read the quest guide</a> and <a href="zone-chapterhouse.html">reward catalog</a>.</p>'
 d['body'],count=re.subn(r'<h2 id="chapterhouse-candidate">.*?(?=<h2|$)',replacement,d['body'],flags=re.S)
 assert count==1,name
 if name=='equipment':d['body']=d['body'].replace('No acquisition quest is active yet; a Chapterhouse quest candidate is now implemented.','Earn this helmet through Camil’s Vigil of the Dawn, now in live testing.')
 d['updated']='2026-10-23'
 d['sources'].append('docs/quests/camil-chapterhouse/deployment/README.md')
 p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
p=WIKI/'articles/camil-vigil.json';d=json.loads(p.read_text(encoding='utf-8'))
d.update(title='The Vigil of the Dawn',summary='Camil’s level-50 Paladin helmet story in Chapterhouse. Live testing, demanding at maximum legal power.',status='Live testing')
d['body']=d['body'].replace('<h2 id="availability">Not released</h2><p>This candidate has not been activated. Native and in-game balance, travel and recovery checks remain distinct; no completed player acceptance is claimed.</p>',
 '<h2 id="availability">Live testing</h2><p>Deployed October 23 for live testing. Automated native, content and cache checks passed. Full encounters, client-visible behavior and owner balance acceptance remain open.</p>')
d['body']=d['body'].replace('The intended route starts','The route starts').replace('Candidate rewards','Rewards').replace('These are candidate values.','<a href="zone-chapterhouse.html">Browse every published reward and its values</a>.')
d['sources'].append('docs/quests/camil-chapterhouse/deployment/README.md')
p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
rows=json.loads((HERE.parent/'install-rows.json').read_text())['items']
helmet=json.loads((HERE/'production-preimage.json').read_text())['content']['helmet'][0]
stats={'ac':'AC','hp':'HP','mana':'Mana','endur':'Endurance','aagi':'AGI','acha':'CHA','adex':'DEX','aint':'INT','asta':'STA','astr':'STR','awis':'WIS',
 'heroic_agi':'Heroic AGI','heroic_cha':'Heroic CHA','heroic_dex':'Heroic DEX','heroic_int':'Heroic INT','heroic_sta':'Heroic STA','heroic_str':'Heroic STR','heroic_wis':'Heroic WIS',
 'cr':'Cold resist','dr':'Disease resist','fr':'Fire resist','mr':'Magic resist','pr':'Poison resist','damage':'Damage','delay':'Delay'}
slots=['Charm','Ear','Head','Face','Ear','Neck','Shoulders','Arms','Back','Wrist','Wrist','Ranged','Hands','Primary','Secondary','Finger','Finger','Chest','Legs','Feet','Waist','Power source','Ammo']
items=[]
for r in rows+[helmet]:
 id=r['id'];kind='Augment' if 961000<=id<=961003 else 'Miniboss reward' if 961010<=id<=961012 else 'Quest helmet' if id==990500 else 'Final Raid reward'
 items.append({'id':id,'name':r['Name'],'kind':kind,'required_level':r['reqlevel'],'recommended_level':r['reclevel'],
  'slot':', '.join(dict.fromkeys(s for i,s in enumerate(slots) if int(r['slots'])&(1<<i))),
  'classes':'Paladin' if id==990500 else 'All','magic':bool(r['magic']),
  'stats':{label:r[k] for k,label in stats.items() if r.get(k,0)},
  'source':{961010:'Vicar Sered the Bellkeeper',961011:'Warden Halvyr',961012:'Sir Vaelen Ashen Dawn',990500:'Camil Silvermist, after completing The Vigil of the Dawn'}.get(id,'Eligible curated static Chapterhouse enemies' if kind=='Augment' else 'The Unbroken Shadow in Raid mode')})
catalog=json.loads((WIKI/'catalog.json').read_text(encoding='utf-8'))
catalog['chapterhouse']={'updated':'2026-10-23','status':'Live testing','items':items,'sources':['docs/quests/camil-chapterhouse/install-rows.json','docs/quests/camil-chapterhouse/deployment/README.md']}
(WIKI/'catalog.json').write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
print(json.dumps({'updated_guides':12,'custom_items':len(items),'existing_hunt_items':len(catalog['items'])}))
