import copy
import math
from pathlib import Path
import re
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tunnel_social as social
from tunnel_courts import appearance, class_members
from tunnel_social_layout import CLASS_GROUPS, MERCHANT_NAMES, RING, RING_CENTER, SUPPLIES, STATIONS, TRADERS, placements, paths

def fixture():
    rows={t:[] for t in social.KEYS}
    for ident in sorted(social.IDS):
        group=ident if ident>=990000 else ident+100000
        spawn=ident if ident>=990000 else ident+200000
        cls=ident-999649+19 if 999650<=ident<=999665 else 41
        npc={k:str(v) for k,v in appearance((1,3,0xABCDEF,6),ident%2).items()}
        npc.update(id=str(ident),name='Existing_'+str(ident),lastname='Retained role',
                   **{'class':str(cls)},merchant_id=str(ident),hp='12345',AC='77',loottable_id='0')
        if ident in MERCHANT_NAMES:
            npc.update(name=social.ORIGINAL_MERCHANT_NAMES[ident],merchant_id=str(99300+ident-997900))
        rows['npc_types'].append(npc)
        rows['spawngroup'].append(dict(id=str(group),name='Group'+str(group)))
        rows['spawnentry'].append(dict(spawngroupID=str(group),npcID=str(ident),chance='100'))
        rows['spawn2'].append(dict(id=str(spawn),spawngroupID=str(group),zone='ecommons',version='0',
            pathgrid=str(ident if ident in paths() else 0),x='-1506.000000',y='-185.000000',z='2.000000',heading='128.000000'))
    for ident,route in paths().items():
        rows['grid'].append(dict(id=str(ident),zoneid='22',type='3',type2='1'))
        for j in range(1,5):rows['grid_entries'].append(dict(gridid=str(ident),zoneid='22',number=str(j),
            x='-200',y='-1600',z='3.75',heading='128',pause='20',centerpoint='0'))
    for ident,(label,*_) in STATIONS.items():
        rows['object'].append(dict(id=str(ident),zoneid='22',display_name=label,type=str(ident-999580),
            objectname='RETAINED_ACTOR',xpos='-300',ypos='-1800',zpos='0',heading='128'))
    for ident in (999220,999520,22089):
        rows['zone_state_spawns'].append(dict(id=str(ident),npc_id=str(ident),
            spawngroup_id=str(ident if ident>=990000 else ident+100000),
            spawn2_id=str(ident if ident>=990000 else ident+200000),
            zone_id='22',instance_id='0',is_corpse='0',is_zone='0'))
    return dict(rows=rows,scopes=social.SCOPES)

