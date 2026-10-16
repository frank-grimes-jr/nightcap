"""Production generator contract: restrict writes and retain fresh recovery state."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unrest_waypoint as content

def fixture():
    def spawn(ident,group,pose):
        row=dict(id=str(ident),zone='unrest',version='0',spawngroupID=str(group),pathgrid='0')
        content.set_pose(row,pose,'spawn2');return row
    rows={
      'spawn2':[spawn(3266123,999240,content.OLD),spawn(3266037,999228,content.NEW)],
      'nightcap_waypoints':[dict(zone='unrest',zone_id='63',x='118',y='881',z='3.75',heading='0',is_dungeon='0')],
      'zone_state_spawns':[dict(id='1',zone_id='63',instance_id='0',is_corpse='0',is_zone='0',npc_id='999240',spawn2_id='3266123',spawngroup_id='999240',x='118',y='881',z='3.85',heading='0',hp='60000',loot_data='keep')],
      'npc_types':[dict(id='999240',name='a_waypoint'),dict(id='999228',name='Instance_Keeper')],
      'spawnentry':[dict(spawngroupID=str(i),npcID=str(i),chance='100') for i in (999240,999228)]}
    return dict(rows=rows,scopes=content.SCOPES,schemas={})

class ContentTests(unittest.TestCase):
    def test_target_matches_reviewed_relocation(self):
        before=fixture();after=content.desired(before)
        self.assertEqual(content.coordinates(content.topology(after['rows'])[999240]),content.NEW)
        self.assertEqual(content.coordinates(after['rows']['nightcap_waypoints'][0]),content.NEW)
        sql=content.patch_sql(before,after)
        self.assertIn('ENGINE=',sql);self.assertIn('ROLLBACK; RESIGNAL',sql)
        self.assertNotIn('DELETE FROM',sql);self.assertNotIn('INSERT INTO',sql)
    def test_saved_identity_boundaries(self):
        before=fixture();marker=before['rows']['zone_state_spawns'][0]
        controls=[dict(marker,id=str(i+2),**change) for i,change in enumerate((dict(is_corpse='1'),dict(is_zone='1'),dict(instance_id='9'),dict(npc_id='999228'),dict(spawn2_id='4'),dict(spawngroup_id='3')))]
        before['rows']['zone_state_spawns']+=controls
        before['rows']['zone_state_spawns'].append(dict(marker,id='9',npc_id='0'))
        after=content.desired(before)
        self.assertEqual(after['rows']['zone_state_spawns'][1:7],controls)
        self.assertEqual(content.coordinates(after['rows']['zone_state_spawns'][-1]),content.NEW)
    def test_roll_back_only_pose_after_activity(self):
        before=fixture();after=content.desired(before);current=copy.deepcopy(after)
        row=current['rows']['zone_state_spawns'][0];row.update(hp='700',loot_data='new')
        current['rows']['zone_state_spawns'].append(dict(row,id='55',is_corpse='1'))
        target=content.rollback_target(before,current,after)
        self.assertEqual(target['rows']['zone_state_spawns'][1],current['rows']['zone_state_spawns'][1])
        self.assertEqual(target['rows']['zone_state_spawns'][0]['hp'],'700')
        self.assertEqual(content.coordinates(target['rows']['zone_state_spawns'][0]),content.OLD)
        content.patch_sql(current,target)
    def test_forbids_nonpose_and_keeper_changes(self):
        for table,key,value in [('spawn2','spawngroupID','0'),('nightcap_waypoints','is_dungeon','1'),('zone_state_spawns','loot_data','bad'),('npc_types','name','bad')]:
            before=fixture();after=content.desired(before);after['rows'][table][0][key]=value
            with self.subTest(table=table),self.assertRaises(ValueError):content.patch_sql(before,after)
        before=fixture();after=content.desired(before);after['rows']['spawn2'][1]['x']='0.000000'
        with self.assertRaises(ValueError):content.patch_sql(before,after)
    def test_rejects_location_and_group_drift(self):
        for table,key,value in [('spawn2','x','119'),('nightcap_waypoints','x','119'),('spawnentry','chance','50')]:
            before=fixture();before['rows'][table][0][key]=value
            with self.subTest(table=table),self.assertRaises(ValueError):content.desired(before)
    def test_unknown_target_refused(self):
        before=fixture();after=content.desired(before)
        for row in (after['rows']['spawn2'][0],after['rows']['nightcap_waypoints'][0]):row['x']='999'
        with self.assertRaises(ValueError):content.patch_sql(before,after)

if __name__=='__main__':unittest.main()
