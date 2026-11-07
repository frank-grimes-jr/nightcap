"""Compile the Last Lantern candidate; writes staging data, never applies SQL."""
from copy import deepcopy
import json
from pathlib import Path

from dungeon_catalog import base_item, existing_items
from epic05 import load_catalog, task_rows

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/adventure-journal'
REVISION = 2026110701
FIRST_ARMOR = 964000
FIT_CLASSES = (65535, 65535 & ~15360, 65535 & ~(15360 | 32 | 64 | 16384), 151)
WORN_SLOTS = (19, 12, 9, 10, 7, 18, 2, 17)
AWARD_LEVELS = (20, 25, 30, 38, 40, 42, 46, 50)
SLOT_DESIGNS = (6, 4, 3, 3, 2, 5, 0, 1)
SLOT_NAMES = ('Boots', 'Gloves', 'Left Bracer', 'Right Bracer', 'Armguards', 'Leggings', 'Helm', 'Cuirass')
FIT_NAMES = ('Woven', 'Leather', 'Chain', 'Plate')

# A separate instance contract owns version80 scenes. Existing Keeper runs,
# checklists, their rewards and public populations are never enrolled or reset.
SCENES = [
    dict(task=9501, zone=63, level=25, title='The Missing Porter', version=80),
    dict(task=9508, zone=66, level=38, title='A Name Beneath the Moss', version=80),
    dict(task=9509, zone=32, level=40, title='What the Fire Kept', version=80),
    dict(task=9510, zone=48, level=42, title="The Captain's Last Watch", version=80),
    dict(task=9511, zone=39, level=45, title='The Debt of the Living', version=80),
    dict(task=9512, zone=72, level=46, title='Where Courage Ends', version=80),
    dict(task=9513, zone=76, level=48, title='The Weight of a Name', version=80),
    dict(task=9515, zone=76, level=50, title='The Last Lantern', version=80),
]
# kind, first activity, number of activities, goal count, wave count,
# credit each wave, escort between the three verified positions.
PROGRAMS = [
    [('Defense', 2, 1, 1, 3, False, True)],
    [('Records', 0, 1, 1, 0, False, False), ('Defense', 1, 1, 3, 3, True, True)],
    [('Battle', 0, 1, 2, 0, False, False), ('Defense', 1, 1, 3, 3, True, False)],
    [('Records', 0, 3, 1, 0, False, False), ('Defense', 3, 1, 3, 3, True, True)],
    [('Battle', 0, 1, 1, 0, False, False), ('Records', 1, 1, 1, 0, False, False), ('Defense', 2, 1, 3, 3, True, True)],
    [('Records', 0, 3, 1, 0, False, False), ('Battle', 3, 1, 1, 0, False, False)],
    [('Battle', 0, 1, 3, 0, False, False), ('Records', 1, 3, 1, 0, False, False)],
    [('Records', 0, 3, 1, 0, False, False), ('Defense', 3, 1, 3, 3, True, False), ('Battle', 4, 1, 1, 0, False, False)],
]


def required_level(grade, slot):
    return max(AWARD_LEVELS[slot], (0, 40, 46, 50)[grade])


