"""Prepare scoped player guides over the exact current public source; no publication."""
from pathlib import Path
import hashlib,html,json,shutil,subprocess,sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
BEFORE=Path('E:/EQ_Local_Dev/artifacts/aa-purchase-latency-20261121');ART=Path('E:/EQ_Local_Dev/artifacts/classic-equipment-paths-20261121');SITE=ART/'wiki'
RELEASE='20261121-classic-equipment-paths-v2'
def main():
 ART.mkdir(exist_ok=True)
 if not SITE.exists():shutil.copytree(BEFORE/'wiki',SITE,ignore=shutil.ignore_patterns('dist','__pycache__','*.tar.gz','*.tar.json'))
 for name in ('config','docs'):
  if not (ART/name).exists():shutil.copytree(BEFORE/name,ART/name)
 subprocess.run([sys.executable,'-B',str(SITE/'build.py')],check=True)
 previous=json.loads((BEFORE/'20261121-aa-purchase-latency-v1.tar.json').read_bytes())
 assert all(hashlib.sha256((SITE/'dist'/n).read_bytes()).hexdigest()==pin for n,pin in previous.items())
 policy=json.loads((ROOT/'docs/items/classic-equipment-paths/policy.json').read_bytes())['families'];effects={s['id']:s['name'] for s in json.loads((ROOT/'docs/items/classic-equipment-paths/effects.json').read_bytes())['spells']}
 table='<table><thead><tr><th>Item</th><th>Source</th><th>Added focus</th><th>Added worn effect</th></tr></thead><tbody>'
 names={'crafted_armor':'Crafting','crafted_jewelry':'Enchanted jewelcraft','class_quest':'Class quest','ro_quest':'Armor of Ro quest','stock_drop':'Named drop'}
 for k,e in policy.items():table+='<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in [e['name'],names[e['category']],effects.get(e.get('focus'),'None'),effects.get(e.get('worn'),'None')])+'</tr>'
 table+='</tbody></table>'
 sections={
 'equipment':'<h2 id="classic-equipment-paths">Classic crafted and quest equipment</h2><p>More stock armor and jewelry now offer offensive, defensive and casting effects. The list covers149 item families across all four existing qualities. The effect strength is the same at each quality. Existing effects and stats stay unchanged.</p><p>New glove effects give 10% or 20% melee haste. A stronger item haste effect takes priority. New shoulder effects add 5 or 15 ATK. New head and foot effects add 1 or 2 HP or mana per tick. Dodge and parry effects use the strongest matching worn effect.</p><p>Damage and affliction focuses use Nightcap scaling. Their 20% endpoint contributes 200% before other modifiers. Spell-level and spell-type limits still apply. Duplicate item and augment focuses do not add together. An existing stronger focus retains its strength.</p><p>Custom augments, weapon procs and healing strength stay unchanged. Recipes still produce their existing quality. Enchanted jewelry and its same-name unenchanted version are different items; only the enchanted items below gain effects.</p>'+table,
 'tradeskills':'<h2 id="classic-equipment-paths">Classic focus equipment</h2><p>Selected Fine Plate and racial armor pieces now have worn and casting effects. Selected enchanted jewelry adds spell haste, healing, mana preservation, damage, affliction or dodge effects. Recipes, ingredients, required skills and output quality stay unchanged.</p><p>Platinum rank III focus jewelry requires high-skill recipes. Its ingredients and finished items can be traded. It offers a crafting route to the same focus category used by dropped gear. See the <a href="equipment.html#classic-equipment-paths">equipment list</a>.</p>',
 'travel':'<h2 id="classic-temple-access">Temple of Solusek Ro</h2><p>The Temple of Solusek Ro is available in Classic. Enter from Lavastorm for its class armor quests. Quest faction and item requirements still apply. Other expansion zone limits stay unchanged.</p>',
 'combat':'<h2 id="classic-equipment-paths">Classic equipment alternatives</h2><p>Crafted, quested and dropped gear offer more ways to obtain casting focuses and worn effects. Item haste uses the strongest value. New shoulder ATK and head or foot regeneration have limited equipment slots. Identical dodge effects, including Dodging scales, do not add together.</p><p>Healing strength is unchanged. Damage-focus items and augments share their existing strongest-focus rules. See the <a href="equipment.html#classic-equipment-paths">equipment list</a>.</p>',
 'features':'<h2 id="classic-equipment-paths">Broader Classic equipment effects</h2><p>Selected stock crafted armor, racial armor, class quest rewards, enchanted jewelry and named drops have additional effects. These give offensive, defensive and sustain options. Custom rewards and existing effects stay unchanged. See <a href="equipment.html#classic-equipment-paths">Equipment</a>.</p>',
 'recent-changes':'<h2 id="classic-equipment-paths">November 21, 2026: Classic equipment effects</h2><p>Added offensive, defensive and casting effects to 149 stock item families across all four qualities. Crafted and racial armor, class quests, enchanted jewelry and named drops are included. Restored Classic access to the Temple of Solusek Ro. Existing healing strength, custom augments and quest reward quality stay unchanged. Reconnect after maintenance; no client download is needed. See <a href="equipment.html#classic-equipment-paths">Equipment</a>.</p>'}
 for name,body in sections.items():
  path=SITE/'articles'/(name+'.json');a=json.loads(path.read_bytes());a['body']=body+a['body'];a['updated']='2026-11-21';a['sources'].append('docs/items/classic-equipment-paths/; apply only after authorized gameplay deployment');path.write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
 package=ART/(RELEASE+'.tar.gz');subprocess.run([sys.executable,'-B',str(SITE/'build.py'),'--package',str(package)],check=True)
 manifest=json.loads(package.with_suffix('.json').read_bytes());changed=sorted(n for n,pin in manifest.items() if previous.get(n)!=pin)
 assert set(manifest)==set(previous)
 out=dict(release=RELEASE,previous='20261121-aa-purchase-latency-v1',published=False,files=len(manifest),changed=changed,preserved=len(manifest)-len(changed),review='All authored guides reviewed for effect, acquisition, commands, home and generated catalog impact. Existing custom item/zone numeric catalogs contain no changed stock definitions and remain unchanged. Home already links the updated guides. Historical source drift remains review-required.',source=str(SITE))
 (HERE/'wiki-candidate.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf8');print(json.dumps(out))
if __name__=='__main__':main()
