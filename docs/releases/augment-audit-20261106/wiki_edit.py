"""Prepare the released public projection over the byte-reproduced live wiki source."""
import html
import json
from pathlib import Path
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
WIKI=ROOT/'artifacts/augment-audit-release/wiki-source/wiki'
AUDIT=ROOT/'docs/audits/augments-20261106'
SOURCE='docs/releases/augment-audit-20261106/README.md'
ELIGIBILITY=('Any unowned, killable NPC in an enabled augment zone can roll its augment, including guards, named and quest NPCs, killable merchants and scripted combat adds. '
             'Player-owned/charmed pets, mercenaries, swarm pets, protected noncombat actors and restored corpses do not reroll. Native corpse ownership and encounter access still apply. '
             'Augments roll at 1.5%; approved native equipment sources keep their separate 0.5% chance and level/night restrictions.')


def load(path):return json.loads(path.read_text(encoding='utf-8'))


def save(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')


def stats(item,after):
    result=dict(item['stats'])
    for field,label in [('avoidance','Avoidance'),('accuracy','Accuracy'),('shielding','Shielding (%)'),
                        ('spellshield','Spell Shielding (%)'),('spelldmg','Spell Damage'),('healamt','Healing Amount')]:
        if int(after[field]):result[label]=int(after[field])
    if int(after['focuseffect'])>0:
        effect=int(after['focuseffect'])
        if effect in (4303,2341):result['Spell haste focus (%)']=15 if effect==2341 else 7
        if effect in (4306,2344):result['Mana preservation maximum (%)']=10 if effect==2344 else 5
    if after['worneffect']=='3660':result['Faerune']=1
    if after['worneffect']=='3889':result['Dodge modifier (%)']=10
    if int(after['id']) in [base+t for base in (940040,940280,940528) for t in (1,2,3)]:
        result['Hunt shield block (%)']=2 if int(after['id'])%4==3 else 1
    return result


def paragraph(body,needle,replacement):
    matches=[m for m in re.finditer(r'<p[^>]*>.*?</p>',body,re.S) if needle in m[0]]
    assert len(matches)==1,(needle,len(matches))
    m=matches[0];return body[:m.start()]+'<p>'+replacement+'</p>'+body[m.end():]


def main():
    data=load(WIKI/'catalog.json');rows={int(r['after']['id']):r['after'] for r in load(AUDIT/'item-preimages.json')}
    families=load(AUDIT/'summary.json')['families']
    for item in data['items']:
        if item['kind']=='Augment':item['stats']=stats(item,rows[item['id']]);item['icon']=int(rows[item['id']]['icon'])
    for slug in ('cazicthule','hateplaneb'):
        family=next(f for f in families if f['zone']==slug)
        assert all(z['slug']!=slug for z in data['zones'])
        data['zones'].append(dict(slug=slug,name='Cazic-Thule' if slug=='cazicthule' else 'Plane of Hate: newer layout',slot='Armor sockets',augment_only=True))
        for tier in range(4):
            after=rows[family['base']+tier]
            raw={'HP':int(after['hp']),'Mana':int(after['mana'])}
            for key,label in [('ac','Armor class'),('heroic_sta','Heroic STA'),('heroic_int','Heroic INT'),('heroic_wis','Heroic WIS'),('heroic_agi','Heroic AGI'),('heroic_dex','Heroic DEX')]:
                if int(after[key]):raw[label]=int(after[key])
            item=dict(id=int(after['id']),zone=slug,kind='Augment',tier=tier,name=after['Name'],required_level=int(after['reqlevel']),
                      recommended_level=int(after['reclevel']),slot='Head, arms, hands, chest, legs, feet',socket=False,stats=raw,icon=int(after['icon']))
            item['stats']=stats(item,after);data['items'].append(item)
    for item in data['chapterhouse']['items']:
        if item['kind']=='Augment':item['stats']=stats(item,rows[item['id']]);item['source']='Any unowned killable Chapterhouse enemy, including scripted combat adds (1.5% family roll)'
    data['updated']='2026-11-06';data['sources'].append(SOURCE);data['chapterhouse']['updated']='2026-11-06';save(WIKI/'catalog.json',data)
    catalog=WIKI/'catalog.py';text=catalog.read_text(encoding='utf-8')
    old='Only the zone’s approved native enemies qualify. Pets, merchants, hub residents, summoned copies and city services do not. There is no guaranteed drop or pity timer.'
    assert text.count(old)==1;text=text.replace(old,ELIGIBILITY+' There is no guaranteed drop or pity timer.')
    text=text.replace('Eligible native enemies have an independent','Unowned killable enemies have an independent')
    text=text.replace('for the gear family. Both may drop together.','for the gear family when they qualify as approved equipment sources. Both may drop together.')
    # The two newly enabled pools have no public equipment sources. Do not invent
    # wearable drops or duplicate original-Hate gear identities in the catalog.
    needle="        if z['slug'] == 'highkeep':"
    addition="        if z.get('augment_only'):\n            body += '<p><strong>Augment-only pool:</strong> only the augment family listed here drops. There are no approved public wearable sources in this pool. Managed newer Hate runs retain the original Hate equipment family and its source rules.</p>'\n"
    assert text.count(needle)==1;text=text.replace(needle,addition+needle)
    text=text.replace('Kithicor requires eligible nighttime undead.','Kithicor’s nighttime-undead restriction applies to equipment only; augments can drop day or night.')
    text=text.replace('Both reward families, at every quality','Available reward families, at every quality')
    text=text.replace('all 48','all 50').replace('48 enabled','50 enabled')
    text=text.replace('Each listed zone has one custom augment family and one equipment family.','Each listed zone has a custom augment family. The original 48 zones also retain their equipment families; Cazic-Thule and newer Hate add augment-only pools.')
    text=text.replace('Highpass, Splitpaw, Cazic-Thule, Jaggedpine, Nedaria, Hate B and both tutorial zones','Highpass, Splitpaw, Jaggedpine, Nedaria and both tutorial zones')
    text=text.replace('48 gear families. 48 augments.','48 gear families. 50 augments.')
    catalog.write_text(text,encoding='utf-8')
    chapter=WIKI/'chapterhouse_catalog.py';text=chapter.read_text(encoding='utf-8').replace('Eligible static custom enemies have a 0.5% augment roll','Any unowned killable enemy, including scripted combat adds, has a 1.5% augment roll')
    text=text.replace('Summoned encounter shades award no loot or experience.','Unowned encounter shades can roll the augment; they still grant no experience or miniboss relics.')
    chapter.write_text(text,encoding='utf-8')
    for name in ('zone-hunt','equipment','features','camil-vigil','zone-kael','ashen-compact'):
        path=WIKI/'articles'/(name+'.json');article=load(path);body=article['body']
        if name=='zone-hunt':
            body=paragraph(body,'Forty-eight enabled','Fifty Classic zones offer an augment family; the original48 also retain their equipment families. Cazic-Thule and the newer Hate layout add augment-only pools. Live testing. Browse the <a href="zones.html">zone directory</a> or <a href="items.html">item index</a>.')
            body=paragraph(body,'Only approved native enemies qualify.',ELIGIBILITY)
            body=paragraph(body,'Chapterhouse adds Ember of the First Dawn','Chapterhouse adds Ember of the First Dawn, a level-50 type-22 armor augment with four qualities and a healing specialty. Any unowned killable enemy, including scripted combat adds, has a 1.5% family roll. Existing Hunt headroom/forging and static-only35% miniboss relic rolls remain. <a href="zone-chapterhouse.html">Published rewards</a>.')
            body=paragraph(body,'Cinder of the Ashen Compact is a separate','Cinder of the Ashen Compact is a separate type-22 STA/INT family with mana-preservation focus at higher qualities. Its managed expedition uses a1.5% family roll from any unowned killable enemy, including scripted adds, with60/30/8/2quality weights.')
        if name=='equipment':
            body=paragraph(body,'Each eligible native enemy has a separate',ELIGIBILITY+' Qualities remain Base60%, Polished30%, Exalted8%, Ascension2%; no guaranteed drop or pity counter. <a href="zones.html">Zone rewards</a>.')
        if name=='features':body=body.replace('Hunt new equipment and heroic augments across 48 Classic zones.','Hunt heroic augments across50 Classic zones, with equipment families retained in the original48.').replace('Each zone has its own reward families and four qualities,','Zone rewards have four qualities and balanced secondary specialties,')
        if name=='camil-vigil':
            body=paragraph(body,'Static curated enemies have a 0.5% augment roll','Ember of the First Dawn retains its published primary/heroic budgets and now adds Healing Amount. Any unowned killable Chapterhouse enemy, including scripted adds, has a1.5% augment roll;60/30/8/2qualities and static-only35% miniboss relic rolls remain. <a href="zone-chapterhouse.html">Current reward values</a>.')
        if name=='zone-kael':body=paragraph(body,'Temporary encounter actors yield no loot or XP.','Unowned scripted combat actors can roll Cinder augments at1.5%; they still grant no XP or miniboss relics. Type-22 forging and other equipment rules remain. Full encounter and appearance acceptance remain pending.')
        body+='<p><a href="augment-audit.html">All top-quality augments, drop zones and secondary specialties</a> — live testing; gameplay acceptance remains open.</p>'
        article.update(body=body,updated='2026-11-06');article['sources'].append(SOURCE);save(path,article)
    for tier in range(4):
        path=WIKI/'articles'/f'item-{961020+tier}.json';article=load(path);after=rows[961020+tier]
        values={'Item ID':int(after['id']),'Family':'Augment','Required level':50,'Recommended level':50,'Slots':'Head, Arms, Hands, Chest, Legs, Feet','Classes':'All held classes','AC':int(after['ac']),'HP':int(after['hp']),'Mana':int(after['mana']),'Heroic STA':int(after['heroic_sta']),'Heroic INT':int(after['heroic_int'])}
        values.update(stats({'stats':{}},after))
        table='<table class="item-stats"><caption>Released values; gameplay acceptance pending</caption><tbody>'+''.join('<tr><th scope="row">'+html.escape(str(k))+'</th><td>'+html.escape(str(v))+'</td></tr>' for k,v in values.items())+'</tbody></table>'
        article['body']=re.sub(r'<table.*?</table>',lambda _:table,article['body'],count=1,flags=re.S)
        article['body']=paragraph(article['body'],'Eligible static custom enemies:', 'Any unowned killable enemy in the managed Ashen Compact expedition, including scripted combat adds:1.5% family roll, then Base60/Polished30/Exalted8/Ascension2percent. <a href="zone-kael.html">Kael reward rules</a>.')
        article['updated']='2026-11-06';article['sources'].append(SOURCE);save(path,article)
    article=load(ROOT/'wiki/articles/augment-audit.json')
    article.update(status='Live testing',updated='2026-11-06',sources=[SOURCE])
    body=article['body'];body=re.sub(r'<p class="notice">.*?</p>','<p class="notice"><strong>Live testing:</strong> the November6 release broadens augment drops, adds balanced secondary specialties and replaces armor/default icons with stock gems/crystals/orbs. Owner approved the artwork; gameplay and balance acceptance remain open.</p>',body,count=1,flags=re.S)
    body=body.replace('The candidate uses','The release uses').replace('The candidate enables','The release enables').replace('The six other disabled pools remain disabled.','Six access-check pools remain disabled.').replace('move from0.5%','move from0.5%').replace('Candidate specialty','Secondary specialty').replace('Disabled; candidate enables','Enabled')
    body=body.replace('Current live catalog values remain below their normal pages.','Current published values appear on item pages.')
    article['body']=body;article['summary']='Every top-quality augment, its drop zone and secondary specialty.';save(WIKI/'articles/augment-audit.json',article)
    path=WIKI/'articles/recent-changes.json';article=load(path)
    article['body']='<h2 id="augment-audit-20261106">November6: zone augments and exotic icons — live testing</h2><p>Augments can drop from any unowned killable NPC in enabled zones, including guards, named enemies, killable merchants and scripted adds. New secondary specialties and gem/crystal icons cover all qualities. Cazic-Thule/newer Hate augment pools enable; both expeditions now roll1.5%. Artwork is approved; gameplay QA remains open. <a href="augment-audit.html">Full list and limits</a>.</p>'+article['body'];article['updated']='2026-11-06';article['sources'].append(SOURCE);save(path,article)
    print(json.dumps({'prepared_zones':len(data['zones']),'classic_variants':len(data['items']),'publication':'pending verified runtime activation'}))


if __name__=='__main__':main()
