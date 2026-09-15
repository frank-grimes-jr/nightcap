import gzip
import json
from pathlib import Path
import unittest

from pet_threat_controls import verify


class PetThreatNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs=Path(__file__).resolve().parents[3]/'docs/balance'
        cls.original=cls.read('gear-source-inputs.json')
        cls.catalog=cls.read('native-aa-catalog.json')

    @classmethod
    def read(cls,name):
        raw=(cls.docs/name).read_bytes()
        return json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)

    def test_all_nine_strategy_pilots_verify_native_inputs_and_outcomes(self):
        for stem,count in (('pet-threat-pilot',6),('pet-threat-escape',3)):
            self.assertEqual(len(verify(self.read(stem+'-inputs.json'),self.read(stem+'.json.gz'),
                                        self.original,self.catalog)),count)

    def test_successful_feigns_actually_clear_owner_hate(self):
        active=[]
        for run in self.read('pet-threat-pilot.json.gz')['runs']:
            combat=run['report']['pet_probe']['combat']
            if combat['threat_control']['policy']!='feign_on_aggro':continue
            active.append(run)
            self.assertTrue(any(a['spell']==366 and a.get('owner_feigned_after')
                                and a['owner_hate_before']>0 and a['owner_hate_after']==0
                                and a['boss_target_after']!=combat['player_id']
                                for a in combat['owner_actions']))
        self.assertEqual(len(active),3)

    def test_twelve_original_gear_reports_are_byte_identical(self):
        old={r['id']:r for r in self.read('gear-source.json.gz')['runs']}
        runs=self.read('pet-threat-regression.json.gz')['runs']
        self.assertEqual(len(runs),12)
        for run in runs:
            self.assertEqual(run['native_raw_sha256'],old[run['id']]['native_raw_sha256'])
            self.assertEqual(run['report'],old[run['id']]['report'])

    def test_emergency_policy_addition_preserves_six_initial_pilot_reports(self):
        old={r['id']:r for r in self.read('pet-threat-pilot.json.gz')['runs']}
        runs=self.read('pet-threat-pilot-regression.json.gz')['runs']
        self.assertEqual(len(runs),6)
        for run in runs:
            self.assertEqual(run['native_raw_sha256'],old[run['id']]['native_raw_sha256'])
            self.assertEqual(run['report'],old[run['id']]['report'])


if __name__=='__main__':unittest.main()
