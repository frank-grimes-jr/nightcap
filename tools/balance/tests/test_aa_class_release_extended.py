import copy
from pathlib import Path
import unittest
from aa_class_release_extended import cases,assess
from aa_policy_preflight import read_json

class ExtendedReleaseControls(unittest.TestCase):
    def test_skill_and_refund_contracts_are_distinct(self):
        controls=cases(read_json(Path(__file__).resolve().parents[3]/'docs/balance/gear-source-inputs.json'))
        by_id={c['id']:c for c in controls}
        self.assertEqual(len(controls),20)
        self.assertEqual(by_id['monk-skill-only-release-clamps-and-preserves']['expected'][-1]['saved_skills'],
                         [{'id':0,'value':250},{'id':19,'value':200},{'id':26,'value':0}])
        self.assertEqual(by_id['charged-class-only-aa-refunds-unused-charge']['expected'][-1]['unspent_points'],21)
        self.assertEqual(by_id['charged-class-only-aa-does-not-refund-consumed-charge']['expected'][-1]['unspent_points'],17)
        self.assertEqual(by_id['class-only-grant-removed-without-refund']['expected'][-1]['unspent_points'],17)
        for case in controls:
            steps=[dict(expected,operation=op) for expected,op in zip(case['expected'],case['input']['aa_ownership_probe']['operations'])]

            final=steps[-1];publishes=final['release_publication_expected']
            final['release_packets']={'publication':({'in_transaction':0,'classes':final['saved_classes'],'points':final['saved_points'],'aa_rows':len(final['stored']),'skills':final['saved_skills']} if publishes else None),
                'clear_packets':1 if publishes else 0,'table_packets':1 if publishes else 0,'table_before_clear':False,
                'skill_packets':[r for r in final['saved_skills'] if case['skills'].get(str(r['id']))!=r['value']],
                'transport_closed':final['session_exited']}
            report={'aa_ownership_probe':{'steps':steps}}
            self.assertTrue(assess(case,report)['passed'])
            for field in ('class_mask','saved_classes','saved_skills','stored','unspent_points','session_exited'):
                bad=copy.deepcopy(report);bad['aa_ownership_probe']['steps'][-1][field]=None
                self.assertFalse(assess(case,bad)['passed'],case['id']+':'+field)
            bad=copy.deepcopy(report);bad['aa_ownership_probe']['steps'][-1]['release_packets']['publication']={}
            self.assertFalse(assess(case,bad)['passed'])
            bad=copy.deepcopy(report);bad['aa_ownership_probe']['steps'][-1]['release_packets']['table_before_clear']=True
            self.assertFalse(assess(case,bad)['passed'])

if __name__=='__main__': unittest.main()
