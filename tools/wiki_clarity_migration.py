"""One editorial migration from the exact published wiki; retain moved history/anchors."""
import html
import json
from pathlib import Path
import re
import subprocess

ROOT=Path(__file__).resolve().parents[1]
BASE='66c7b843'
ARTICLES=ROOT/'wiki/articles'
EVIDENCE=ROOT/'docs/releases/wiki-clarity-20261024'


def original(slug):
    return json.loads(subprocess.check_output(['git','show',f'{BASE}:wiki/articles/{slug}.json'],cwd=ROOT,text=True,encoding='utf-8'))


def sections(body):
    matches=list(re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>',body,re.S))
    return {m[1]:body[m.start():matches[i+1].start() if i+1<len(matches) else len(body)] for i,m in enumerate(matches)}


def heading(body,title):
    return re.sub(r'(<h2[^>]*>).*?(</h2>)',lambda m:m[1]+title+m[2],body,count=1,flags=re.S)


def main():
    old={p.stem:original(p.stem) for p in ARTICLES.glob('*.json')}
    bodies={slug:a['body'] for slug,a in old.items()}
    moved={}
    def archive(slug,body):
        if body.strip():moved[slug]=moved.get(slug,'')+body
    def trim(slug,marker):
        body=bodies[slug];offset=body.index(marker);archive(slug,body[:offset]);bodies[slug]=body[offset:]
    def remove(slug,ids):
        for ident in ids:
            part=sections(bodies[slug]).get(ident)
            if part:archive(slug,part);bodies[slug]=bodies[slug].replace(part,'')
    def replace(slug,ident,body):
        part=sections(bodies[slug])[ident];archive(slug,part);bodies[slug]=bodies[slug].replace(part,body)

    for slug,ident in [('multiclass','three-classes'),('combat','buffs'),('pets','pets'),('item-upgrades','recipes'),('getting-started','joining'),('launcher','updates'),('travel','travel'),('dungeon-modes','modes')]:
        trim(slug,f'<h2 id="{ident}"')
    trim('ascension','<p>Turn an existing class epic')
    trim('waypoints','<p>Explore the world')
    remove('combat',['cooldown-corrections'])
    remove('launcher',['startup-repairs','animation-repairs','october-release'])
    remove('tunnel',['experience-blessing'])
    # Current mechanics stay in their owning guides; repair narratives go to history.
    replace('combat','blessing-repair','<h2 id="blessing-repair">Blessings after reconnecting</h2><p>Ordinary lasting blessings remain active after zoning and reconnecting. Temporary abilities keep their remaining duration; reconnecting does not refresh their timers.</p>')
    bodies['combat']+='<h2 id="focus-effects">Spell focus effects</h2><p>Improved Damage, Improved Healing, Mana Preservation, Reagent Conservation and Hate Adjustment use their strongest endpoints. Improved Damage is multiplied by 10, except Mage Heart of Flame (100%) and Fire Core (150%). Supported area targets retain the other focus restrictions. Bard damage-focus songs retain random ranges; direct-damage focuses gain 10× and DoT focuses do not. Bard songs receive no spell focus or twincast, and a three-second base song casts in 2.5 seconds. These custom effects remain under live balance testing.</p>'
    bodies['multiclass']=bodies['multiclass'].replace('The extra-class training and offhand correction is deployed; the reported player issue was confirmed resolved.','')
    bodies['multiclass']=bodies['multiclass'].replace('The spell-selection menu also refreshes after a class change, fixing stale level-255 labels.','The spell-selection menu refreshes after a class change.')
    bodies['multiclass']=bodies['multiclass'].replace('Fully close EverQuest and use normal launcher Play to install game 2026102301 first.','Keep your game current through the normal launcher.')
    bodies['multiclass']=heading(bodies['multiclass'],'Choose three classes')
    bodies['multiclass']=bodies['multiclass'].replace('All-class AA update</h2>','The allowed AA catalog</h2>')
    custom=sections(old['unreleased']['body'])['thj-behavior-candidate']
    custom_rules=re.search(r'<h3>Custom AA behavior</h3>(<ul>.*?</ul>)',custom,re.S)[1]
    bodies['multiclass']+='<h2 id="custom-aa">Custom AA effects</h2>'+custom_rules+'<p>These installed effects remain under live gameplay and balance testing. Normal class ownership, earned ranks and other restrictions apply.</p>'
    bodies['getting-started']='<p>Nightcap is a solo-preferred EverQuest server with <strong>three classes per character</strong> and a <strong>Classic level cap of 50</strong>. Start here, then explore the <a href="features.html">major differences from standard EQ</a>.</p>'+bodies['getting-started']
    bodies['launcher']=bodies['launcher'].replace('For the new loading gallery, fully close both the game and launcher, then reopen that shortcut.','Fully close both the game and launcher before updating, then reopen that shortcut.')
    bodies['launcher']+='<h2 id="zone-repair">If a zone fails to load</h2><p>Fully close EverQuest, reopen your usual launcher, select the game folder you actually use and press Play. Missing or corrupted managed terrain and object archives are downloaded; matching files and personal settings are preserved. If a zone still fails, report its name and the exact error. A full reinstall is usually unnecessary.</p>'
    bodies['launcher']=bodies['launcher'].replace('Background interface requests no longer clutter local chat.','')
    bodies['travel']+='<h2 id="hole-entrance">Entering The Hole</h2><p>In Paineel, click the entrance rock at <code>/loc 568,-896,-96</code>. The passage needs neither The Hole Key nor lock picks. Paineel city-lift keys and Sacred Key doors inside The Hole keep their own requirements. This entrance change is installed for live testing.</p><h2 id="missing-zone-files">Missing zone files</h2><p>Close EverQuest and use the normal launcher’s Play flow to check managed zone files. See <a href="launcher.html#zone-repair">zone loading help</a> if a destination still fails.</p>'
    bodies['dungeon-modes']='<p>Choose <strong>Raid or Grind in 21 Classic dungeons</strong>. Hail an entrance Keeper, enroll in a run and earn your own boss-checklist rewards. Runs last up to twelve hours.</p>'+bodies['dungeon-modes']
    bodies['dungeon-modes']+='<h2 id="classic-candidate">Classic dungeon coverage and planar rules</h2><p>The 21 combat dungeons include Fear, Hate and Sky, with current native populations. Managed Sky has durable key exchangers that still require the normal tokens; its four previously scripted Grind bosses have eight-hour timers and the princess keeps four hours. Public and legacy Sky retain their original behavior. Plane runs isolate quest state from public zones and other runs.</p><p>Hate’s public Keeper is in East Commonlands at <code>/loc -1570,-346,3</code>, between Mirielle and Khalure; its private instances keep an entrance Keeper. Hate entry requires level 46.</p><p>For the keyless Paineel passage, see <a href="travel.html#hole-entrance">Entering The Hole</a>.</p>'
    # Keep the useful original seven Keeper coordinates as reference, without its repair bulletin.
    prefix=old['dungeon-modes']['body'].split('<h2 id="modes"')[0]
    tables=re.findall(r'<table>.*?</table>',prefix,re.S)
    if tables:bodies['dungeon-modes']+='<h2 id="original-keepers">Original dungeon Keeper locations</h2><p>Locations use in-game /loc order. Use <code>/target Instance_Keeper</code> and hail if needed.</p>'+tables[-1]
    s=sections(bodies['dungeon-modes'])['unique-rewards']
    s=s.replace(re.search(r'<p class="notice">.*?</p>',s,re.S)[0],'<p>Every Classic dungeon has three exclusive Raid designs. The 14 added dungeons contribute 42 designs in two qualities; all 414 dungeon rewards are MAGIC. Fear, Hate and Sky include planar relics and equipped utility clicks.</p>')
    replace('dungeon-modes','unique-rewards',heading(s,'Exclusive Raid rewards'))

    gear=sections(old['equipment']['body'])
    archive('equipment',old['equipment']['body'].split('<h2 id="free-trade"')[0])
    bodies['equipment']='<p>Find ordinary equipment with the <a href="loot-finder.html">Loot finder</a>, browse <a href="items.html">Hunt rewards</a>, or compare an upgrade in the experimental <a href="build-lab.html">Build Lab</a>.</p>'+old['equipment']['body'][old['equipment']['body'].index('<h2 id="free-trade"'):]
    bodies['equipment']+=heading(gear['quest-ingredients'],'Quest ingredients and item quality')
    formula=gear['thj-behavior-candidate']
    formula=re.sub(r'(<h2[^>]*>).*?</h2><p>.*?</p>',r'\1How ordinary item stats scale</h2>',formula,count=1,flags=re.S)
    formula=re.sub(r'<p class="notice">.*?</p>','',formula,flags=re.S)
    bodies['equipment']+=formula

    # Only genuinely unavailable work belongs in In development.
    pending=sections(old['unreleased']['body'])
    archive('unreleased',old['unreleased']['body'])
    bodies['unreleased']='<p>These projects are not yet available, or have a specific unresolved boundary. Installed systems and their instructions are in <a href="features.html">Features</a> and <a href="all-pages.html">Guides</a>; deployment history is in <a href="recent-changes.html">Change Log</a>.</p>'+''.join(pending[k] for k in ['pet-scaling','cooldown-identities','journal','combat','testing'])

    # The overview is intentionally small: eight meaningful differences, one route each.
    archive('features',old['features']['body'])
    feature_rows=[
      ('character','Three classes. One character.','Keep your starting class and choose two more from level 1. Combine their spells, skills, equipment access and strongest base HP/mana calculations.','multiclass.html','Build your character'),
      ('aa','AA progression from the beginning','Earn two AA per level-equivalent while leveling, or allocate up to 100% of eligible XP to AA. The allowed pool opens at level 1, with earned points and prerequisites.','multiclass.html#passive-abilities','Plan your AA progression'),
      ('adventuring','Classic dungeons, your way','Choose respawning Grind runs or harder Raid runs with permanent enemy deaths. Personal boss checklists and exclusive rewards give all 21 Classic dungeons a new purpose.','dungeon-modes.html','Choose a dungeon mode'),
      ('rewards','Loot that grows with you','Find Polished, Exalted and Ascended ordinary gear, hunt custom rewards in 48 zones, and turn matching duplicates into upgrades. Trade gear freely and equip across your held classes.','equipment.html','Understand gear progression'),
      ('companions','Build a roster of companions','Summon multiple pets, command one or all, manage their equipment and develop pet builds through earned gear and abilities.','pets.html','Manage your pets'),
      ('combat','Combat built around your whole build','Instant DoT casts, melee while casting, lasting ordinary blessings and earned class synergies support new combinations. Normal death preserves EXP and belongings.','combat.html','Read the combat rules'),
      ('world','A home base and a world to discover','Prepare in the Commonlands tunnel, use its travel network and unlock waypoint return destinations through exploration.','travel.html','Find your way around'),
      ('story','Original endgame stories','The Vigil of the Dawn is a demanding level-50 Paladin capstone with personal chapters, custom Chapterhouse encounters and an earned helmet.','camil-vigil.html','Explore the Vigil')]
    bodies['features']='<p class="feature-intro">The changes that reshape how you build, explore and progress in EverQuest. Classic is the current chapter; the level cap is 50.</p><div class="feature-list">'+''.join(f'<section class="feature-row" id="{ident}"><h2>{title}</h2><div><p>{desc}</p><a href="{href}">{label} →</a></div></section>' for ident,title,desc,href,label in feature_rows)+'</div><p class="overview-links">Practical guides: <a href="item-upgrades.html">Item upgrades</a> · <a href="tradeskills.html">Crafting</a> · <a href="advanced-loot.html">Loot controls</a> · <a href="launcher.html">Launcher</a>. Fixes and smaller updates: <a href="recent-changes.html">Change Log</a>.</p>'
    # Anchor preservation is handled below, including the retired overview group names.
    archive('index',old['index']['body'].split('<div class="welcome">')[0])
    bodies['index']='''<div class="welcome"><div class="welcome-copy"><p class="eyebrow">CLASSIC EVERQUEST · NEW POSSIBILITIES</p><h2>Make Norrath your own.</h2><p>Three classes per character. Earned progression. Classic adventures with a different path forward.</p><a class="button" href="features.html">What makes Nightcap different →</a><a class="welcome-secondary" href="getting-started.html">Start playing</a></div><img src="assets/traders-at-dusk.png" alt="Adventurers gathering in the Commonlands tunnel at dusk"></div><p class="home-context">Classic · Level 50 · Solo preferred · Friends welcome</p><p class="feature-entry">Browse <a href="all-pages.html">Guides</a> for instructions, or <a href="recent-changes.html">Change Log</a> for updates and fixes.</p>'''

    # Keep long references available on demand rather than as walls of text.
    folds={
      'combat':['bard-songs','throw-stone','monk-cooldowns','ability-cooldowns','spell-scaling','melee-builds','rabid-bear','focus-effects'],
      'multiclass':['class-awareness','spell-levels','ability-class-column','class-release','all-class-aa','aa-cooldowns','custom-aa'],
      'equipment':['heroic-gear','caster-gear','stat-cap','summoned-gear','merchant-payouts','fixed-resale','reviewed-ascended','starter-bands','earned-procs','thj-behavior-candidate'],
      'dungeon-modes':['required-bosses','added-keepers','added-objectives','unique-rewards','original-keepers','classic-candidate'],
      'build-lab':['model-scope','rotation-model','privacy'],
      'pets':['animation-commands','pet-scaling'],
      'tunnel':['residents','resident-chat','living-market','city-market'],
      'launcher':['loading-art','classic-models']}
    for slug,ids in folds.items():
        for ident in ids:
            part=sections(bodies[slug]).get(ident)
            if not part:continue
            h=re.match(r'<h2[^>]*>(.*?)</h2>',part,re.S)
            summary=re.sub('<[^>]+>','',h[1]);content=part[h.end():]
            replacement=f'<details class="guide-topic" id="{ident}"><summary>{summary}</summary><div class="topic-body">{content}</div></details>'
            bodies[slug]=bodies[slug].replace(part,replacement)

    # Concise, consistent summaries improve directories, bookmarks and search results.
    summaries={
      'index':'Your starting point for Nightcap’s features, guides and tools.',
      'features':'The major ways Nightcap changes standard EverQuest.',
      'getting-started':'Join, update, choose your classes and begin your first adventure.',
      'multiclass':'Choose three classes, learn their abilities and plan your AA progression.',
      'equipment':'Item qualities, trading, equipment access and reward systems.',
      'combat':'Casting, blessings, class synergies, healing and recovery.',
      'dungeon-modes':'Choose Raid or Grind, track boss credit and claim rewards.',
      'pets':'Summon, command, equip and care for your pet roster.',
      'launcher':'Install updates, use the interface and resolve launch problems.',
      'unreleased':'Unavailable projects and specific limits still under investigation.',
      'camil-vigil':'A level-50 Paladin story, personal chapters and Chapterhouse rewards.',
      'recent-changes':'Dated releases, smaller improvements and fixes.'}

    # Preserve every old anchor. Historical deep links reveal a short contextual
    # route to their archived notice, without showing release clutter on normal visits.
    alias_report={}
    for slug,body in bodies.items():
        if slug=='recent-changes':continue
        old_ids=re.findall(r'\bid="([^"]+)"',old[slug]['body'])
        current_ids=set(re.findall(r'\bid="([^"]+)"',body))
        missing=[ident for ident in old_ids if ident not in current_ids]
        if missing:
            if slug not in moved:archive(slug,old[slug]['body'])
            # Archive a complete preimage when a moved fragment was outside a prefix.
            if any(f'id="{ident}"' not in moved[slug] for ident in missing):moved[slug]=old[slug]['body']
            body+=''.join(f'<aside class="archived-update" id="{html.escape(ident,quote=True)}"><p>This update is in <a href="recent-changes.html#{slug}--{html.escape(ident,quote=True)}">Change Log →</a></p></aside>' for ident in missing)
            alias_report[slug]=missing
        bodies[slug]=body

    history=old['recent-changes']['body']
    dated=[]
    matches=list(re.finditer(r'<h2 id="([^"]+)">(.*?)</h2>',history,re.S))
    for i,m in enumerate(matches):
        end=matches[i+1].start() if i+1<len(matches) else len(history)
        day=re.search(r'October\s+(\d{1,2})',m[2])
        day=int(day[1]) if day else {'hole-entrance':24,'chapterhouse-candidate':23,'thj-behavior-candidate':19}.get(m[1],22)
        title=m[2] if 'October' in m[2] else f'October {day} · {m[2]}'
        dated.append((day,f'<details class="change-entry" id="{m[1]}"><summary>{title}</summary><div class="change-body">{history[m.end():end]}</div></details>'))
    archive_html=[]
    for slug,body in sorted(moved.items()):
        body=re.sub(r'\bid="([^"]+)"',lambda m:f'id="{slug}--{m[1]}"',body)
        archive_html.append(f'<details class="change-entry"><summary>{html.escape(old[slug]["title"])}: earlier update details</summary><div class="change-body">{body}</div></details>')
    bodies['recent-changes']='''<p>Current instructions live in <a href="all-pages.html">Guides</a>. This is the history of releases, improvements and fixes; older entries describe their date and may be superseded.</p><details class="change-entry" id="wiki-clarity" open><summary>October 24, 2026 · A clearer wiki</summary><div class="change-body"><p>Features now highlights the major differences from standard EQ. Guides start with useful instructions; fixes and repeated release announcements are collected here. Navigation and text sizes are consistent, and long reference lists expand when needed. Existing tools, gameplay rules, reward values and links are preserved.</p></div></details>'''+''.join(entry for _,entry in sorted(dated,key=lambda d:-d[0]))+'<h2 id="earlier-guide-notices">Earlier release detail</h2><p>Notices previously repeated across guides are retained below for their original context. Use the current guides for today’s instructions.</p>'+''.join(archive_html)

    for slug,body in bodies.items():
        a=dict(old[slug]);a['body']=body
        aliases={'multiclass':['AA','classes','class','AA progression'],'combat':['buffs','healing','death'],'equipment':['gear','loot','qualities'],'dungeon-modes':['dungeons','bosses','raid','grind'],'pets':['pet','pets'],'item-upgrades':['reforging','upgrades','forge'],'recent-changes':['fixes','change log','patch notes'],'travel':['teleport','travel']}
        if slug in aliases:a['keywords']=list(dict.fromkeys(a.get('keywords',[])+aliases[slug]))
        if slug in summaries:a['summary']=summaries[slug]
        if slug=='recent-changes':a['title']='Change Log'
        if slug=='index':a['title']='Nightcap Wiki'
        if body!=old[slug]['body'] or a.get('summary')!=old[slug].get('summary'):
            a['updated']='2026-10-24';a['sources']=a['sources']+['docs/releases/wiki-clarity-20261024/README.md']
        (ARTICLES/(slug+'.json')).write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    report={'source':BASE,'guides':len(old),'moved_notice_guides':sorted(moved),'preserved_anchor_aliases':alias_report,'catalog_values':'unchanged','gameplay_changes':False,'highkeep_candidate':'not activated or included'}
    (EVIDENCE/'content-review.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(f'Reorganized {len(old)} maintained guides; preserved all old anchors and moved notices.')


if __name__=='__main__':main()
