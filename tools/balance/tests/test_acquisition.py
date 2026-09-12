import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from acquisition_snapshot import reward_candidates,scan_quests
from baseline import query_json


class AcquisitionTests(unittest.TestCase):
    def test_reward_discovery_excludes_comments_and_strings(self):
        source='''-- e.other:SummonItem(1)
--[=[ e.other:SummonItem(2) ]=]
local message = "quest::summonitem(3)";
local long_message = [[ e.other:SummonItem(4) ]]
# quest::summonitem(5);
quest::summonitem(10908);
e.other:QuestReward(e.self,0,0,0,0,5532,500);
e.other:SummonItem(14341,1);
'''
        rows=reward_candidates(source)
        self.assertEqual([r['item_id'] for r in rows],[10908,5532,14341])
        self.assertEqual(rows[0]['line'],6)
        self.assertTrue(all(r['status']=='unreviewed_reference_not_acquisition_proof' for r in rows))

    def test_dynamic_rewards_remain_unresolved(self):
        rows=reward_candidates('quest::summonitem($id + 800000); e.other:SummonItem(choose(1,2));')
        self.assertEqual([r['item_id'] for r in rows],[None,None])

    def test_quoted_literal_ids_are_candidates_but_interpolation_is_not(self):
        rows=reward_candidates('quest::summonitem("18088"); quest::summonitem("$item1"); e.other:SummonItem(\'14341\');')
        self.assertEqual([r['item_id'] for r in rows],[18088,None,14341])

    def test_lua_override_and_zone_scope(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            for zone in ('classic','future','global'):
                (root/zone).mkdir()
            (root/'classic/NPC.pl').write_text('quest::summonitem(10);')
            (root/'classic/NPC.lua').write_text('e.other:SummonItem(20);')
            (root/'future/NPC.lua').write_text('e.other:SummonItem(30);')
            (root/'global/global_player.lua').write_text('e.other:SummonItem(40);')
            rows=scan_quests(root,['classic'])
            self.assertEqual([r['path'] for r in rows],['classic/NPC.lua','global/global_player.lua'])
            self.assertEqual([r['reward_candidates'][0]['item_id'] for r in rows],[20,40])

    def test_large_read_only_sql_uses_stdin(self):
        sql='SELECT '+('1,'*20000)+'1'
        with patch('baseline.subprocess.run',return_value=SimpleNamespace(stdout='{"value":1}\n')) as run:
            self.assertEqual(query_json(sql),[{'value':1}])
        argv=run.call_args.args[0]; kwargs=run.call_args.kwargs
        self.assertIn('-i',argv)
        self.assertNotIn('-e',argv)
        self.assertEqual(kwargs['input'],'START TRANSACTION READ ONLY; '+sql+'; COMMIT;')
        self.assertNotIn(sql,argv)


if __name__=='__main__':
    unittest.main()
