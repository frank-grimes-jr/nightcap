import copy
import math
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tunnel_compact as compact
import tunnel_social as social
from tunnel_courts import class_members
from tunnel_services import pos,spawn_position
from tunnel_campfire import RING
from tunnel_compact_layout import CLASS_AREAS,CLASS_FIRES,SUPPLIES,STATIONS,placements,paths
from test_tunnel_social import fixture as original_fixture


def fixture():
    before=social.desired(original_fixture())
    before['rows']['doors']=[dict(id='999606',zone='ecommons',version='0',doorid='211',name='CAMPFIRE',
        pos_x='-274',pos_y='-1707',pos_z='0',heading='0',size='65',opentype='58',dest_zone='NONE')]
    for spawn in before['rows']['spawn2']:
        ident=int(spawn['spawngroupID'])
        if ident in RING:spawn.update(spawn_position(pos(*RING[ident],-274,-1707)))
    for ident in (997900,999523):
        before['rows']['zone_state_spawns'].append(dict(id=str(ident),npc_id=str(ident),spawngroup_id=str(ident),spawn2_id=str(ident),zone_id='22',instance_id='0',is_zone='0',is_corpse='0'))
    before['scopes']=compact.SCOPES
    return before


class CompactServices(unittest.TestCase):
    def test_all_classes_have_close_counterparts_and_consistent_facing(self):
        self.assertEqual(sorted(c for _,classes,_ in CLASS_AREAS for c in classes),list(range(1,17)))
        for _,classes,center in CLASS_AREAS:
            for cls in classes:
                a,b=(placements()[i] for i in class_members()[cls])
                self.assertEqual(math.dist((a['x'],a['y']),(b['x'],b['y'])),12)
                for p in (a,b):
                    h=p['heading']*math.tau/512
                    toward=(center[0]-p['x'],center[1]-p['y'])
                    self.assertGreater((math.sin(h)*toward[0]+math.cos(h)*toward[1])/math.hypot(*toward),.999)

    def test_workshop_is_compact_and_contains_all_suppliers_and_stations(self):
        self.assertEqual(set(SUPPLIES),set(range(999600,999622)))
        points=[p[:2] for p in SUPPLIES.values()]+[p[1:3] for p in STATIONS.values()]
        area=(max(x for x,y in points)-min(x for x,y in points))*(max(y for x,y in points)-min(y for x,y in points))
        self.assertLessEqual(area,11270)
        self.assertEqual(len(STATIONS),6)

    def test_accepted_residents_native_npcs_appearances_names_and_stock_links_survive(self):
        before=fixture();after=compact.desired(before)
        self.assertEqual(before['rows']['npc_types'],after['rows']['npc_types'])
        self.assertEqual(before['rows']['doors'],after['rows']['doors'][:1])
        changed=compact.moved(before,after)
        self.assertFalse(changed & (set(RING)|social.NATIVES|{999220}))
        self.assertEqual({int(s['npc_id']) for s in after['rows']['zone_state_spawns']},{22089,999523})
        for table in ('spawngroup','spawnentry','grid'):self.assertEqual(before['rows'][table],after['rows'][table])

    def test_exactly_four_nonfunctional_class_landmarks(self):
        after=compact.desired(fixture())
        fires=after['rows']['doors'][1:]
        self.assertEqual({int(f['id']) for f in fires},set(CLASS_FIRES))
        self.assertTrue(all(f['name']=='CAMPFIRE' and f['size']=='45' and f['dest_zone']=='NONE' for f in fires))

    def test_mutation_budget_rejects_appearance_gameplay_native_and_resident_changes(self):
        before=fixture();after=compact.desired(before)
        sql=compact.patch_sql(before,after)
        self.assertLessEqual(set(re.findall(r'(?:UPDATE|INSERT INTO|DELETE FROM) `(\w+)`',sql)),{'spawn2','grid_entries','object','doors','zone_state_spawns'})
        for table,key,value in [('npc_types','race','99'),('npc_types','merchant_id','1'),('object','type','99'),('spawn2','pathgrid','1')]:
            bad=copy.deepcopy(after);bad['rows'][table][0][key]=value
            with self.assertRaises(ValueError):compact.patch_sql(before,bad)
        for ident in ('999523','22089'):
            bad=copy.deepcopy(after)
            row=next(s for s in bad['rows']['spawn2'] if s['spawngroupID']==(ident if ident=='999523' else '122089'))
            row['x']='0'
            with self.assertRaisesRegex(ValueError,'Preserved'):compact.patch_sql(before,bad)
        bad=copy.deepcopy(after);bad['rows']['zone_state_spawns']=[]
        with self.assertRaisesRegex(ValueError,'Unchanged'):compact.patch_sql(before,bad)

    def test_replay_collisions_and_grid_drift_rejected(self):
        with self.assertRaises(ValueError):compact.desired(compact.desired(fixture()))
        for field,value in [('id','999607'),('doorid','212')]:
            before=fixture();before['rows']['doors'].append(dict(before['rows']['doors'][0],**{field:value}))
            with self.assertRaisesRegex(ValueError,'collision'):compact.desired(before)
        before=fixture();before['rows']['grid'][0]['zoneid']='202'
        with self.assertRaises(ValueError):compact.desired(before)

    def test_rollback_keeps_fresh_unmoved_cache_and_invalidates_only_moved(self):
        before=fixture();after=compact.desired(before);current=copy.deepcopy(after)
        current['rows']['zone_state_spawns'][-1]['x']='-123'
        current['rows']['zone_state_spawns'].append(copy.deepcopy(before['rows']['zone_state_spawns'][-2]))
        target=compact.rollback_target(before,current,after)
        self.assertEqual(target['rows']['zone_state_spawns'],current['rows']['zone_state_spawns'][:-1])
        compact.patch_sql(current,target)
        for table in compact.KEYS:
            if table!='zone_state_spawns':self.assertEqual(before['rows'][table],target['rows'][table])

if __name__=='__main__':unittest.main()
