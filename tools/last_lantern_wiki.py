"""Project only reachable campaign rewards and maintain the owning player guide."""
import html,json,re,shutil
from pathlib import Path
from last_lantern_content import ROOT,compile_items,compile_tasks,FIT_NAMES,SLOT_NAMES
from epic05 import load_catalog

WIKI=ROOT/'wiki'
OUT=ROOT/'docs/adventure-journal/release-20261107'
SOURCE='docs/adventure-journal/release-20261107/README.md and verified release receipts; normal-player appearance/encounter acceptance remains open'

def write(wiki,name,data):
    (wiki/'articles'/f'{name}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def article(slug,title,summary,body,category='Quests'):
    return dict(slug=slug,title=title,summary=summary,body=body,category=category,status='Live testing',updated='2026-11-07',sources=[SOURCE])

def guide():
    e=html.escape;catalog=load_catalog();tasks,goals=compile_tasks()
    body='''<p>Mera Vell has three entrance reports and the same name scratched out of every one. Captain Selene’s company entered the dark together; somebody sold their names to come back alone. Carry the lantern, bring the missing voices home, and decide how they will be remembered.</p>
<h2 id="begin">Begin in East Commonlands</h2><p>At level20, hail the <strong>Ancient Chronicler</strong> in the tunnel, near <code>/loc -1585, -215, 4</code>, and choose the Adventure Journal. Your normal Tasks window tracks the chapters. The story continues through the current level50 endgame. Complete the three opening chapters, earn one oath path, then follow eight further chapters.</p><p>Fully exit EverQuest and press <strong>Play</strong> in the launcher for signed update2026110701 before starting. Mera Vell, Oren Lanternwright and Tovin stand nearby. Oren handles earned equipment; the Chronicler offers chapters, oath attunement and journal expeditions.</p>
<h2 id="chapters">The journey</h2><p>These are minimum levels. Prepare gear, trained skills, recovery and legal AAs for the later encounters; reaching the level alone does not finish the story.</p><div class="table-scroll"><table><caption>Twelve chapters in one playthrough</caption><thead><tr><th>Chapter</th><th>Level</th><th>Journey</th><th>Earned armor</th></tr></thead><tbody>'''
    names={9500:'The First Pages',9501:'Beneath the Surface',9502:'Steel and Sorcery',9508:'A Name Beneath the Moss',9509:'What the Fire Kept',9510:"The Captain’s Last Watch",9511:'The Debt of the Living',9512:'Where Courage Ends',9513:'The Weight of a Name',9514:'A Light Carried Forward',9515:'The Last Lantern'}
    journeys={9500:'Visit Upper Guk, Unrest and Runnyeye; read each entrance courier’s note and return.',9501:'Win the field trials, then rescue Tovin through three waves in an Unrest company memory.',9502:'Recover the named accounts and let Mera compare the company records.',9508:'Recover Mera’s satchel in Lower Guk and escort her through three retreat checkpoints.',9509:'Defeat the Solusek B lieutenants and defend Oren’s furnace through three waves.',9510:'Hear Selene’s last orders in Cazic-Thule and hold the retreat positions.',9511:'Recover the stolen roster in The Hole and bring Mera home.',9512:'Release three bound names in Fear, then defeat their pursuer.',9513:'Break the chosen guard in Hate and save the recorded names.',9514:'Gather the company in Commonlands and choose a memorial inscription.',9515:'Break the Witness’s bindings, defend the standard and face the Hollow Witness in Hate. Return to the campfire.'}
    awards={9500:'Boots',9501:'Gloves',9502:'Left bracer',9508:'Right bracer',9509:'Armguards + Oathbound refits',9510:'Leggings',9511:'—',9512:'Helm + Restored refits',9513:'—',9514:'—',9515:'Chest/robe + Complete refits'}
    ordered=[9500,9501,9502,'path',9508,9509,9510,9511,9512,9513,9514,9515]
    byid={t['id']:t for t in tasks}
    for number,identity in enumerate(ordered,1):
        if identity=='path':row=(number,35,'Choose one oath trial: Guardian, Striker, Arcanist, Warden or Binder.','Wayfarer’s Oath charm')
        else:row=(number,byid[identity]['min_level'],e(names[identity])+': '+e(journeys[identity]),e(awards[identity]))
        body+=f'<tr><td>{row[0]}</td><td>{row[1]}</td><td>{row[2]}</td><td>{row[3]}</td></tr>'
    body+='</tbody></table></div><h2 id="oath-paths">Choose your oath</h2><p>Any class combination can earn an oath. One completed path opens the rest of the campaign. Further paths are optional: they add attunement choices to the same charm, with one shared ten-minute recovery.</p>'
    for path in catalog['paths']:
        objectives='; '.join(o['label'] for o in path['objectives'])
        body+=f'<h3 id="{path["key"]}">{e(path["title"])}</h3><p>{e(objectives)}. Return to the Chronicler and claim or attune your oath.</p><p><strong>{e(path["ability"])}:</strong> {e(path["effect_text"])}</p>'
    body+='''<h2 id="memories">Private company memories</h2><p>The Chronicler opens separate, hour-long journal expeditions for the Unrest rescue and later field chapters. These reconstruct the company’s past; Tovin’s presence in Commonlands is part of the story. They do not replace public zones or Keeper Raid/Grind runs. Solo characters and groups of up to six can enter; SSF characters enter alone.</p><p>Hail each remembered voice and choose its response. Stay with an escort, lead it to the displayed checkpoints, draw pursuers away and heal the companion when needed. Three waves must be survived in order. Dead, distant or disconnected characters receive no credit; combat credit also follows the killer’s current native party, including owned pet and swarm attribution. A helper needs their own active chapter and prerequisites to advance. Late helpers may replay earlier checkpoints.</p><p>If a defense fails, speak with the company to try the memory again. Hail the lanternlit wayfarer to return to Commonlands. These actors grant no repeatable XP or loot. Durable Tasks retain completed checkpoints; no reward is earned by merely entering a scene.</p>
<h2 id="finale">The Hollow Witness</h2><p>The finale has three parts: answer the bindings, defend the company standard through three waves, then confront its recorder. When the Witness marks your feet, move at least ten units within three seconds or stun him before the brand resolves. Watch the shout and yellow message. Return to the Commonlands campfire after the victory to finish the chapter, earn the final armor step and unlock <strong>the Lanternbearer</strong> title.</p>
<h2 id="outfit">An outfit earned along the road</h2><p>Earn boots, gloves, two bracers, arms, legs, head and chest. These are useful progression items with a coordinated slate-and-blue look. Oren offers woven, leather, chain or plate pieces when one of your held classes permits that fit. The woven chest uses an existing robe appearance. Your race and client models determine the rendered result; full appearance checks remain in live testing.</p><p>Return to Oren after the level40 furnace chapter, level46 Fear chapter and final level50 campfire for the Oathbound, Restored and Complete refits. Refitting an earned piece preserves augments, custom dye, binding and ornaments. Finish the chapter first: a new level alone does not unlock its refit. Choose the armor fit and refit each eligible piece through Oren’s links; this does not automatically equip an outfit.</p><p>Campaign equipment is personal, cannot be traded, transferred to another character, given to pets or sold for coin. A missing receipted item is not replaced for free; recover it from your bank or corpse before refitting. Do not destroy a piece to change its fit. The six major armor pieces have a type22 augment socket; bracers do not. No armor set bonus, haste, focus, heroic stats or stacked oath clicks are added. Harder endgame loot retains its progression role.</p><p><a href="last-lantern-equipment.html">All reachable armor grades, exact stats and acquisition</a> · <a href="item-900501.html">Wayfarer’s Oath</a></p>
<h2 id="testing">Live testing</h2><p>The campaign is installed for live QA. Native checks and measured earned-gear combat runs do not complete player acceptance of all paths, escort behavior, race/gender armor rendering or the full finale. Report the chapter, zone, party, class combination and what happened if progress stalls.</p>'''
    return article('adventure-journal','Wayfarer’s Oath: The Last Lantern','A twelve-chapter level20–50 story, five oath paths and a complete earned armor outfit.',body)

def projection():
    result=[]
    for row in compile_items():
        n=row['id']-964000;grade=(n%32)//8;slot=n%8
        first=0 if slot<4 else 1 if slot<6 else 2 if slot==6 else 3
        if grade<first:continue
        result.append(row)
    assert len(result)==100
    return dict(status='Live testing',updated='2026-11-07',sources=[SOURCE],items=result)

def maintain(wiki):
    write(wiki,'adventure-journal',guide())
    (wiki/'last-lantern-catalog.json').write_text(json.dumps(projection(),indent=2)+'\n')
    for name in ('features','index','equipment','unreleased','recent-changes'):
        p=wiki/'articles'/f'{name}.json';a=json.loads(p.read_text(encoding='utf-8'));body=a['body']
        # Replace only the superseded Adventure Journal preview; preserve anchors.
        body=re.sub(r'<h2 id="(?:journal|adventure-journal|adventure-journal-endgame)[^"]*".*?(?=<h2 |\Z)','',body,flags=re.S)
        if name=='features':
            body=re.sub(r'<(?:li|p)[^>]*>[^<]*(?:<[^>]+>)*Adventure Journal.*?</(?:li|p)>','',body,flags=re.S)
            body+='<h2 id="adventure-journal">A story and an outfit to level50</h2><p><a href="adventure-journal.html">Wayfarer’s Oath: The Last Lantern</a> follows a lost company through twelve chapters, a choice of five oath paths, private memory encounters and eight useful coordinated armor pieces. Live testing.</p>'
        elif name=='index':body+='<p>Looking for a continuing story? Begin <a href="adventure-journal.html">The Last Lantern</a> at level20 and carry an earned armor outfit through level50.</p>'
        elif name=='equipment':body+='<h2 id="last-lantern">Last Lantern campaign armor</h2><p>Earn eight personal armor pieces over the <a href="adventure-journal.html">level20–50 Adventure Journal</a>, with legal woven, leather, chain or plate fits and earned refits. <a href="last-lantern-equipment.html">Exact stats and chapters</a>. Live testing; harder endgame loot remains worthwhile.</p>'
        elif name=='unreleased':body+='<h2 id="adventure-journal">Adventure Journal — live testing</h2><p><a href="adventure-journal.html">The Last Lantern campaign</a>, its oath charm and progression outfit are installed. Full player encounter, pathing and rendered armor acceptance remain open.</p>'
        else:body='<h2 id="last-lantern-20261107">November7: The Last Lantern — live testing</h2><p>The Adventure Journal now continues to level50 with recurring companions, eight private company memories, five oath paths, an eight-piece progression outfit, earned40/46/50 refits, a final Witness encounter and a memorial/title. Signed client2026110701 adds the paired oath spells and client notes. Fully exit EverQuest and press Play. <a href="adventure-journal.html">Start, chapters and rewards</a>. Full player appearance and encounter acceptance remain open.</p>\n'+body
        a.update(body=body,updated='2026-11-07');a['sources']=list(dict.fromkeys(a['sources']+[SOURCE]));write(wiki,name,a)

def main():
    if 'from last_lantern_catalog import' in (WIKI/'catalog.py').read_text(encoding='utf-8'):
        raise SystemExit('One-time projection already installed; edit its maintained source files directly.')
    maintain(WIKI)
    # Publication is built over the byte-reproduced current public source, keeping
    # unrelated main previews unpublished. Its own articles get the same scoped edits.
    public=ROOT/'artifacts/last-lantern-20261107/wiki-source/wiki'
    maintain(public)
    for name in ('last_lantern_catalog.py',):shutil.copyfile(WIKI/name,public/name)
    for target in (WIKI,public):
        p=target/'catalog.py';s=p.read_text(encoding='utf-8')
        needle='    return articles\n';assert s.count(needle)==1
        s=s.replace(needle,"    from last_lantern_catalog import articles as lantern_articles\n    articles.extend(lantern_articles(json.loads((ROOT/'last-lantern-catalog.json').read_text(encoding='utf-8'))))\n"+needle)
        p.write_text(s,encoding='utf-8')

if __name__=='__main__':main()
