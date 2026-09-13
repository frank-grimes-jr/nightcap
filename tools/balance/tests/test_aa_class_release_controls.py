import copy
import json
from pathlib import Path
import unittest

from aa_class_release_controls import cases,assess


class ClassReleaseControlsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        root=Path(__file__).resolve().parents[3]
        cls.controls=cases(json.loads((root/'docs/balance/gear-source-inputs.json').read_bytes()))

    def test_earned_refund_is_full_cost_at_each_usable_stage(self):
        by_id={c['id']:c for c in self.controls}
        for identity,active in [('release-full-earned-wizard',6),('release-partially-usable-wizard',3),('release-suspended-wizard',0)]:
            case=by_id[identity]
            ops=case['input']['aa_ownership_probe']['operations']
            index=ops.index('release_third')
            self.assertEqual(case['expected'][index-1]['effective_rank_count'],active)
            released=case['expected'][index]
            self.assertEqual(released['saved_points'],{'wallet':47,'spent':5,'expended':5})
            self.assertEqual(released['earned_rank_count'],0)
            self.assertEqual(released['stored'],[])
            self.assertEqual(released['saved_classes'],[1,2,0])
        shared=by_id['release-preserves-shared-earned-aa']['expected'][1]
        self.assertEqual(shared['stored'],[{'first_rank_id':107,'rank_count':6,'charges':0}])
        self.assertEqual(shared['saved_points'],{'wallet':47,'spent':29,'expended':5})

    def test_assessment_detects_persistence_and_session_disagreement(self):
        for candidate in self.controls:
            expected=[dict(s,operation=op) for s,op in zip(candidate['expected'],candidate['input']['aa_ownership_probe']['operations'])]
            self.assertTrue(assess(candidate,{'aa_ownership_probe':{'steps':expected}})['passed'],candidate['id'])
        case=self.controls[0]
        steps=[dict(s,operation=op) for s,op in zip(case['expected'],case['input']['aa_ownership_probe']['operations'])]
        report={'aa_ownership_probe':{'steps':steps}}
        self.assertTrue(assess(case,report)['passed'])
        for field,value in [('earned_rank_count',6),('saved_classes',[1,2,12]),('unspent_points',17),('earned_state_valid',False)]:
            bad=copy.deepcopy(report)
            bad['aa_ownership_probe']['steps'][1][field]=value
            self.assertFalse(assess(case,bad)['passed'],field)


if __name__=='__main__': unittest.main()