class SocialTunnel(unittest.TestCase):
    def test_complete_roster_includes_glorphyndel_native_center_and_all_services(self):
        self.assertEqual(len(social.IDS),119)
        self.assertEqual(set(RING),{999520,999521,999522,999523,999524,999526})
        self.assertTrue({22089,999220,999810,999525,999527}<=social.IDS)
        self.assertEqual(len(TRADERS),16)
        self.assertEqual(len(paths()),8)

    def test_classes_congregate_with_adjacent_counterparts_and_inward_headings(self):
        positions=placements()
        for label,classes,center,points in CLASS_GROUPS:
            area=abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(points,points[1:]+points[:1])))/2
            self.assertGreater(area,350,label+' cannot collapse to a row')
            for cls in classes:
                a,b=(positions[i] for i in class_members()[cls])
                self.assertTrue(12<=math.hypot(a['x']-b['x'],a['y']-b['y'])<=35,label)
            for ident in [i for c in classes for i in class_members()[c]]:
                p=positions[ident];h=p['heading']*math.tau/512
                toward=(center[0]-p['x'],center[1]-p['y'])
                self.assertGreater((math.sin(h)*toward[0]+math.cos(h)*toward[1])/math.hypot(*toward),.99)

    def test_ring_is_irregular_and_faces_the_group(self):
        radii=[math.dist(p,RING_CENTER) for p in RING.values()]
        self.assertGreater(max(radii)-min(radii),5)
        self.assertTrue(all(20<r<35 for r in radii))
        angles=sorted(math.atan2(y-RING_CENTER[1],x-RING_CENTER[0])%math.tau for x,y in RING.values())
        gaps=[(angles[(i+1)%6]-angles[i])%math.tau for i in range(6)]
        self.assertGreater(max(gaps)-min(gaps),.2)

    def test_tradeskill_corner_contains_every_page_and_six_existing_stations(self):
        self.assertEqual(set(SUPPLIES),set(range(999600,999622)))
        for x,y,*_ in SUPPLIES.values():self.assertTrue(-410<=x<=-225 and -1845<=y<=-1710)
        self.assertEqual({s[0] for s in STATIONS.values()},{'Loom','Oven','Forge','Brewing Barrel','Pottery Wheel','Kiln'})
        for _,x,y,_ in STATIONS.values():self.assertTrue(-410<=x<=-225 and -1860<=y<=-1710)

    def test_chronicler_is_next_to_shady_and_traders_are_distributed(self):
        p=placements()[999220]
        self.assertLessEqual(math.dist((p['x'],p['y']),(-141,-1677)),30)
        self.assertGreater(max(p[0] for p in TRADERS.values())-min(p[0] for p in TRADERS.values()),300)
        self.assertGreater(max(p[1] for p in TRADERS.values())-min(p[1] for p in TRADERS.values()),250)

    def test_only_class_merchant_names_change_npc_data(self):
        before=fixture();after=social.desired(before)
        new={n['id']:n for n in after['rows']['npc_types']}
        self.assertEqual(len(set(MERCHANT_NAMES.values())),16)
        for n in before['rows']['npc_types']:
            expected=dict(n)
            if int(n['id']) in MERCHANT_NAMES:expected['name']=MERCHANT_NAMES[int(n['id'])]
            self.assertEqual(new[n['id']],expected)
        self.assertTrue(all(re.fullmatch('[A-Z][a-z]+_[A-Z][a-z]+',n) for n in MERCHANT_NAMES.values()))

    def test_station_models_types_and_spawn_functions_preserved(self):
        before=fixture();after=social.desired(before)
        for table in ('object','spawn2','grid_entries'):
            for old,new in zip(before['rows'][table],after['rows'][table]):
                changed={k for k in old if old[k]!=new[k]}
                self.assertLessEqual(changed,social.FIELDS[table])
        self.assertEqual(before['rows']['spawnentry'],after['rows']['spawnentry'])
        self.assertEqual(before['rows']['spawngroup'],after['rows']['spawngroup'])

    def test_walking_routes_use_distinct_pauses_and_native_random_half_mode(self):
        after=social.desired(fixture())
        self.assertTrue(all(g['type']=='3' and g['type2']=='0' for g in after['rows']['grid']))
        self.assertGreater(len({p['pause'] for p in after['rows']['grid_entries']}),20)
        self.assertGreater(len({p['heading'] for p in after['rows']['grid_entries']}),20)
        for route in paths().values():self.assertGreater(len(set(p['pause'] for p in route)),1)

    def test_untouched_native_saved_states_survive(self):
        before=fixture();after=social.desired(before)
        self.assertEqual(after['rows']['zone_state_spawns'],[before['rows']['zone_state_spawns'][-1]])

    def test_ambiguous_corpse_instance_and_shared_references_block_changes(self):
        for field,value in [('is_corpse','1'),('is_zone','1'),('zone_id','202'),('instance_id','1'),('npc_id','22089')]:
            before=fixture();before['rows']['zone_state_spawns'][0][field]=value
            with self.assertRaisesRegex(ValueError,'Ambiguous'):social.desired(before)
        before=fixture();before['rows']['spawnentry'].append(dict(before['rows']['spawnentry'][0],npcID='999520'))
        with self.assertRaisesRegex(ValueError,'Shared'):social.desired(before)

    def test_name_collision_and_replay_are_rejected(self):
        before=fixture();before['rows']['npc_types'].append(dict(before['rows']['npc_types'][0],id='12345',name=MERCHANT_NAMES[997900]))
        with self.assertRaisesRegex(ValueError,'collision'):social.desired(before)
        with self.assertRaisesRegex(ValueError,'already installed'):social.desired(social.desired(fixture()))

    def test_merchant_identity_and_stock_link_drift_block_planning(self):
        for field,value in [('name','Someone_Else'),('merchant_id','12345')]:
            before=fixture()
            next(n for n in before['rows']['npc_types'] if n['id']=='997900')[field]=value
            with self.assertRaisesRegex(ValueError,'identity or stock link'):social.desired(before)

    def test_rollback_uses_fresh_caches_without_restoring_stale_positions(self):
        before=fixture();after=social.desired(before);current=copy.deepcopy(after)
        current['rows']['zone_state_spawns'].append(dict(before['rows']['zone_state_spawns'][0],id='8000000'))
        restored=social.rollback_target(before,current,after)
        self.assertEqual(restored['rows']['zone_state_spawns'],after['rows']['zone_state_spawns'])
        for t in social.KEYS:
            if t!='zone_state_spawns':self.assertEqual(restored['rows'][t],before['rows'][t])
        current['rows']['object'][0]['type']='99'
        with self.assertRaisesRegex(ValueError,'drift'):social.rollback_target(before,current,after)

    def test_mutation_budget_refuses_gameplay_or_stock_changes(self):
        before=fixture();after=social.desired(before)
        sql=social.patch_sql(before,after)
        writes=set(re.findall(r'(?:UPDATE|INSERT INTO|DELETE FROM) `(\w+)`',sql))
        self.assertLessEqual(writes,{'npc_types','spawn2','grid','grid_entries','object','zone_state_spawns'})
        for table,field in [('npc_types','class'),('object','type'),('spawn2','pathgrid')]:
            bad=copy.deepcopy(after);bad['rows'][table][0][field]='999'
            with self.assertRaisesRegex(ValueError,'Unapproved'):social.patch_sql(before,bad)
        bad=copy.deepcopy(after);bad['rows']['zone_state_spawns']=[]
        with self.assertRaisesRegex(ValueError,'Untouched'):social.patch_sql(before,bad)

if __name__=='__main__':unittest.main()
