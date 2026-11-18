"""Apply the owner's custom-feature directory correction to the clarity release."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTICLES = ROOT / 'wiki/articles'


def save(name, data):
    (ARTICLES / (name + '.json')).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def row(anchor, title, text, links):
    return f'<section class="feature-row" id="{anchor}"><h3>{title}</h3><div><p>{text}</p><p>{links}</p></div></section>'


def link(target, label):
    return f'<a href="{target}.html">{label} →</a>'


def main():
    path = ARTICLES / 'features.json'
    data = json.loads(path.read_text(encoding='utf-8'))
    # Keep every historical incoming fragment and its contextual archive link.
    archive = data['body'][data['body'].index('<aside class="archived-update"'):]
    body = '<p class="feature-intro">Nightcap’s custom adventures and systems, all in one place. Classic is the current chapter; the level cap is 50. Released systems are in live testing; player and balance acceptance remain separate.</p>'
    body += '<nav class="feature-jumps" aria-label="Feature groups"><a href="#custom-adventures">Adventures &amp; quests</a><a href="#custom-builds">Character &amp; combat</a><a href="#custom-world">Gear, crafting &amp; world</a><a href="#custom-tools">Tools &amp; previews</a></nav>'
    body += '<h2 id="custom-adventures">Custom adventures &amp; quests</h2><div class="feature-list">'
    body += row('adventuring', 'Raid &amp; Grind dungeons', 'Choose respawning Grind runs or harder Raid runs with permanent enemy deaths. All 21 Classic dungeons have personal boss checklists, completion rewards and exclusive Raid designs; Chapterhouse adds a separate level-50 expedition.', link('dungeon-modes', 'Choose Raid or Grind'))
    body += row('story', 'Custom helmet quests', 'Earn the Winged Helm of the Dawn through Camil’s Vigil: a level-50 Paladin story with personal chapters, a three-wave defense and custom Chapterhouse bosses. The Shadow Knight campaign, The Ashen Compact, is prepared but <strong>not released</strong>.', link('camil-vigil', 'Paladin helmet quest') + ' · <a href="unreleased.html#ashen-compact">Shadow Knight preview →</a>')
    body += row('zone-hunt', 'Zone Hunt: custom gear &amp; augments', 'Hunt new equipment and heroic augments across 48 Classic zones. Each zone has its own reward families and four qualities, with matching-copy forging and six eligible armor locations for augments.', link('zone-hunt', 'How Zone Hunt works') + ' · ' + link('zones', 'Browse zone rewards'))
    body += row('epics', 'Ascended epic quest', 'Bring an earned, supported original class epic to the Epic Forgemaster and reforge it with Essence of Ascension and platinum. Eligibility follows your starting class; the original epic must already be earned.', link('ascension', 'Ascend your epic'))
    body += '</div><h2 id="custom-builds">Custom character &amp; combat systems</h2><div class="feature-list">'
    body += row('character', 'Three classes. One character.', 'Keep your starting class and choose two more from level 1. Combine their spells, skills, equipment access and strongest base HP/mana calculations.', link('multiclass', 'Build your character'))
    body += row('aa', 'AA progression from the beginning', 'Earn two AA per level-equivalent while leveling, or allocate up to 100% of eligible XP to AA. The allowed pool opens at level 1, with earned points and prerequisites.', '<a href="multiclass.html#passive-abilities">Plan your AA progression →</a>')
    body += row('companions', 'A roster of companions', 'Summon multiple pets, command one or all, manage their equipment and develop pet builds through earned gear and abilities.', link('pets', 'Manage your pets'))
    body += row('combat', 'Combat built around your whole build', 'Instant DoT casts, melee while casting, lasting ordinary blessings and earned class synergies support new combinations. Normal death preserves EXP and belongings.', link('combat', 'Read the combat rules'))
    body += '</div><h2 id="custom-world">Custom gear, crafting &amp; world systems</h2><div class="feature-list">'
    body += row('rewards', 'Tiered loot &amp; free trading', 'Find Polished, Exalted and Ascended versions of eligible ordinary gear. Trade freely, own duplicates and equip across your held classes while remaining item requirements still apply.', link('equipment', 'Understand gear progression') + ' · ' + link('advanced-loot', 'Personal loot controls'))
    body += row('reforging', 'Reforge duplicate equipment', 'Turn matching copies into a higher quality using Artisan Veyra’s reusable Reforging Box or Zone Hunt forging. Recipes differ by reward system; dungeon rewards do not use these upgrades.', link('item-upgrades', 'Compare upgrade recipes'))
    body += row('class-armor', 'Ascended class-armor quests', 'Earn Ascended rewards from the reviewed Crafted, Lambent, Darkforge, Ivy Etched and Totemic quests. Their materials and quest requirements remain; already-owned armor is not converted.', '<a href="equipment.html#class-armor-candidate">Find the class-armor rules →</a>')
    body += row('crafting', 'Stacked materials &amp; Craft All', 'Prepare at the tunnel workshop, combine from material stacks and repeat an eligible selected recipe with Craft All. Skill checks, ingredients and class or station requirements remain.', link('tradeskills', 'Use the workshop'))
    body += row('exploration', 'Waypoint Explorer', 'Discover crystal markers to unlock return destinations with the Waypoint Master. Complete the current discovery catalog to earn the Explorer title; progress is personal.', link('waypoints', 'Start exploring'))
    body += row('world', 'A custom Commonlands home base', 'Gather at class courts, crafting stations, limited-stock traders and level-based blessing services. City routes, rings, spires and Nightcap Recall connect your adventures.', link('tunnel', 'Meet the tunnel services') + ' · ' + link('travel', 'Explore travel options'))
    body += '</div><h2 id="custom-tools">Tools &amp; upcoming content</h2><p>Try builds and rotation priorities in the experimental <a href="build-lab.html">Build Lab</a>, find ordinary equipment with the <a href="loot-finder.html">Loot finder</a>, or update with the <a href="launcher.html">Nightcap launcher</a>. Each tool explains its limits.</p><p>Prepared adventures stay separate from available rewards: see <a href="unreleased.html#ashen-compact">The Ashen Compact</a> and <a href="unreleased.html#journal">Adventure Journal &amp; Epic 0.5</a>. Both are <strong>not released</strong>.</p><p class="overview-links">Choose a feature above for its guide. Smaller improvements, repairs and release history belong in <a href="recent-changes.html">Change Log</a>.</p>'
    data.update(summary='Custom dungeons, helmet quests, rewards and systems that make Nightcap different.', body=body + archive, updated='2026-10-24')
    data['keywords'] = ['custom features', 'custom content', 'server features', 'helmet quests', 'raid grind', 'custom quests']
    data['sources'].append('docs/releases/wiki-custom-features-20261024/README.md; reviewed linked maintained guides and Ashen Compact SPEC653d3266; candidate remains not released')
    save('features', data)
    data = json.loads((ARTICLES / 'unreleased.json').read_text(encoding='utf-8'))
    if 'id="ashen-compact"' not in data['body']:
        data['body'] = data['body'].replace('<h2 id="pet-scaling">', '<h2 id="ashen-compact">The Ashen Compact — not released</h2><p>A prepared level-50 Shadow Knight helmet campaign in a curated Kael expedition, with personal story objectives, Raid/Grind journals, a three-wave defense and custom bosses. Shadow Knight in any held class slot is required; difficulty targets a Shadow Knight main. Its Warhelm reward, encounters and client appearance are <strong>not installed or accepted in game</strong>. The released Paladin counterpart is <a href="camil-vigil.html">Camil’s Vigil of the Dawn</a>, in live testing.</p><h2 id="pet-scaling">', 1)
        data['sources'].append('Candidate only: feature/warhelm-shadow-knight653d3266, docs/quests/warhelm/SPEC.md reviewed2026-10-24; no deployment/acceptance evidence')
    save('unreleased', data)
    data = json.loads((ARTICLES / 'recent-changes.json').read_text(encoding='utf-8'))
    if 'id="custom-feature-directory"' not in data['body']:
        data['body'] = '<h2 id="custom-feature-directory">October 24 — Custom content on Features</h2><p><a href="features.html">Features</a> now groups Raid &amp; Grind dungeons, helmet quests, Zone Hunt, epic reforging, class armor, crafting, exploration and custom character systems. Each entry links to its guide. The Ashen Compact preview is explicitly not released; gameplay, rewards and balance are unchanged.</p>' + data['body']
    save('recent-changes', data)


if __name__ == '__main__':
    main()
