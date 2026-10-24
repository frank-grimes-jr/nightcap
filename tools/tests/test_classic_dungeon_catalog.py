"""Coverage and append-only compatibility for every requested Classic zone."""
import json
import hashlib
from pathlib import Path
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
from dungeon_catalog import DUNGEONS, items, existing_items

class ClassicCoverage(unittest.TestCase):
    def test_all_classic_dungeons_and_three_planes(self):
        expected={'befallen','unrest','highkeep','najena','cazicthule','permafrost','soldungb',
            'blackburrow','crushbone','runnyeye','soldunga','guktop','gukbottom','mistmoore',
            'kedge','paw','hole','qcat','fearplane','hateplane','airplane'}
        self.assertEqual({d[0] for d in DUNGEONS},expected)
        self.assertEqual(len(DUNGEONS),21)
        self.assertEqual(len({d[2] for d in DUNGEONS}),21)

    def test_existing_rewards_and_indices_are_preserved(self):
        old=json.loads((ROOT/'docs/dungeons/classic-expansion-20261022/compatibility.json').read_text())
        current=json.loads((ROOT/'docs/dungeons/catalog.json').read_text())
        self.assertEqual([d[0] for d in DUNGEONS[:7]],
            ['befallen','unrest','highkeep','najena','cazicthule','permafrost','soldungb'])
        self.assertEqual(current['dungeons'][:7],old['dungeons'])
        self.assertEqual(current['revision'],old['revision'])
        self.assertEqual(hashlib.sha256(json.dumps(existing_items(),sort_keys=True,separators=(',',':')).encode()).hexdigest(),old['reward_sha256'])
        expected=existing_items()
        for row in expected:row['values']['magic']=1
        self.assertEqual(items()[:330],expected)
        self.assertEqual(len([r for r in items() if r['values']['id']<960414]),414)
        self.assertEqual({r['values']['id'] for r in items()[414:420]},set(range(960414,960420)))
        self.assertTrue(all(r['source']=='chapterhouse' for r in items()[414:420]))
        self.assertEqual({r['values']['id'] for r in items()[420:]},set(range(960420,960426)))
        self.assertTrue(all(r['source']=='kael' for r in items()[420:]))

    def test_all_objectives_have_distinct_native_or_private_spawn_identities(self):
        catalog=json.loads((ROOT/'docs/dungeons/catalog.json').read_text())
        for dungeon in catalog['dungeons']:
            bosses=dungeon['bosses']
            self.assertGreater(len(bosses),0)
            self.assertLess(len(bosses),20)
            self.assertEqual(len({b['spawn_id'] for b in bosses}),len(bosses))
            self.assertEqual(len({b['npc_id'] for b in bosses}),len(bosses))
            self.assertEqual([b['boss_id'] for b in bosses],list(range(1,len(bosses)+1)))
            self.assertEqual([b['is_final'] for b in bosses],[False]*(len(bosses)-1)+[True])

    def test_service_and_private_content_are_additive(self):
        rows=json.loads((ROOT/'docs/dungeons/classic-expansion-20261022/install-rows.json').read_text())
        self.assertNotIn('items',rows)
        self.assertEqual(len(rows['npc_types']),15)
        self.assertEqual({r['id'] for r in rows['npc_types']},set(range(998800,998815)))
        self.assertEqual({r['id'] for r in rows['tasks']},set(range(9714,9742)))
        self.assertEqual(len({r['name'] for r in rows['spawngroup']}),len(rows['spawngroup']))
        self.assertEqual(len(rows['nightcap_dungeon_spawns']),12)
        self.assertEqual({r['zone_id'] for r in rows['nightcap_dungeon_spawns']},{71})
        for row in rows['npc_types']:
            if row['id']==998814:continue
            self.assertEqual((row['race'],row['gender'],row['size'],row['untargetable']),(108,2,3,0))

    def test_sky_key_services_are_durable_and_noncombat(self):
        rows=json.loads((ROOT/'docs/dungeons/classic-expansion-20261022/install-rows.json').read_text())
        service=next(r for r in rows['npc_types'] if r['id']==998814)
        abilities={int(v.split(',')[0]) for v in service['special_abilities'].split('^')}
        self.assertTrue({14,15,16,17,19,20,24,25,35,46,47,48,57}<=abilities)
        self.assertEqual((service['loottable_id'],service['npc_faction_id']),(0,0))
        spawns=rows['nightcap_dungeon_spawns']
        self.assertEqual(len([r for r in spawns if r['npc_id']==998814]),7)
        self.assertEqual(next(r['respawn'] for r in spawns if r['npc_id']==71032),14400)
        self.assertFalse(any(r['spawngroupID'] in range(986000,986012) for r in rows['spawn2']))

if __name__=='__main__':unittest.main()
