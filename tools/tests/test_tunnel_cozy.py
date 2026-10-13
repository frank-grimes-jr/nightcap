import copy
import math
from pathlib import Path
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import tunnel_cozy as content
import tunnel_compact
from test_tunnel_compact import fixture as compact_fixture
from tunnel_cozy_layout import placements, SERVICES, SUPPLIERS, STATIONS
from probe_tunnel_cozy import preserved_frontage_issues

def fixture():
    before = tunnel_compact.desired(compact_fixture())
    donor = before['rows']['doors'][0]
    before['rows']['doors'] += [dict(donor,id='405',doorid='66',name='BARREL3',opentype='55'),
                               dict(donor,id='40600',doorid='200',name='HANGLANT',opentype='9')]
    before['scopes'] = content.SCOPES
    cache=dict(id='8000000',npc_id='999220',spawngroup_id='999220',spawn2_id='999220',
        zone_id='22',instance_id='0',is_corpse='0',is_zone='0',x='-141')
    before['rows']['zone_state_spawns'] += [cache,
        dict(cache,id='8000001',is_corpse='1'),dict(cache,id='8000002',instance_id='7'),
        dict(cache,id='8000003',is_zone='1'),dict(cache,id='8000004',npc_id='0')]
    return before

class CozyLayout(unittest.TestCase):
    def test_veyra_approach_rejects_old_candidate_and_accepts_corrected_forgemaster(self):
        veyra=('npc-999820',dict(x=-385,y=-1818,heading=0,gap=12))
        old=('npc-999226',dict(x=-383,y=-1801,heading=0,gap=12))
        new=('npc-999226',dict(placements()[999226],gap=12))
        self.assertEqual(len(preserved_frontage_issues([veyra,old],[old])),1)
        self.assertEqual(preserved_frontage_issues([veyra,new],[new]),[])

    def test_ambiguous_owned_cache_rejected_and_static_ornaments_cannot_trigger(self):
        before=fixture()
        next(s for s in before['rows']['zone_state_spawns'] if s['id']=='8000000')['spawn2_id']='123'
        with self.assertRaisesRegex(ValueError,'Ambiguous'):content.desired(before)
        after=content.desired(fixture())
        for door in after['rows']['doors'][-3:]:
            self.assertEqual((door['opentype'],door['triggerdoor'],door['door_param'],door['dest_zone']),('58','0','0','NONE'))

    def test_interactive_donor_drift_is_rejected_before_generation(self):
        for field in ('dz_switch_id','is_ldon_door','triggerdoor','triggertype','door_param',
                      'guild','lockpick','keyitem','nokeyring','dest_instance'):
            with self.subTest(field=field):
                before=fixture()
                next(d for d in before['rows']['doors'] if d['id']=='405')[field]='123'
                with self.assertRaisesRegex(ValueError,'Interactive ornament donor'):
                    content.desired(before)

    def test_services_near_buffers_and_workshop_has_varied_spacing(self):
        for pose in SERVICES.values():
            self.assertLess(min(math.dist(pose[:2], b) for b in [(-197,-1586),(-183,-1586)]),35)
        self.assertEqual(set(SUPPLIERS),set(range(999601,999622))|{999226})
        poses=list(placements().values())
        self.assertGreater(len({p['heading'] for p in poses}),18)
        self.assertGreater(len({p['y'] for p in poses}),20)
        for index,a in enumerate(poses):
            for b in poses[index+1:]:
                self.assertGreaterEqual(math.dist((a['x'],a['y']),(b['x'],b['y'])),14)

    def test_only_owned_poses_decor_and_noncorpse_instance_zero_cache_change(self):
        before=fixture();after=content.desired(before)
        content.patch_sql(before,after)
        for table in ('npc_types','spawngroup','spawnentry','grid','grid_entries'):
            self.assertEqual(before['rows'][table],after['rows'][table])
        self.assertEqual({r['id'] for r in before['rows']['zone_state_spawns']} -
                         {r['id'] for r in after['rows']['zone_state_spawns']},{'8000000','8000004'})
        self.assertEqual(len(after['rows']['doors'])-len(before['rows']['doors']),3)

    def test_replay_and_global_or_cross_version_door_collisions_rejected(self):
        before=fixture();after=content.desired(before)
        with self.assertRaises(ValueError):content.desired(after)
        for fields in [dict(id='999611',zone='unrelated'),dict(id='700000',doorid='216',version='1')]:
            bad=fixture();bad['rows']['doors'].append(dict(bad['rows']['doors'][0],**fields))
            with self.assertRaises(ValueError):content.desired(bad)

    def test_shared_missing_or_moving_spawn_rejected(self):
        for field,value in [('zone','qeynos'),('pathgrid','1'),('version','1')]:
            bad=fixture();s=next(s for s in bad['rows']['spawn2'] if s['spawngroupID']=='999220');s[field]=value
            with self.assertRaises(ValueError):content.desired(bad)
        bad=fixture();bad['rows']['spawnentry'].append(dict(spawngroupID='700000',npcID='999220',chance='100'))
        with self.assertRaises(ValueError):content.desired(bad)

    def test_mutation_budget_rejects_preserved_actors_gameplay_and_cache_loss(self):
        before=fixture();after=content.desired(before)
        for table,field,value in [('npc_types','race','99'),('object','type','99'),('spawn2','pathgrid','1')]:
            bad=copy.deepcopy(after);bad['rows'][table][0][field]=value
            with self.assertRaises(ValueError):content.patch_sql(before,bad)
        bad=copy.deepcopy(after)
        next(s for s in bad['rows']['spawn2'] if s['spawngroupID']=='999237')['x']='0'
        with self.assertRaises(ValueError):content.patch_sql(before,bad)
        for ident in ('8000001','8000002','8000003'):
            bad=copy.deepcopy(after);bad['rows']['zone_state_spawns']=[s for s in bad['rows']['zone_state_spawns'] if s['id']!=ident]
            with self.assertRaises(ValueError):content.patch_sql(before,bad)

    def test_rollback_preserves_fresh_state_and_rejects_static_drift(self):
        before=fixture();after=content.desired(before);current=copy.deepcopy(after)
        current['rows']['zone_state_spawns'][0]['x']='123'
        current['rows']['zone_state_spawns'].append(copy.deepcopy(next(s for s in before['rows']['zone_state_spawns'] if s['id']=='8000000')))
        target=content.rollback_target(before,current,after);content.patch_sql(current,target)
        self.assertEqual(current['rows']['zone_state_spawns'][:-1],target['rows']['zone_state_spawns'])
        for table in content.KEYS:
            if table!='zone_state_spawns':self.assertEqual(before['rows'][table],target['rows'][table])
        current['rows']['npc_types'][0]['name']='changed'
        with self.assertRaises(ValueError):content.rollback_target(before,current,after)

if __name__=='__main__':unittest.main()
