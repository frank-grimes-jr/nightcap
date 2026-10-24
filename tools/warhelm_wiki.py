"""Prepare an unpublished overlay from the current published wiki; never publish."""
import argparse,copy,difflib,hashlib,html,json,shutil,subprocess,sys
from pathlib import Path
from warhelm_content import ROOT,OUT,compile_rows
from dungeon_catalog import items

def prepare(source,target):
    source=source.resolve();target=target.resolve()
    revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=source).decode().strip()
    if target.exists() or source==target or source in target.parents:raise ValueError('Use a new independent staging directory')
    shutil.copytree(source,target,ignore=shutil.ignore_patterns('dist','__pycache__','*.tar.gz','*.pyc'))
    article=target/'articles'
    def save(name,title,summary,body,category='World'):
        data=dict(slug=name,title=title,summary=summary,body=body,category=category,status='Not released',updated='2026-10-24',sources=['docs/quests/warhelm/SPEC.md','docs/quests/warhelm/install-rows.json','docs/quests/warhelm/QA.md'])
        (article/(name+'.json')).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
    common='<h2 id="ashen-compact">The Ashen Compact — not released</h2><p><a href="ashen-compact.html">The Ashen Compact</a> is a prepared level-50 Shadow Knight helmet campaign in a curated Kael expedition. It is not yet installed. Client appearance and complete encounters still require in-game acceptance.</p>'
    additions={name:common for name in ('index','features','recent-changes','unreleased')}
    additions.update({
        'dungeon-modes':common+'<p>Four bosses, personal credit and Raid/Grind journals follow the existing expedition system. The separate story has fourteen objectives and durable progress. Temporary war souls give no loot or XP.</p>',
        'equipment':common+'<p>The Warhelm of the Ashen Compact uses the Paladin helm budget with INT replacing WIS. It requires a held Shadow Knight class. Its new enclosed Classic appearance requires the paired client update.</p>',
        'travel':common+'<p>Drazhul and the Kael Keeper stand together near Befallen in West Commonlands. The public Kael foyer contains services; its Keeper controls private runs. The scoped exception does not unlock Velious globally.</p>',
        'waypoints':common+'<p>The Kael waypoint recalls to its public foyer. It does not enter someone else’s private expedition.</p>',
        'zone-hunt':common+'<p>Cinder of the Ashen Compact is a separate type-22 STA/INT augment family, with the existing 0.5% static-enemy roll and 60/30/8/2 quality weights. The ordinary 48-zone Hunt pools are unchanged.</p>',
        'item-upgrades':common+'<p>Cinder forging uses three identical Base copies, then four Polished or Exalted copies. The helmet and other Kael equipment do not use that augment recipe.</p>',
        'launcher':common+'<p>The staged Warhelm appearance needs the paired Classic client archives. Current launcher releases do not yet contain it; do not manually mix candidate files into the installed client.</p>',
        'camil-vigil':common+'<p>This separate Shadow Knight campaign follows the Vigil’s structure. Camil’s progress and helmet entitlement remain independent.</p>'})
    review=[]
    for path in sorted((source/'articles').glob('*.json')):
        raw=path.read_bytes();data=json.loads(raw);name=path.stem
        entry=dict(path='articles/'+path.name,title=data['title'],sha256=hashlib.sha256(raw).hexdigest(),decision='No change: separate campaign does not alter this guide’s behavior.')
        if name in additions:
            data['body']+=additions[name];data['updated']='2026-10-24';data['sources'].append('docs/quests/warhelm/SPEC.md')
            (article/path.name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
            entry['decision']='Append explicitly unreleased campaign guidance; preserve all existing released content.'
        review.append(entry)
    body='<h2 id="availability">Not released</h2><p>This candidate is built for testing, not yet available on the live server.</p><h2 id="start">A warlord’s challenge</h2><p>At level 50, with Shadow Knight in any held class slot, speak to Drazhul Blackmantle near Befallen in West Commonlands. Accept before creating a run at the adjacent Kael Keeper. Difficulty is intended for a developed Shadow Knight main; reaching level 50 alone does not establish readiness.</p><h2 id="story">The stolen war-fire</h2><p>A renegade war cult in Rallos Zek’s giant city binds stolen souls into its standards. Break its claim and temper its war-fire into your own helm. These characters and events are original Nightcap fiction; you do not kill Rallos Zek or the original Avatar of War.</p><h2 id="route">Fourteen duties</h2><ol>'
    for r in compile_rows()['task_activities']:
        if r['taskid']==9801:body+='<li>'+html.escape(r['description_override'])+'</li>'
    body+='</ol><h2 id="counterplay">Survive the Compact</h2><p>The Herald warns before his warcry: interrupt or leave its radius. Protect Veyra and control three waves. Kharzug summons two owned war souls at half health. Vhalek and the Echo mark your position with three seconds to move more than ten paces or interrupt. Named champions resist charm and fear; their war souls remain controllable. The final Echo can flurry. Full route and build-specific balance still require player testing.</p><h2 id="progress">Keep your progress</h2><p>Be alive, enrolled and nearby for personal boss credit. Pet kills credit eligible owners. Completed duties survive reconnects and run resets; removing the Tasks display does not erase them. Make room for both story and dungeon journals. Return to Drazhul after tempering the helm. A full inventory leaves delivery pending; a durable receipt prevents duplicate claims.</p><h2 id="rewards">The Warhelm</h2><p><a href="item-990510.html">Warhelm of the Ashen Compact</a> is a one-time custom reward based on the Warhelm of Rallos Zek appearance. Camil’s item remains separate. <a href="zone-kael.html">Browse all fourteen proposed Kael rewards</a>. The enclosed Classic model package is staged; native rendering and animation acceptance remain pending.</p>'
    save('ashen-compact','The Ashen Compact','A demanding Shadow Knight helmet campaign in Kael · Not released.',body)
    rows=compile_rows()['items']+[r['values'] for r in items() if r['source']=='kael']
    self_ids={r['id'] for r in rows};assert len(rows)==len(self_ids)==14
    links=[]
    slots=['Charm','Ear','Head','Face','Ear','Neck','Shoulders','Arms','Back','Wrist','Wrist','Range','Hands','Primary','Secondary','Finger','Finger','Chest','Legs','Feet','Waist','Ammo']
    labels={'ac':'AC','hp':'HP','mana':'Mana','asta':'STA','aint':'INT','awis':'WIS','astr':'STR','adex':'DEX','aagi':'AGI','acha':'CHA','heroic_sta':'Heroic STA','heroic_int':'Heroic INT','mr':'Magic resist','fr':'Fire resist','cr':'Cold resist','pr':'Poison resist','dr':'Disease resist','damage':'Damage','delay':'Delay'}
    for r in rows:
        id=r['id'];kind='Quest helmet' if id==990510 else 'Augment' if 961020<=id<=961023 else 'Miniboss relic' if 961030<=id<=961032 else 'Final Raid reward'
        values={'Item ID':id,'Family':kind,'Required level':r['reqlevel'],'Recommended level':r['reclevel'],'Slots':', '.join(dict.fromkeys(s for i,s in enumerate(slots) if r['slots']&(1<<i))),'Classes':'Shadow Knight' if r['classes']==16 else 'All held classes'}
        values.update({label:r[key] for key,label in labels.items() if r.get(key,0)})
        if kind=='Augment':values['Socket type']=22
        table='<table><caption>Proposed values; not released</caption><tbody>'+''.join('<tr><th>'+html.escape(str(k))+'</th><td>'+html.escape(str(v))+'</td></tr>' for k,v in values.items())+'</tbody></table>'
        source_text='Drazhul, once after the story' if id==990510 else 'Eligible static custom enemies: 0.5% family roll, then Base60/Polished30/Exalted8/Ascension2 percent' if kind=='Augment' else 'The corresponding first, second or third named boss: 35% custom-item roll' if kind=='Miniboss relic' else 'The Echo of Endless War in Raid mode, under the existing final Raid loot rules'
        save('item-'+str(id),r['Name'],kind+' · Kael · Not released.',table+'<h2 id="source">Source</h2><p>'+source_text+'. See <a href="zone-kael.html">Kael reward rules</a>.</p>','Equipment')
        links.append(f'<li><a href="item-{id}.html">{html.escape(r["Name"])}</a> · {kind}</li>')
    save('zone-kael','Kael Drakkel — The Ashen Compact','Curated level-50 Shadow Knight expedition · Not released.','<p>Enter through the Keeper near Befallen. <a href="ashen-compact.html">Start the Compact with Drazhul first</a>. Stock Velious enemies, drops and exits are excluded from this private campaign.</p><h2 id="rewards">Proposed rewards</h2><ul>'+''.join(links)+'</ul><p>Temporary encounter actors yield no loot or XP. Cinder augments follow the existing type-22 forging recipe; other equipment does not. Full encounter and appearance acceptance remain pending.</p>')
    catalog=target/'catalog.py';code=catalog.read_text();needle='    return articles\n';assert code.count(needle)==1
    code=code.replace(needle,"    next(a for a in articles if a['slug']=='zones')['body'] += '<h2 id=\"ashen-compact\">In development</h2><p><a href=\"zone-kael.html\">Kael: The Ashen Compact</a> is a separate curated campaign, not released.</p>'\n"+needle);catalog.write_text(code)
    patch=[]
    for path in sorted(target.rglob('*')):
        if not path.is_file():continue
        rel=path.relative_to(target);old=source/rel
        if old.exists() and old.read_bytes()==path.read_bytes():continue
        if path.suffix not in ('.json','.py'):raise ValueError('Unexpected wiki output '+str(rel))
        patch.extend(difflib.unified_diff(old.read_text(encoding='utf8').splitlines(True) if old.exists() else [],path.read_text(encoding='utf8').splitlines(True),fromfile='a/wiki/'+rel.as_posix() if old.exists() else '/dev/null',tofile='b/wiki/'+rel.as_posix()))
    (OUT/'wiki-candidate.patch').write_text(''.join(patch),encoding='utf8')
    (OUT/'wiki-review.json').write_text(json.dumps(dict(status='Unpublished overlay; rebase against then-current published source before any authorized publication',basis=str(source),base_commit=revision,articles=review,generated_routes='Existing447 unchanged; 14new item pages and Kael route added, separate from48ClassicHunt pools',new_story='ashen-compact',production_changed=False),indent=2)+'\n')
    print(json.dumps(dict(target=str(target),existing_guides=len(review),new_items=14,patch=str(OUT/'wiki-candidate.patch'))))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();prepare(a.source,a.output)
