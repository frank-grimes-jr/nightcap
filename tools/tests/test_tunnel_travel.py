import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import tunnel_travel as travel


def source():
    plan=json.loads((travel.ROOT/'docs/ecommons-hub/plan.json').read_bytes())
    doors=[]
    for d in plan['doors']:
        row={k:str(v) for k,v in d.items() if k!='template_id'}
        row.update(version='0',opentype='58',size='100',dest_instance='0')
        doors.append(row)
    return dict(rows=dict(npc_types=[dict(id='22033',race='1',gender='0',texture='2',helmtexture='0',size='6')],
        spawngroup=[dict(id='999239',name='Existing')],
        spawnentry=[dict(spawngroupID='999239',npcID='999239',chance='100')],
        spawn2=[dict(id='123',spawngroupID='999239')],doors=doors,zone_state_spawns=[]))


class TravelTests(unittest.TestCase):
    def test_replaces_ten_stones_with_three_native_props_and_one_guide(self):
        before=source();after=travel.desired(before)
        self.assertEqual(len(after['rows']['doors']),15)
        props=[d for d in after['rows']['doors'] if int(d['id'])<40610]
        self.assertEqual({p['name'] for p in props},{'HANGLANT','BARREL3','CRATEA'})
        self.assertTrue(all(p['dest_zone']=='NONE' and p['opentype']=='9' for p in props))
        self.assertEqual(after['rows']['npc_types'][-1]['name'],'Merrin')
        self.assertEqual(after['rows']['spawn2'][-1]['pathgrid'],'0')
        self.assertEqual(len(before['rows']['doors']),22,'input is not mutated')

    def test_all_return_and_pok_books_are_byte_for_byte_preserved(self):
        before=source();after=travel.desired(before)
        books=lambda s:[d for d in s['rows']['doors'] if int(d['id'])>=40610]
        self.assertEqual(books(before),books(after))
        for table in ('npc_types','spawngroup','spawnentry','spawn2'):
            self.assertEqual(before['rows'][table][0],after['rows'][table][0])

    def test_geometry_destinations_sizes_and_extra_versions_fail_closed(self):
        for key,value in [('pos_x','-300'),('doorid','123'),('name','OTHER'),('size','50'),
                          ('dest_zone','nexus'),('dest_x','123'),('version','1')]:
            before=source();before['rows']['doors'][0][key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):travel.desired(before)
        before=source();before['rows']['doors'].append(dict(before['rows']['doors'][0],id='50000',version='1'))
        with self.assertRaises(ValueError):travel.desired(before)

    def test_reserved_identity_and_shared_template_rejected(self):
        for table,row in [('npc_types',dict(id='999810')),('spawnentry',dict(spawngroupID='7',npcID='999810')),
                          ('spawn2',dict(id='999810',spawngroupID='7')),('spawngroup',dict(id='999810'))]:
            before=source();before['rows'][table].append(row)
            with self.subTest(table=table),self.assertRaises(ValueError):travel.desired(before)

    def test_runtime_rollback_removes_only_unambiguous_new_guide_state(self):
        original=source();expected=travel.desired(original);current=copy.deepcopy(expected)
        row=dict(id='77',npc_id='999810',spawngroup_id='999810',spawn2_id='999810',zone_id='22',
                 instance_id='0',is_corpse='0',is_zone='0')
        current['rows']['zone_state_spawns']=[row]
        self.assertEqual(travel.rollback_target(original,current,expected),original)
        for field,value in [('npc_id','123'),('spawn2_id','123'),('spawngroup_id','123'),
                            ('instance_id','1'),('is_corpse','1')]:
            changed=copy.deepcopy(current);changed['rows']['zone_state_spawns'][0][field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):travel.rollback_target(original,changed,expected)
        current['rows']['doors'][0]['name']='Changed'
        with self.assertRaises(ValueError):travel.rollback_target(original,current,expected)

    def test_committed_route_catalog_is_generated_from_approved_landings(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'catalog.pl';travel.write_catalog(path)
            self.assertEqual(path.read_bytes(),(travel.ROOT/'server-mods/plugins/tunnel_travel_data.pl').read_bytes())


if __name__=='__main__':unittest.main()
