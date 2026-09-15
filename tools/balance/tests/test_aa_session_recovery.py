"""Regression checks on real recorded native session recovery evidence."""
from copy import deepcopy
import json
from pathlib import Path
import unittest
from run_aa_session_recovery import check_state

DOCS = Path(__file__).resolve().parents[3]/'docs/balance'


class SessionRecoveryEvidence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.evidence = json.loads((DOCS/'aa-session-recovery.json').read_text())

    def test_native_termination_and_single_refund(self):
        r = self.evidence
        self.assertEqual(r['status'],'passed')
        self.assertEqual(len(r['runs']),3)
        steps = [run['report']['aa_ownership_probe']['steps'] for run in r['runs']]
        self.assertEqual([len(s) for s in steps],[4,2,2])
        for index,s in enumerate(steps[0]):
            check_state(s,False,index==0)
        self.assertEqual(steps[0][2]['operation'],'process_invalid_session')
        self.assertFalse(steps[0][2]['success'])
        self.assertEqual(steps[0][2]['disconnect_events'],[{'event_type_id':11,'character_id':1}])
        self.assertEqual(steps[0][2]['saved_ingame'],0)
        self.assertEqual(steps[0][2]['stats_rows'],1)
        for i,released in ((1,False),(2,True)):
            check_state(steps[i][0],released)
            check_state(steps[i][1],True)
            self.assertEqual(steps[i][1]['success'],not released)
            self.assertEqual(r['inputs'][i]['builds'][0]['aa_budget'],999)
            self.assertNotIn('initial_spent_points',r['inputs'][i]['aa_ownership_probe'])
            self.assertEqual(r['runs'][i]['report']['builds'][0]['aa_remaining'],999)
            for s in steps[i]:
                self.assertTrue(s['connected'])
                self.assertFalse(s['release_packets']['transport_closed'])
                self.assertEqual(s['disconnect_events'],[])

    def test_disconnect_character_writes_and_restoration(self):
        check = self.evidence['character_row_check']
        before,after = [check[k].strip().split('\t') for k in ('before','after')]
        idx = check['columns'].index('ingame')
        self.assertEqual(before[idx],'1')
        before[idx] = '0'
        self.assertEqual(before,after)
        final = self.evidence['final']
        self.assertFalse(any(final['remaining_rows'].values()))
        self.assertTrue(all(v for k,v in final.items() if k!='remaining_rows'))

    def test_verifier_rejects_stale_reload_and_duplicate_refund(self):
        original = self.evidence['runs'][2]['report']['aa_ownership_probe']['steps'][0]
        for field,value in (('unspent_points',77),('earned_rank_count',6),
                            ('loaded_classes',[1,7,12]),('loaded_skills',[{'id':0,'value':260},{'id':4,'value':250}])):
            changed = deepcopy(original)
            changed[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                check_state(changed,True)


if __name__ == '__main__':
    unittest.main()
