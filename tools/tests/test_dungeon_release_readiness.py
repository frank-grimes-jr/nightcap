"""Keeper admission must accept the reviewed November6 expedition afterimages."""
import json
import copy
from pathlib import Path
import re
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from dungeon_contract import predicate
from chapterhouse_content import compile_rows as vigil_rows
from warhelm_content import compile_rows as compact_rows
from dungeon_refresh_contract import expedition_augments


def expedition_rows():
    audit = json.loads((ROOT / 'docs/audits/augments-20261106/item-preimages.json').read_text())
    after = {int(r['after']['id']): r for r in audit if r['zone'] in ('chapterhouse', 'kael')}
    assert len(after) == 8
    result = {}
    for prefix, compiler in [('vigil', vigil_rows), ('compact', compact_rows)]:
        rows = compiler()['items']
        for row in rows:
            release = after.get(row['id'])
            if release:
                for field, value in release['after'].items():
                    if value != release['before'][field]:
                        row[field] = int(value) if field != 'lore' else value
        result[prefix] = rows
    return result


class DungeonReadiness(unittest.TestCase):
    def test_generator_rejects_wrong_compiler_or_sql_preimages(self):
        historical = {'content': []}
        for source in ('camil-chapterhouse', 'warhelm'):
            historical['content'] += json.loads((ROOT / 'docs/quests' / source / 'runtime-checks.json').read_text())
        custom = [dict(values=r) for compiler in (vigil_rows,compact_rows) for r in compiler()['items']]
        bad_compiler = copy.deepcopy(custom)
        bad_compiler[0]['values']['icon'] = 5000
        with self.assertRaisesRegex(AssertionError,'Compiler preimage drift'):
            expedition_augments(copy.deepcopy(historical),bad_compiler)
        bad_sql = copy.deepcopy(historical)
        check = next(c for c in bad_sql['content'] if c['label']=='vigil/items/0')
        check['sql'] = check['sql'].replace('`icon` <=> 500','`icon` <=> 5000')
        with self.assertRaisesRegex(AssertionError,'SQL preimage drift'):
            expedition_augments(bad_sql,copy.deepcopy(custom))

    def test_generator_changes_only_the_two_expedition_item_batches(self):
        contract = {'content': []}
        for source in ('camil-chapterhouse', 'warhelm'):
            contract['content'] += json.loads((ROOT / 'docs/quests' / source / 'runtime-checks.json').read_text())
        before = {c['label']:copy.deepcopy(c) for c in contract['content']}
        custom = [dict(values=r) for compiler in (vigil_rows,compact_rows) for r in compiler()['items']]
        expedition_augments(contract,custom)
        after = {c['label']:c for c in contract['content']}
        self.assertEqual(before.keys(),after.keys())
        self.assertEqual({k for k in before if before[k]!=after[k]}, {'vigil/items/0','compact/items/0'})

    def test_sql_guards_accept_reviewed_expedition_afterimages(self):
        contract = json.loads((ROOT / 'docs/dungeons/runtime-contract.json').read_text())
        for prefix, rows in expedition_rows().items():
            clauses = [clause.removeprefix('SELECT COUNT(*) FROM `items` WHERE ')
                       for c in contract['content'] if c['label'].startswith(prefix+'/items/')
                       for clause in c['sql'].split(' OR ')]
            for row in rows:
                clause, = [c for c in clauses if f"`id` <=> {row['id']} AND " in c]
                self.assertEqual(set(clause.strip('()').split(' AND ')),
                                 set(predicate(row).strip('()').split(' AND ')),
                                 f"{prefix} item {row['id']} rejects the released definitions")

    def test_native_cache_guards_accept_icons_healing_and_focus_metadata(self):
        header = (ROOT / 'server-mods/code/common/dungeon_contract.h').read_text()
        for rows in expedition_rows().values():
            for row in rows[:4]:
                guard = re.search(r'case '+str(row['id'])+r': return ([^\n]+)', header).group(1)
                fields = [('icon', 'Icon'), ('healamt', 'HealAmt'), ('focuseffect', 'Focus.Effect')]
                if row.get('focuseffect', -1) > 0:
                    fields += [('focustype', 'Focus.Type'), ('focuslevel', 'Focus.Level'), ('focuslevel2', 'Focus.Level2')]
                for field, member in fields:
                    self.assertIn(f'i.{member}=={row.get(field, 0)}', guard, (row['id'], field))

    def test_current_hate_placement_contract_is_preserved(self):
        contract = json.loads((ROOT / 'docs/dungeons/runtime-contract.json').read_text())
        checks = {c['label']: c for c in contract['content']}
        self.assertEqual(checks['hate-layout/nightcap_dungeon_spawns/count']['expected'], '223')
        self.assertEqual(len([c for c in checks if c.startswith('hate-density/')]), 21)
        for expected in json.loads((ROOT / 'docs/dungeons/hate-boss-placement-20261030/runtime-checks.json').read_text()):
            self.assertEqual(checks[expected['label']], expected)


if __name__ == '__main__':
    unittest.main()
