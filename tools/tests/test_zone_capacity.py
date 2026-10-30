"""Guard the observed capacity regression, scoped timer plan and rollout budgets."""
import copy
import datetime
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))


class DeploymentRegression(unittest.TestCase):
    def test_default_pool_has_room_for_original_thirteen_destinations_and_reserve(self):
        text = (ROOT / 'deploy/production/compose.yaml').read_text()
        self.assertIn('NIGHTCAP_ZONE_WORKERS: "20"', text)


class CapacityPolicyTests(unittest.TestCase):
    def setUp(self):
        import zone_capacity
        self.policy = zone_capacity
        self.before = {'rows': {'zone': [dict(id=str(i), short_name=name,
            version='0', zoneidnumber=str(zone), shutdowndelay='3600000',
            long_name='preserve', safe_x='1.25')
            for i, (name, zone) in enumerate(self.policy.TRAVEL_ZONES.items(), 1)]}}
        self.before['rows']['zone'] += [dict(id='100', short_name='fearplane', version='0',
            zoneidnumber='72', shutdowndelay='3600000'), dict(id='101',short_name='airplane',
            version='0',zoneidnumber='71',shutdowndelay='43200000')]

    def test_only_audited_version_zero_retention_changes(self):
        before = copy.deepcopy(self.before)
        after = self.policy.plan(before)
        self.assertEqual(before, self.before)
        for old, new in zip(before['rows']['zone'], after['rows']['zone']):
            expected = dict(old)
            if old['short_name'] in self.policy.TRAVEL_ZONES:
                expected['shutdowndelay'] = str(self.policy.DELAYS[old['short_name']])
            self.assertEqual(new, expected)

    def test_missing_duplicate_changed_identity_and_timer_reject(self):
        variants = []
        for field, value in [('short_name','fearplane'),('zoneidnumber','72'),
                             ('version','1'),('shutdowndelay','300000')]:
            changed = copy.deepcopy(self.before)
            changed['rows']['zone'][0][field] = value
            variants.append(changed)
        missing = copy.deepcopy(self.before); missing['rows']['zone'].pop(0); variants.append(missing)
        duplicate = copy.deepcopy(self.before); duplicate['rows']['zone'].append(duplicate['rows']['zone'][0]); variants.append(duplicate)
        for variant in variants:
            with self.subTest(variant=variant), self.assertRaises(ValueError):
                self.policy.plan(variant)

    def test_inverse_guards_exact_afterimage_and_never_touches_player_state(self):
        forward, inverse = self.policy.generate(self.before)
        for text in (forward, inverse):
            self.assertIn('FOR UPDATE', text)
            self.assertIn('ROLLBACK; RESIGNAL;', text)
            self.assertIn("ENGINE='InnoDB'", text)
            self.assertIn('information_schema.TRIGGERS', text)
            self.assertNotIn('DELETE FROM', text)
            self.assertNotIn('character_', text)
            self.assertNotIn('zone_state_', text)
            self.assertNotIn('UPDATE `zone` SET `safe_x`', text)

    def test_resource_gate_requires_disk_and_memory_reserve(self):
        mib = 1024**2
        resource = {'disk_free':4*1024**3, 'native':{'memory_peak':1579*mib,
                    'memory_current':1100*mib,'memory_limit':4500*mib},
                    'host_memory':{'MemAvailable':4000*mib},
                    'worker_env':['NIGHTCAP_ZONE_WORKERS=12']}
        self.assertEqual(self.policy.resource_blockers(resource), [])
        resource['disk_free'] = 512*mib
        self.assertTrue(any('disk' in x for x in self.policy.resource_blockers(resource)))
        resource['disk_free'] = 4*1024**3
        resource['native']['memory_peak'] = 2300*mib
        self.assertTrue(any('memory' in x for x in self.policy.resource_blockers(resource)))

    def test_original_route_fails_old_pool_and_passes_new_plan(self):
        # Seconds after18:50. One-hour retention (Kithicor1day) kept every
        # successful destination resident until the13th request at19:43:33.
        visits = [('ecommons',0),('misty',163),('rivervale',213),('kithicor',242),
                  ('highpasshold',354),('highkeep',413),('highkeep-102',432),
                  ('highpasshold',860),('eastkarana',936),('ecommons',1162),
                  ('befallen',1392),('commons',1400),('chapterhouse-103',1427),
                  ('commons',1464),('chapterhouse-103',1485),('ecommons',1568),
                  ('feerrott',3070),('fearplane',3213)]
        def replay(workers, delays):
            loaded = {}; current = None
            for zone, now in visits:
                if current is not None:
                    loaded[current] = now + delays.get(current, 86400 if current == 'kithicor' else 3600)
                loaded = {z:until for z,until in loaded.items() if until>now}
                if zone not in loaded and len(loaded)>=workers:
                    return zone
                loaded[zone] = float('inf'); current = zone
            return None
        self.assertEqual(replay(12,{}), 'fearplane')
        self.assertIsNone(replay(self.policy.WORKERS,{z:ms/1000 for z,ms in self.policy.DELAYS.items()}))

    def test_sustained_travel_reuses_slots_with_thirteen_retained_destinations(self):
        def replay(delays):
            loaded = {f'retained-{i}':float('inf') for i in range(13)}
            current = None
            route = ['ecommons','feerrott','commons','highpasshold',
                     'rivervale','eastkarana','misty','befallen'] * 20
            for step, name in enumerate(route):
                now = step * 120
                if current:
                    loaded[current] = now + delays.get(current,3600)
                loaded = {z:t for z,t in loaded.items() if t>now}
                if name not in loaded and len(loaded)>=self.policy.WORKERS:
                    return False
                loaded[name] = float('inf'); current = name
            return True
        self.assertFalse(replay({}))
        self.assertTrue(replay({z:ms/1000 for z,ms in self.policy.DELAYS.items()}))

    def test_preflight_rejects_stale_unsafe_rules_and_oom(self):
        mib=1024**2
        now=datetime.datetime(2026,10,30,tzinfo=datetime.timezone.utc)
        sample={'captured_at':now.isoformat(), 'rules':'1\tZone:StateSavingOnShutdown\ttrue\n1\tZone:KillProcessOnDynamicShutdown\tfalse\n',
                'resources':{'disk_free':4*1024**3,'native':{'memory_peak':1579*mib,
                'memory_current':1100*mib,'memory_limit':4500*mib,'memory_events':'oom 0\noom_kill 0\n'},
                'host_memory':{'MemAvailable':4000*mib},'worker_env':['NIGHTCAP_ZONE_WORKERS=12'],
                'services':{'game':{'running':True,'oom':False}}}}
        self.assertEqual(self.policy.activation_blockers(sample,now),[])
        self.assertTrue(self.policy.activation_blockers(sample,now+datetime.timedelta(hours=2)))
        sample['rules'] += '2\tZone:KillProcessOnDynamicShutdown\ttrue\n'
        self.assertTrue(any('rule drift' in x for x in self.policy.activation_blockers(sample,now)))
        sample['resources']['native']['memory_events']='oom 1\noom_kill 1\n'
        self.assertTrue(any('OOM' in x for x in self.policy.activation_blockers(sample,now)))


if __name__ == '__main__':
    unittest.main()