def compile_items():
    templates = {(r['band'], r['design']): r['values'] for r in existing_items()
                 if r['source'] == 'completion' and r['quality'] == 'Normal'}
    result = []
    for fit in range(4):
        for grade in range(4):
            for slot, design in enumerate(SLOT_DESIGNS):
                level = required_level(grade, slot)
                low = min(50, max(20, level // 10 * 10))
                high = min(50, low + 10)
                a, b = templates[low, design], templates[high, design]
                name = f'Last Lantern {FIT_NAMES[fit]} {SLOT_NAMES[slot]}'
                if fit == 0 and slot == 7:
                    name = 'Last Lantern Woven Robe'
                if fit == 0 and slot == 6:
                    name = 'Last Lantern Woven Hood'
                name += ('', ' (Oathbound)', ' (Restored)', ' (Complete)')[grade]
                item = base_item(FIRST_ARMOR + fit * 32 + grade * 8 + slot, name)
                for field in ('ac', 'hp', 'mana', 'mr', 'fr', 'cr', 'pr', 'dr'):
                    item[field] = a[field] if high == low else (a[field] * (high - level) + b[field] * (level - low)) // 10
                primary = a['asta'] or a['adex'] or a['astr'] or a['aint'] or a['awis'] or a['aagi']
                item['ac'] = max(1, item['ac'] * (60, 80, 90, 100)[fit] // 100)
                item['hp'] = max(1, item['hp'] * (90, 100, 105, 110)[fit] // 100)
                item['mana'] = item['mana'] * (125, 100, 80, 70)[fit] // 100
                for field in (('aint', 'awis'), ('aagi', 'asta'), ('adex', 'awis'), ('astr', 'asta'))[fit]:
                    item[field] = primary
                item.update(slots=1 << WORN_SLOTS[slot], classes=FIT_CLASSES[fit],
                            reqlevel=level, reclevel=level, magic=1, nodrop=0,
                            norent=255, notransfer=1, nopet=1, price=0, sellrate=0,
                            material=11 if fit == 0 and slot == 7 else max(1, fit),
                            color=0xFF48515C if grade == 0 else 0xFF24364A,
                            icon=(666, 517, 634, 634, 546, 631, 639, 678)[slot],
                            weight=1 if fit == 0 else 5,
                            comment=f'Last Lantern {REVISION}; fixed personal campaign fit={fit} grade={grade} slot={slot}')
                if slot not in (2, 3):
                    item['augslot1type'] = 22
                    item['augslot1visible'] = 1
                result.append(item)
    return result


def manual(task, activity, step, label, zone, count=1, public=False):
    return dict(taskid=task, activityid=activity, req_activity_id=-1, step=step,
                activitytype=2, target_name=label, description_override=label,
                goalmethod=2, goalcount=count, npc_match_list='', zones=str(zone),
                zone_version=0 if public else 80, optional=0)


def compile_tasks():
    tasks, activities = task_rows(load_catalog())
    for row in tasks:
        row['reward_text'] = 'Personal Last Lantern equipment; return to the company.'
        if row['id'] == 9500:
            row['description'] += ' Mera Vell is searching for the Company of the Last Lantern. Read each entrance courier\'s copy: the same name has been scratched from every page.'
        elif row['id'] == 9501:
            row['description'] += ' After those victories, ask the Chronicler to enter a private journal expedition and rescue the missing porter. Return with his account.'
        elif row['id'] == 9502:
            row['description'] += ' Bring the expedition records to Mera in the Commonlands tunnel. She recognizes Captain Selene\'s seal.'
    # Visits and their individual courier notes can be completed in any order.
    for index, (zone, label) in enumerate(((65, 'Read the Upper Guk courier note'),
                                         (63, 'Read the Unrest courier note'),
                                         (11, 'Read the Runnyeye courier note'))):
        activities.append(manual(9500, 3 + index, 0, label, zone, public=True))
    activities.append(manual(9500, 6, 1, 'Return your annotated pages to the Chronicler', 22, public=True))
    activities += [manual(9501, 2, 1, 'Rescue the missing porter in a private journal expedition', 63),
                   manual(9501, 3, 2, 'Bring the porter\'s account to the Chronicler', 22, public=True),
                   manual(9502, 2, 1, 'Ask Mera to compare the recovered expedition records', 22, public=True)]
    stories = [
        (9508, 38, 'A Name Beneath the Moss', 'Mera followed the missing company into Lower Guk. Find her marked satchel, defend her retreat and bring her account home.',
         [(0, 'Recover the marked satchel', 66, 1), (1, 'Defend Mera at three retreat positions', 66, 3), (2, 'Return to the Chronicler with Mera', 22, 1)]),
        (9509, 40, 'What the Fire Kept', 'The recorder traded the company seal in the depths of Solusek\'s dungeons. Defeat his lieutenants and defend the furnace while Oren restores it.',
         [(0, 'Defeat the Witness\'s two lieutenants', 32, 2), (1, 'Protect the restored seal through three furnace waves', 32, 3), (2, 'Report to Oren in Commonlands', 22, 1)]),
        (9510, 42, 'The Captain\'s Last Watch', 'Reconstruct Captain Selene\'s last retreat in Cazic-Thule. Read her records, hold the marked positions and bring her final decision home.',
         [(0, 'Read the first retreat record', 48, 1), (0, 'Read the second retreat record', 48, 1), (0, 'Read the captain\'s final record', 48, 1), (1, 'Hold three positions during the retreat', 48, 3), (2, 'Return Selene\'s account to the Chronicler', 22, 1)]),
        (9511, 45, 'The Debt of the Living', 'In The Hole, the Witness\'s agent holds the stolen roster. Recover it and escape with Mera. The Chronicler must finally read every missing name.',
         [(0, 'Defeat the Witness\'s agent', 39, 1), (1, 'Recover the stolen roster', 39, 1), (2, 'Escape the collapsing ritual with Mera', 39, 3), (3, 'Hear the Chronicler read the restored names', 22, 1)]),
        (9512, 46, 'Where Courage Ends', 'Carry the company\'s courage into Fear. Release three bound names, survive the pursuer and recover the standard. Move, interrupt and leave yourself an escape.',
         [(0, 'Release the first bound name', 72, 1), (0, 'Release the second bound name', 72, 1), (0, 'Release the third bound name', 72, 1), (1, 'Defeat the pursuer of lost names', 72, 1), (2, 'Return the company standard to Oren', 22, 1)]),
        (9513, 48, 'The Weight of a Name', 'The Hollow Witness waits in Hate. Break through his chosen guard, stop him consuming the recorded names, and tell Mera what your oath now means.',
         [(0, 'Defeat three guards of the unwritten record', 76, 3), (1, 'Save the first recorded name', 76, 1), (1, 'Save the second recorded name', 76, 1), (1, 'Save the third recorded name', 76, 1), (2, 'Speak to Mera in Commonlands', 22, 1)]),
        (9514, 50, 'A Light Carried Forward', 'Gather the survivors in Commonlands. Return a personal effect, choose a memorial inscription and prepare to carry the restored standard into the final expedition.',
         [(0, 'Speak with Mera about the final expedition', 22, 1), (0, 'Ask Oren to prepare the standard', 22, 1), (0, 'Hear the rescued porter\'s account', 22, 1), (1, 'Choose a memorial inscription with the Chronicler', 22, 1)]),
        (9515, 50, 'The Last Lantern', 'In a final private Hate expedition, break the Witness\'s bindings, defend the company standard and face the man who traded his companions\' names. Then return to the Commonlands campfire.',
         [(0, 'Break the first binding', 76, 1), (0, 'Break the second binding', 76, 1), (0, 'Break the third binding', 76, 1), (1, 'Protect the standard through three waves', 76, 3), (2, 'Defeat the Hollow Witness', 76, 1), (3, 'Return to the company\'s closing campfire', 22, 1)]),
    ]
    for task, level, title, description, goals in stories:
        tasks.append(dict(id=task, type=2, duration=0, title=title, description=description,
                          reward_text='Personal Last Lantern progression; claim and refit with Oren.',
                          reward_id_list='', cash_reward=0, exp_reward=0, reward_method=0,
                          min_level=level, max_level=0, repeatable=0, enabled=1,
                          completion_emote='Your journal remembers. Return to the Commonlands company.'))
        activities += [manual(task, i, step, label, zone, count, public=zone == 22)
                       for i, (step, label, zone, count) in enumerate(goals)]
    activities.sort(key=lambda a: (a['taskid'], a['activityid']))
    return tasks, activities


def compile_npcs():
    template = json.loads((ROOT / 'docs/quests/camil-chapterhouse/local-content.json').read_text())['templates']['npc_types']
    result = []

    def npc(identity, name, **changes):
        row = deepcopy(template)
        row.update(id=identity, name=name, lastname='The Last Lantern', race=1, gender=0,
                   size=6, level=50, hp=10000, mana=0, bodytype=1, AC=100, ATK=0,
                   mindmg=0, maxdmg=0, attack_count=0, attack_delay=30, hp_regen_rate=0,
                   hp_regen_per_second=0, npc_spells_id=0, npc_spells_effects_id=0,
                   merchant_id=0, loottable_id=0, npc_faction_id=0, skip_global_loot=1,
                   special_abilities='14,1^15,1^16,1^17,1^19,1^20,1^24,1^25,1^35,1',
                   aggroradius=0, assistradius=0, always_aggro=0, exp_mod=0, exclude=1,
                   MR=50, FR=50, CR=50, PR=50, DR=50, Corrup=0, PhR=0, spellscale=100,
                   healscale=100, slow_mitigation=0, version=0)
        row['class'] = 1
        row.update(changes)
        result.append(row)

    npc(998900, 'Mera_Vell', gender=1, d_melee_texture1=0, d_melee_texture2=0)
    npc(998901, 'Oren_Lanternwright')
    npc(998902, 'Tovin_the_Returned_Porter')
    for identity in range(998903, 998906):
        npc(identity, 'a_wayfarer_courier')
    npc(998934, 'a_bound_wayfarer', gender=1)
    npc(998935, 'a_bound_wayfarer')
    npc(998936, 'a_bound_wayfarer', race=5, gender=1)
    for index, scene in enumerate(SCENES):
        level = scene['level']
        npc(998910 + index, ('a_roster_thief', 'a_mossbound_pursuer', 'an_emberbound_lieutenant',
                            'an_echo_of_the_last_watch', 'the_Witnesses_agent', 'a_pursuer_of_lost_names',
                            'a_guard_of_the_unwritten', 'a_fragment_of_the_broken_oath')[index],
            lastname='', level=level, hp=(650, 1000, 1300, 1500, 1500, 3200, 1500, 1200)[index],
            mindmg=(12, 22, 28, 30, 32, 40, 42, 40)[index],
            maxdmg=(28, 48, 60, 65, 70, 90, 95, 90)[index],
            AC=80 + level * 2, ATK=level * 5, attack_count=2,
            attack_delay=24 if level < 46 else 20, special_abilities='', aggroradius=35,
            assistradius=20, always_aggro=1)
    npc(998918, 'The_Hollow_Witness', lastname='Recorder of the Last Lantern', level=50,
        hp=6000, mindmg=50, maxdmg=110, AC=240, ATK=300, attack_count=2,
        attack_delay=20, special_abilities='', aggroradius=35, assistradius=20, always_aggro=1,
        spellscale=500)
    npc(998919, 'a_company_standard_bearer', level=50, hp=40000,
        special_abilities='14,1^15,1^16,1^17,1')
    return result


def native_catalog():
    geometry = json.loads((OUT / 'release-20261107/geometry.json').read_text())
    tasks, goals = compile_tasks()
    lines = ['#pragma once', '#include "last_lantern_policy.h"',
             '#include "last_lantern_scene_policy.h"', 'namespace NightcapLantern {',
             'struct Point { float x,y,z,h; };',
             'struct Scene { unsigned task,zone,level,npc; Point arrival; std::array<Point,3> points; const char *name; };',
             'inline constexpr Program Programs[] = {']
    for program in PROGRAMS:
        values = ['Segment{Kind::' + kind + ',' + ','.join(map(str, (first, count, goal, waves))) +
                  ',' + str(per_wave).lower() + ',' + str(escort).lower() + '}'
                  for kind, first, count, goal, waves, per_wave, escort in program]
        lines.append('\t{{' + ','.join(values) + '},' + str(len(values)) + '},')
    lines += ['};', 'inline constexpr Scene Scenes[] = {']

    def point(p):
        return '{' + ','.join(f'{float(p[k]):.7f}f' for k in ('x', 'y', 'z', 'heading')) + '}'

    for index, scene in enumerate(SCENES):
        positions = geometry['scenes'][str(scene['zone'])]
        lines.append('\t{' + ','.join(map(str, (scene['task'], scene['zone'], scene['level'], 998910 + index))) +
                     ',' + point(positions['arrival']) + ',{{' +
                     ','.join(point(p) for p in positions['poses']) + '}},' + json.dumps(scene['title']) + '},')
    lines += ['};', 'struct Goal { unsigned task,activity,step,count,zone,version,actor; };',
              'inline constexpr Goal Goals[] = {']
    actors = {(9500, 3): 998903, (9500, 4): 998904, (9500, 5): 998905,
              (9500, 6): 999220, (9501, 3): 999220, (9502, 2): 998900,
              (9508, 2): 999220, (9509, 2): 998901, (9510, 4): 999220,
              (9511, 3): 999220, (9512, 4): 998901, (9513, 4): 998900,
              (9514, 0): 998900, (9514, 1): 998901, (9514, 2): 998902,
              (9514, 3): 999220, (9515, 5): 999220}
    for goal in goals:
        if goal['goalmethod'] != 2:
            continue
        lines.append('\t{' + ','.join(map(str, (goal['taskid'], goal['activityid'], goal['step'],
                     goal['goalcount'], goal['zones'], goal['zone_version'],
                     actors.get((goal['taskid'], goal['activityid']), 0)))) + '},')
    lines += ['};', 'struct Task { unsigned id,level,activities; const char *name; };',
              'inline constexpr Task Tasks[] = {']
    for task in tasks:
        count = sum(goal['taskid'] == task['id'] for goal in goals)
        lines.append('\t{' + f"{task['id']},{task['min_level']},{count}," + json.dumps(task['title']) + '},')
    lines += ['};', 'template<class Item> bool CacheMatches(const Item &item) {', '\tswitch (item.ID) {']
    fields = dict(ac='AC', hp='HP', mana='Mana', astr='AStr', asta='ASta', aagi='AAgi', adex='ADex',
                  aint='AInt', awis='AWis', mr='MR', fr='FR', cr='CR', pr='PR', dr='DR',
                  slots='Slots', classes='Classes', material='Material', color='Color', reqlevel='ReqLevel')
    for item in compile_items():
        checks = [f'item.{native}=={item[field]}' + ('u' if field == 'color' else '') for field, native in fields.items()]
        checks += [f'item.AugSlotType[0]=={item["augslot1type"]}', '!item.NoDrop', 'item.NoTransfer',
                   'item.NoPet', 'item.NoRent', '!item.FreeTrade', 'item.FVNoDrop==1',
                   '!item.Price', '!item.FixedSellPrice', '!item.LoreFlag', '!item.Attuneable']
        lines.append(f'\tcase {item["id"]}: return ' + ' && '.join(checks) + ';')
    lines += ['\tdefault: return false;', '\t}', '}', '}']
    return '\n'.join(lines) + '\n'


def main():
    tasks, activities = compile_tasks()
    data = dict(revision=REVISION, status='built content candidate; not installed or player accepted',
                items=compile_items(), tasks=tasks, task_activities=activities,
                npc_types=compile_npcs(), scenes=SCENES)
    (OUT / 'last-lantern-catalog.json').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    geometry = OUT / 'release-20261107/geometry.json'
    if geometry.exists():
        (ROOT / 'server-mods/code/common/last_lantern_catalog.h').write_text(native_catalog(), encoding='utf-8')
    print(f'Compiled {len(tasks)} tasks, {len(activities)} activities, 128 armor definitions and 8 private scenes.')


if __name__ == '__main__':
    main()
