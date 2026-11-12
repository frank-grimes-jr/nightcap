"""Reviewed title catalog; generate native definitions and the wiki together.

python -B tools/earned_titles.py [--check]
Never renumber or reuse an issued title ID. Availability stays Not released until
the separate native/storage activation and player QA have evidence.
"""
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def catalog():
    rows = []

    def add(offset, name, kind, key, required, description, group, suffix=False):
        rows.append(dict(id=1900000000 + offset, name=name, kind=kind, key=key,
                         required=required, description=description, group=group, suffix=suffix))

    for offset, name, key, goal, label in [
        (1, 'Hunter', 1, 100, 'enemies'), (2, 'Slayer', 1, 1000, 'enemies'),
        (3, 'Vanquisher', 1, 10000, 'enemies'),
        (4, 'Grave Warden', 2, 100, 'undead'), (5, 'Undead Slayer', 2, 1000, 'undead'),
        (6, 'Deathbane', 2, 5000, 'undead'), (7, 'Giant Hunter', 3, 100, 'giants'),
        (8, 'Giant Slayer', 3, 1000, 'giants'), (9, 'Wyrm Hunter', 4, 1, 'dragons'),
        (10, 'Wyrm Slayer', 4, 10, 'dragons'), (11, 'Wyrmbane', 4, 100, 'dragons'),
    ]:
        add(offset, name, 'Counter', key, goal, f'Defeat {goal:,} qualifying {label}.', 'Slayer ranks')
    for offset, name, key, who, where in [
        (12, 'Flamebreaker', 100, 'Lord Nagafen', "Nagafen's Lair"),
        (13, 'Frostbreaker', 101, 'Lady Vox', 'Permafrost'),
        (14, 'Dracoliche Bane', 102, 'a dracoliche', 'Plane of Fear'),
    ]:
        add(offset, name, 'Counter', key, 1, f'Defeat {who} in {where}.', 'Named victories')
    add(15, 'Dragonslayer', 'BothDragons', 0, 2, 'Defeat both Lord Nagafen and Lady Vox.', 'Named victories')
    add(16, 'Dungeon Delver', 'ClearCount', 0, 1, 'Earn a personal full clear in any Keeper dungeon, Grind or Raid.', 'Dungeon and expansion')
    add(17, 'Dungeon Conqueror', 'RaidCount', 0, 5, 'Earn personal full Raid clears in five different Keeper dungeons.', 'Dungeon and expansion')
    add(18, 'Conqueror of Classic', 'Classic', 0, 21, 'Earn personal full Raid clears in all 21 Classic Keeper dungeons.', 'Dungeon and expansion')
    add(19, 'Planar Conqueror', 'Planes', 0, 3, 'Earn personal full Raid clears in Fear, Hate and Sky.', 'Dungeon and expansion')
    zones = [
        (36, 'Befallen', 'Bane of Befallen'), (63, 'Estate of Unrest', 'Restbringer'),
        (6, 'High Keep', 'High Keep Liberator'), (44, 'Najena', 'Breaker of Najena'),
        (48, 'Cazic-Thule', 'Temple Breaker'), (73, 'Permafrost', 'Winter Conqueror'),
        (32, "Nagafen's Lair", 'Flame Conqueror'), (17, 'Blackburrow', 'Blackburrow Bane'),
        (58, 'Crushbone', 'Orcbane'), (11, 'Runnyeye', 'Runnyeye Conqueror'),
        (31, "Solusek's Eye", 'Deepfire Conqueror'), (65, 'Upper Guk', 'Guk Pathfinder'),
        (66, 'Lower Guk', 'Ghoulbane'), (59, 'Castle Mistmoore', 'Mistmoore Conqueror'),
        (64, 'Kedge Keep', 'Tidebreaker'), (18, 'Splitpaw', 'Splitpaw Conqueror'),
        (39, 'The Hole', 'Deep Delver'), (45, 'Qeynos Catacombs', 'Catacomb Conqueror'),
        (72, 'Plane of Fear', 'Fearless'), (186, 'Plane of Hate', 'Hatebreaker'),
        (71, 'Plane of Sky', 'Skybreaker'),
    ]
    for i, (zone, label, name) in enumerate(zones):
        add(30 + i, name, 'RaidZone', zone, 1, f'Earn a personal full Raid clear in {label}.', 'Dungeon and expansion')
    skills = [
        (0, '1H Blunt', 'Mace Master'), (1, '1H Slashing', 'Blademaster'),
        (2, '2H Blunt', 'Maul Master'), (3, '2H Slashing', 'Greatblade Master'),
        (36, '1H Piercing', 'Piercing Master'), (77, '2H Piercing', 'Lance Master'),
        (7, 'Archery', 'Deadeye'), (28, 'Hand to Hand', 'Iron Fist'),
        (15, 'Defense', 'Stalwart'), (31, 'Meditate', 'Tranquil'),
        (4, 'Abjuration', 'Master Abjurer'), (5, 'Alteration', 'Master Transmuter'),
        (14, 'Conjuration', 'Master Conjurer'), (18, 'Divination', 'Master Seer'),
        (24, 'Evocation', 'Master Evoker'), (41, 'Singing', 'Virtuoso'),
        (53, 'Tracking', 'Pathfinder'), (29, 'Hide', 'Unseen'),
        (42, 'Sneak', 'Silent Step'), (39, 'Safe Fall', 'Surefoot'),
        (50, 'Swimming', 'Tidewalker'), (55, 'Fishing', 'Master Angler'),
        (66, 'Alcohol Tolerance', 'Iron Liver'),
        (60, 'Baking', 'Master Baker'), (61, 'Tailoring', 'Master Tailor'),
        (63, 'Blacksmithing', 'Master Smith'), (64, 'Fletching', 'Master Fletcher'),
        (65, 'Brewing', 'Master Brewer'), (68, 'Jewelry Making', 'Master Jeweler'),
        (69, 'Pottery', 'Master Potter'), (59, 'Alchemy', 'Master Alchemist'),
        (56, 'Make Poison', 'Master Poisoner'), (57, 'Tinkering', 'Master Tinker'),
        (58, 'Research', 'Master Researcher'),
    ]
    for i, (skill, label, name) in enumerate(skills):
        add(100 + i, name, 'Skill', skill, 1,
            f'At level 50 or higher, raise raw {label} to the highest legal level-50 cap among your currently held classes.', 'Skill mastery')
    add(140, 'Master Artisan', 'AllCrafts', 0, 7,
        'At level 50 or higher, master Baking, Tailoring, Blacksmithing, Fletching, Brewing, Jewelry Making and Pottery together.', 'Skill mastery')
    add(150, 'Seasoned Adventurer', 'Level', 0, 50, 'Reach level 50.', 'Adventure milestones')
    add(151, 'the Last Lantern', 'Task', 9515, 1, 'Complete the final chapter of The Last Lantern campaign.', 'Adventure milestones', suffix=True)
    assert len({r['id'] for r in rows}) == len(rows)
    assert all(len(r['name'].encode()) < 32 and len(r['description']) < 240 for r in rows)
    return rows, zones


