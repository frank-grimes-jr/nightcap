"""Evidence identity, earned progression, multiclass capacity and safe content delta."""
from collections import Counter,defaultdict
import copy
import itertools
import os
import unittest

import all_class_aa as aa
from aa_tbs_policy import compile_policy


class AllClassAA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config,cls.tables,cls.old,cls.rows,cls.ledger=aa.prepare()
        cls.old_config,cls.before=aa.baseline()
        cls.caps=Counter(r['ability_id'] for r in cls.rows)

    def test_full_566_disposition_and_exact_admitted_identity(self):
        source=aa.read_json(aa.RELEASE/'thj-ranks.json')['abilities']
        self.assertEqual(len(self.ledger),566)
        self.assertEqual({r['ability_id'] for r in self.ledger},{r['id'] for r in source})
        old={r['rank_id'] for r in self.old}
        evidence={r['id']:{rank['id'] for rank in r['ranks']} for r in source}
        for r in self.rows:
            if r['rank_id'] not in old:
                self.assertIn(r['rank_id'],evidence[r['ability_id']])
                self.assertIn('requested',next(d for d in self.ledger if d['ability_id']==r['ability_id']))
        self.assertTrue(all(row['decision'] for row in self.ledger))

    def test_no_earned_rank_cost_identity_or_starter_regression(self):
        self.assertLessEqual({r['rank_id'] for r in self.old},{r['rank_id'] for r in self.rows})
        for table in ('aa_ranks','aa_rank_effects','aa_rank_prereqs'):
            self.assertEqual(self.tables[table],self.before[table])
        before={r['id']:r for r in self.before['aa_ability']}
        for row in self.tables['aa_ability']:
            expected=copy.deepcopy(before[row['id']])
            if row['id']==389:expected['classes']=550
            self.assertEqual(row,expected)
        ranks={r['id']:r for r in self.tables['aa_ranks']}
        old={r['rank_id'] for r in self.old}
        self.assertTrue(all(ranks[r['rank_id']]['cost']>0 for r in self.rows if r['rank_id'] not in old))
        self.assertEqual({r['level'] for r in self.rows},{1})
        self.assertEqual(self.config['expansion_max'],self.old_config['expansion_max'])
        self.assertEqual(self.config['prerequisite_waivers'],self.old_config['prerequisite_waivers'])
        old_caps=Counter(r['ability_id'] for r in self.old)
        for aid in aa.PRESERVED|{6000,6001,6002,25,334,492,516}:
            self.assertEqual(self.caps[aid],old_caps[aid],aid)

    def test_every_class_receives_new_class_specific_options_and_depth(self):
        expected=(3732,506,3500,877,825,1092,3805,359,3515,3729,751,397,3516,602,986,4002)
        old={r['ability_id'] for r in self.old}
        for cl,aid in enumerate(expected):
            self.assertNotIn(aid,old)
            self.assertTrue(any(r['ability_id']==aid and r['classes']&(1<<cl) for r in self.rows))
        self.assertEqual(self.caps[397],9)
        self.assertEqual(self.caps[359],3)
        self.assertEqual(self.caps[541],3)
        for aid in (32,218,555,309,914,17785,17786,16001):self.assertEqual(self.caps[aid],0)
        self.assertEqual(self.caps[389],6)
        _,summary=aa.report(self.old,self.rows,self.ledger)
        druid=summary[5]
        class_delta=aa.changes([r for r in self.old if r['classes']&32],[r for r in self.rows if r['classes']&32])
        boon=next(r for r in class_delta if r['id']==389)
        self.assertEqual((boon['before'],boon['after'],boon['kind']),(0,6,'Added'))
        self.assertEqual(druid['added_lines'],sum(r['kind']=='Added' for r in class_delta))

    def test_every_prefix_and_prerequisite_remains_closed(self):
        keys={(r['ability_id'],r['ordinal']) for r in self.rows}
        for row in self.rows:
            if row['ordinal']>1:self.assertIn((row['ability_id'],row['ordinal']-1),keys)
            for aid,n in row['prereqs'].items():self.assertIn((int(aid),n),keys)
        blocked=[r for r in self.ledger if r.get('requested',0)>r['after']]
        self.assertTrue(blocked)
        self.assertTrue(all('prerequisite' in r['decision'] for r in blocked))

    def test_all_696_class_masks_fit_native_100_timer_slots(self):
        coverage=aa.coverage(self.rows,self.tables)
        self.assertEqual(coverage['class_masks'],696)
        self.assertLess(coverage['max_timer_slots'],100)
        self.assertEqual(coverage['max_timer_slots'],74)

    def test_all_696_class_masks_keep_positive_effective_activation_cooldowns(self):
        ranks={r['id']:r for r in self.tables['aa_ranks']}
        effects=defaultdict(list)
        for effect in self.tables['aa_rank_effects']:effects[effect['rank_id']].append(effect)
        max_ranks={}
        for row in sorted(self.rows,key=lambda r:r['ordinal']):max_ranks[row['ability_id']]=row
        for size in (1,2,3):
            for combo in itertools.combinations(range(16),size):
                mask=sum(1<<cl for cl in combo)
                eligible=[r for r in max_ranks.values() if r['classes']&mask]
                # Conservative maximum: even prerequisite-unreachable held ranks
                # contribute reductions, so this cannot understate haste risk.
                reduction=defaultdict(int)
                for row in eligible:
                    for e in effects[row['rank_id']]:
                        if e['effect_id']==264:reduction[e['base2']]+=e['base1']
                for row in self.rows:
                    r=ranks[row['rank_id']]
                    if row['classes']&mask and 0<r['spell']<65535 and r['recast_time']>0:
                        self.assertGreater(r['recast_time']-reduction[row['ability_id']],0,(combo,row['ability_id']))

    def test_generated_policy_content_report_and_ledger_are_current(self):
        for path,expected in aa.artifacts().items():
            actual=path.read_bytes() if isinstance(expected,bytes) else path.read_text(encoding='utf-8')
            self.assertEqual(actual,expected if isinstance(expected,bytes) else expected.replace('\r\n','\n'),str(path))

    @unittest.skipUnless(os.environ.get('NIGHTCAP_DB_TESTS')=='1','isolated DB rehearsal opt-in')
    def test_sql_replay_rollback_and_drift_rejection_preserve_owned_state(self):
        from pok_hub_migration import read_sql
        from wpm_migration import insert,migration
        g=aa.groups(self.tables)[0]
        setup=['DROP PROCEDURE IF EXISTS allclass_test;',
               'CREATE TEMPORARY TABLE allclass_template LIKE peq.aa_ability;',
               'CREATE TEMPORARY TABLE aa_ability LIKE allclass_template;',insert('aa_ability',g['before'][0]),
               'CREATE TEMPORARY TABLE character_alternate_abilities (id INT PRIMARY KEY,aa_value INT) ENGINE=InnoDB;',
               'INSERT INTO character_alternate_abilities VALUES (1186,6);']
        forward=migration([g],'allclass_test')
        reverse=migration([{**g,'before':g['after'],'after':g['before']}],'allclass_test')
        query='\n'.join(setup+[forward,forward,"SELECT 'FORWARD',classes FROM aa_ability WHERE id=389;",
                            reverse,reverse,"SELECT 'ROLLBACK',classes FROM aa_ability WHERE id=389;",
                            "SELECT 'OWNED',aa_value FROM character_alternate_abilities WHERE id=1186;"])
        results=dict(line.split('\t') for line in read_sql(query).splitlines() if '\t' in line)
        self.assertEqual(results,{'FORWARD':'550','ROLLBACK':'518','OWNED':'6'})
        with self.assertRaises(RuntimeError):
            read_sql('\n'.join(setup+["UPDATE aa_ability SET name='DRIFT' WHERE id=389;",forward]))
        read_sql('DROP PROCEDURE IF EXISTS allclass_test;')


if __name__=='__main__':unittest.main()
