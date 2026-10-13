"""Check the policy-counting boundaries that can materially alter this audit."""
import copy
import gzip
import json
import unittest
from analyze import Catalog, HERE


def ability(aid, first, classes=1, grant=0):
    return dict(id=aid,name=str(aid),first_rank_id=first,classes=classes,
                enabled=1,category=-1,status=0,grant_only=grant)


def rank(rid,next_id=-1,expansion=3,cost=2):
    return dict(id=rid,next_id=next_id,expansion=expansion,level_req=1,cost=cost,spell=-1)


class AnalysisTests(unittest.TestCase):
    def catalog(self, abilities, ranks, prereqs=()):
        return Catalog({'aa_ability':abilities,'aa_ranks':ranks,'aa_rank_prereqs':prereqs})

    def test_cutoff_stops_chain_before_later_rank_even_if_next_returns_to_old_era(self):
        c=self.catalog([ability(1,10)],[rank(10,11),rank(11,12,14),rank(12)])
        p,_=c.pool(cutoff=13)
        self.assertEqual([r['id'] for r in p[1]],[10])

    def test_dependencies_are_rank_counts_and_inherit(self):
        c=self.catalog([ability(1,10),ability(2,20)],[rank(10,11),rank(11),rank(20,21),rank(21)],
                       [dict(rank_id=10,aa_id=2,points=2)])
        self.assertEqual(c.chains[1][1]['prereqs'],{2:2})
        p,b=c.pool();self.assertEqual([len(p[1]),len(p[2])],[2,2]);self.assertFalse(b)
        p,b=c.pool(overrides={'1':2,'2':1});self.assertNotIn(1,p);self.assertEqual(len(b),1)

    def test_missing_and_grant_only_dependencies_are_not_silently_granted(self):
        for abilities in ([ability(1,10)], [ability(1,10),ability(2,20,grant=1)]):
            c=self.catalog(abilities,[rank(10),rank(20)], [dict(rank_id=10,aa_id=2,points=1)])
            self.assertEqual(c.pool()[0],{})

    def test_union_deduplicates_and_unlocks_cross_class_dependency(self):
        c=self.catalog([ability(1,10,1),ability(2,20,2),ability(3,30,3)],
                       [rank(10),rank(20),rank(30)], [dict(rank_id=10,aa_id=2,points=1)])
        self.assertEqual(set(c.pool(mask=1)[0]),{3})
        p,_=c.pool(mask=3);self.assertEqual(c.stats(p)['points'],6)

    def test_missing_tail_retains_valid_prefix_and_cycles_fail(self):
        c=self.catalog([ability(1,10)],[rank(10,99)])
        self.assertEqual(len(c.pool()[0][1]),1)
        with self.assertRaises(ValueError):
            self.catalog([ability(1,10)],[rank(10,10)])

    def test_shared_enabled_rank_rejected(self):
        with self.assertRaises(ValueError):
            self.catalog([ability(1,10),ability(2,10)],[rank(10)])

    def test_mutual_prerequisites_cannot_bootstrap(self):
        c=self.catalog([ability(1,10),ability(2,20)],[rank(10),rank(20)],
                       [dict(rank_id=10,aa_id=2,points=1),dict(rank_id=20,aa_id=1,points=1)])
        self.assertEqual(c.pool()[0],{})

    def test_production_snapshot_invariants_and_monotonicity(self):
        t=json.load(gzip.open(HERE/'production-snapshot.json.gz','rt'))['tables'];c=Catalog(t)
        self.assertEqual(len(c.abilities),len(t['aa_ability']))
        self.assertEqual(len(c.ranks),len(t['aa_ranks']))
        self.assertEqual({r['level_req'] for r in c.ranks.values()},{1})
        for mask in [65535]+[1<<i for i in range(16)]:
            old,_=c.pool(mask,13);full,_=c.pool(mask)
            for aid,chain in old.items():
                self.assertEqual(chain,full[aid][:len(chain)])
                self.assertTrue(all(r['expansion']<=13 for r in chain))
                for r in chain:
                    self.assertTrue(all(len(old.get(dep,[]))>=n for dep,n in r['prereqs'].items()))
            self.assertEqual(old,c.pool(mask,12)[0])


if __name__=='__main__':
    unittest.main(verbosity=2)