def outputs():
    rows, zones = catalog()
    header = '// Generated by tools/earned_titles.py; stable IDs, never reuse.\ninline constexpr Definition Catalog[] = {\n'
    for r in rows:
        header += '\t{' + ','.join([str(r['id']), json.dumps(r['name']), str(r['suffix']).lower(),
                                    'Kind::' + r['kind'], str(r['key']), str(r['required']),
                                    json.dumps(r['description'])]) + '},\n'
    header += '};\n'
    body = (
        '<p><strong>Not released.</strong> This is the planned earned-title catalog. '
        'These new titles and #titles are unavailable until the server release is activated.</p>'
        '<h2 id="using-titles">Choosing your title</h2><p>Titles are cosmetic, permanent unlocks for one character. '
        'They give no stats, experience, loot or combat bonuses, and do not transfer to other characters. '
        'Once released, open the native Titles window to choose an earned prefix or suffix; choosing a title '
        'does not consume it. You may change or clear it. New awards never replace your currently selected title.</p>'
        '<p>Use <code>#titles</code> or <code>#titles 2</code> to check six requirements per page. '
        'Opening the Titles window or using #titles also checks existing dungeon, story and skill progress. '
        'Qualifying kills and a skill reaching its cap award their titles automatically. '
        'Level-50 and dungeon/story milestones are reconciled when you open the list.</p>'
        '<h2 id="kill-credit">Combat credit</h2><p>New slayer counters start when this feature is enabled. '
        'Defeat naturally spawned enemies that are not gray to your character. The credited killer and '
        'their current group or raid members can each count the kill if alive, connected and within '
        '200 game units in the same zone instance. A pet or swarm-pet victory follows native owner '
        'credit. Pets, charmed victims, merchants, chests, scripted campaign actors and GM accounts do not count. '
        'There is no requirement to land the final blow personally.</p>'
        '<p>Undead means the server undead, summoned-undead and vampire body types; giants include raid giants; '
        'dragons include all four server dragon body types. Appearance alone does not determine a slayer family. '
        'Named victory titles require the exact named encounter in its home zone. Earlier personal Keeper '
        'boss credit for Nagafen, Vox or the Fear dracoliche can qualify; it does not create historical slayer totals.</p>'
        '<h2 id="classic-completion">What completing Classic means</h2><p><strong>Conqueror of Classic</strong> '
        'requires a personal full <strong>Raid</strong> clear in every dungeon below. Each run must record '
        'your credit for all required bosses. Entering a run, another member finishing it or killing only its '
        'last boss is insufficient. Grind clears qualify for Dungeon Delver but do not satisfy Classic conquest. '
        'Saved full-clear history counts; older Plane of Hate clears and the current Hate layout count as one dungeon. '
        'Chapterhouse and Ashen Compact are separate adventures and do not replace a Classic dungeon. '
        'This is Nightcap’s 21-dungeon completion checklist, not every quest, item or NPC in the expansion. '
        'Later expansion completion titles will receive separate checklists when those releases are designed.</p><ul>'
        + ''.join('<li>' + html.escape(label) + '</li>' for _, label, _ in zones) + '</ul>'
        '<h2 id="skill-caps">Skill mastery</h2><p>Be level 50 or higher and reach the highest legal '
        '<strong>level-50 raw skill cap</strong> among your currently held classes. A cap of zero never qualifies. '
        'A low-level cap, equipment modifiers and temporary skill bonuses do not qualify. Existing racial, '
        'class, tradeskill advancement and specialization rules remain unchanged. Master Artisan needs all '
        'seven listed crafts at their legal caps together. Different builds can have different legal caps; '
        'the in-game progress command shows yours. Unlocks remain after leveling, changing classes or releasing a class.</p>'
        '<h2 id="catalog">Title requirements</h2>'
    )
    for group in dict.fromkeys(r['group'] for r in rows):
        anchor = 'title-group-' + group.lower().replace(' ', '-')
        body += '<details class="guide-topic" id="' + anchor + '"><summary>' + html.escape(group) + '</summary><table><thead><tr><th>Title</th><th>Placement</th><th>Requirement</th></tr></thead><tbody>'
        for r in rows:
            if r['group'] == group:
                body += '<tr><td>' + html.escape(r['name']) + '</td><td>' + ('Suffix' if r['suffix'] else 'Prefix') + '</td><td>' + html.escape(r['description']) + '</td></tr>'
        body += '</tbody></table></details>'
    article = dict(slug='titles', title='Titles', summary=f'How to earn and choose {len(rows)} cosmetic titles for slaying, dragons, Classic dungeon completion, skills and adventures.',
                   body=body, category='Character', status='Not released', updated='2026-11-12',
                   keywords=['slayer', 'dragonslayer', 'Nagafen', 'Vox', 'mastery', 'Classic completion', '#titles'],
                   sources=['tools/earned_titles.py', 'server-mods/code/common/earned_title_policy.h',
                            'server-mods/code/zone/earned_titles.inc', 'docs/titles/SPEC.md', 'docs/titles/QA.md'],
                   reviewed_at='2026-11-12')
    return {'server-mods/code/common/earned_title_catalog.h': header,
            'wiki/articles/titles.json': json.dumps(article, ensure_ascii=False, indent=2) + '\n'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    stale = []
    for name, expected in outputs().items():
        path = ROOT / name
        if args.check:
            if not path.exists() or path.read_text(encoding='utf-8') != expected:
                stale.append(name)
        else:
            path.write_text(expected, encoding='utf-8', newline='\n')
    if stale:
        raise SystemExit('Title catalog outputs need regeneration: ' + ', '.join(stale))
    print(f'{len(catalog()[0])} earned titles; catalog and wiki ' + ('verified' if args.check else 'generated'))


if __name__ == '__main__':
    main()
