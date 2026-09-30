import copy
import json
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tunnel_courts import (class_members, roman_title, appearance, CLASS_STYLES,
                          placements, IDS, KHALEID, KEYS, desired, rollback_target, patch_sql)

def fixture():
    rows={t:[] for t in KEYS}
    for ident in sorted(IDS-{KHALEID}):
        cls=ident-999649+19 if 999650<=ident<=999665 else 6 if ident==999525 else 41
        row={k:str(v) for k,v in appearance((1,0,0,6),0).items()}
        row.update(id=str(ident),name='NPC_'+str(ident),lastname='Alchemy Supplies 2' if ident==999612 else 'Supplies',
            **{'class':str(cls)},hp='12345',AC='77',merchant_id=str(ident if cls==41 else 0),
            loottable_id='0',level='50',maxlevel='50',npc_spells_id='0',npc_spells_effects_id='0',
            prim_melee_type='1',skip_global_loot='1')
        rows['npc_types'].append(row)
        rows['spawngroup'].append(dict(id=str(ident),name='Group'+str(ident)))
        rows['spawnentry'].append(dict(spawngroupID=str(ident),npcID=str(ident),chance='100'))
        rows['spawn2'].append(dict(id=str(3266027 if ident==999225 else ident),spawngroupID=str(ident),
            zone='ecommons',version='0',pathgrid='0',x='-200',y='-1700',z='3.75',heading='0'))
    return dict(rows=rows)


class TunnelCourts(unittest.TestCase):
    def test_classes_keep_one_trainer_and_one_shop_with_matching_uniforms(self):
        groups=class_members()
        self.assertEqual(set(groups),set(range(1,17)))
        self.assertEqual(len({i for pair in groups.values() for i in pair}),32)
        for cls,(trainer,merchant) in groups.items():
            self.assertEqual(trainer,999649+cls)
            self.assertEqual(merchant,997899+cls)
            self.assertIn(appearance(CLASS_STYLES[cls],0)['race'],range(1,13))

    def test_migration_preserves_stock_links_stats_and_class_functions(self):
        before=fixture();after=desired(before)
        old={n['id']:n for n in before['rows']['npc_types']}
        new={n['id']:n for n in after['rows']['npc_types']}
        for ident,n in old.items():
            for key in ('name','class','hp','AC','merchant_id','loottable_id'):
                self.assertEqual(n[key],new[ident][key],(ident,key))
        for cls,(trainer,merchant) in class_members().items():
            a,b=new[str(trainer)],new[str(merchant)]
            for key in ('race','texture','helmtexture','size','armortint_red','armortint_green','armortint_blue'):
                self.assertEqual(a[key],b[key],(cls,key))
            self.assertEqual({a['gender'],b['gender']},{'0','1'})
        self.assertEqual(new['999525']['lastname'],'Druid Rings')
        self.assertEqual(new['999612']['lastname'],'Alchemy Supplies II')
        self.assertEqual(len(after['rows']['npc_types']),len(old)+1)
        self.assertEqual(next(r for r in after['rows']['spawn2'] if r['spawngroupID']=='999225')['id'],'3266027')

    def test_khaleid_has_classic_display_only_equipment(self):
        n=next(n for n in desired(fixture())['rows']['npc_types'] if n['id']==str(KHALEID))
        for k,v in dict(name='Khaleid',lastname='Wizard Spires',race='6',gender='0',texture='15',
                        d_melee_texture1='122',d_melee_texture2='0',loottable_id='0',merchant_id='0',
                        skip_global_loot='1',armortint_red='175',armortint_green='10',armortint_blue='50').items():
            self.assertEqual(n[k],v,k)

    def test_collision_or_shared_reference_blocks_generation(self):
        for table,row in [('npc_types',dict(id=str(KHALEID))),
            ('spawn2',dict(id='8',spawngroupID='999525')),
            ('spawnentry',dict(spawngroupID='7',npcID='999525')),
            ('npc_types_tint',dict(id=str(KHALEID)))]:
            before=fixture();before['rows'][table].append(row)
            with self.assertRaises(ValueError):desired(before)

    def test_only_unambiguous_instance_zero_saved_states_can_be_invalidated(self):
        before=fixture()
        state=dict(id='1',npc_id='999525',spawngroup_id='999525',spawn2_id='999525',
                   zone_id='22',instance_id='0',is_corpse='0',is_zone='0')
        for changes in ({'is_corpse':'1'},{'is_zone':'1'},{'instance_id':'1'},{'zone_id':'202'},
                        {'spawn2_id':'999650'},{'spawngroup_id':'999650'}):
            before['rows']['zone_state_spawns']=[dict(state,**changes)]
            with self.assertRaisesRegex(ValueError,'Ambiguous'):desired(before)
        before['rows']['zone_state_spawns']=[state]
        self.assertEqual(desired(before)['rows']['zone_state_spawns'],[])

    def test_rollback_requires_exact_static_content_but_accepts_fresh_safe_state(self):
        before=fixture();expected=desired(before);current=copy.deepcopy(expected)
        current['rows']['zone_state_spawns']=[dict(id='9',npc_id=str(KHALEID),spawngroup_id=str(KHALEID),
            spawn2_id=str(KHALEID),zone_id='22',instance_id='0',is_zone='0',is_corpse='0')]
        self.assertEqual(rollback_target(before,current,expected),before)
        current['rows']['npc_types'][0]['name']='Changed'
        with self.assertRaisesRegex(ValueError,'Rollback content drift'):rollback_target(before,current,expected)

    def test_generated_sql_only_writes_content_tables(self):
        import re
        before=fixture();sql=patch_sql(before,desired(before))
        writes=set(re.findall(r'(?:UPDATE|INSERT INTO|DELETE FROM) `(\w+)`',sql))
        self.assertLessEqual(writes,set(KEYS))
        self.assertNotIn('merchantlist',writes)
        self.assertNotIn('items',writes)
        self.assertIn('ROLLBACK; RESIGNAL',sql)
        self.assertLess(sql.index('Court row drift'),sql.index('UPDATE `npc_types`'))

    def test_spillover_titles_use_roman_numerals_only(self):
        for n,roman in [(1,'I'),(2,'II'),(3,'III'),(4,'IV'),(9,'IX'),(12,'XII')]:
            self.assertEqual(roman_title('Alchemy Supplies '+str(n)), 'Alchemy Supplies '+roman)
        self.assertEqual(roman_title('Pottery Supplies'),'Pottery Supplies')
        with self.assertRaises(ValueError):roman_title('Supplies 0')

    def test_pairs_are_adjacent_and_courts_are_separated(self):
        import math
        p=placements()
        centers=[]
        for cls,(trainer,merchant) in class_members().items():
            a,b=p[trainer],p[merchant]
            self.assertAlmostEqual(math.hypot(a['x']-b['x'],a['y']-b['y']),16)
            self.assertEqual(a['heading'],b['heading'])
            centers.append(((a['x']+b['x'])/2,(a['y']+b['y'])/2))
        self.assertGreater(len({x for x,y in centers}),6)
        self.assertGreater(len({y for x,y in centers}),6)

if __name__=='__main__':unittest.main()
