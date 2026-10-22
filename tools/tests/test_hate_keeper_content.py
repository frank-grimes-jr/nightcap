import copy,json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'tools'))
import hate_keeper as patch

class KeeperContent(unittest.TestCase):
    def setUp(self):self.before=json.loads((patch.HERE/'preimages.json').read_text())
    def test_exact_content_scope_and_private_continuity(self):
        after=patch.desired(self.before)
        for table in ('npc_types','spawnentry','spawngroup'):
            self.assertEqual(self.before['rows'][table],after['rows'][table])
        spawn=after['rows']['spawn2'][0]
        self.assertEqual((spawn['id'],spawn['zone'],spawn['x'],spawn['y']),('9100012','ecommons','-346.000000','-1570.000000'))
        changed={k for k,v in spawn.items() if v!=self.before['rows']['spawn2'][0][k]}
        self.assertEqual(changed,set(patch.POSE))
        zone=after['rows']['zone'][0]
        self.assertEqual({k for k,v in zone.items() if v!=self.before['rows']['zone'][0][k]},{'min_status'})
        self.assertEqual(zone['min_level'],'46')
        self.assertEqual(len(after['rows']['nightcap_dungeon_spawns']),1)
        self.assertEqual(after['rows']['nightcap_dungeon_spawns'][0]['spawn_id'],'9100012')
    def test_refuses_drift_and_unowned_saved_state(self):
        for table,field,value in [('zone','min_level','1'),('zone','min_status','0'),('npc_types','lastname','fearplane'),('spawn2','zone','ecommons')]:
            changed=copy.deepcopy(self.before);changed['rows'][table][0][field]=value
            with self.assertRaises(ValueError):patch.desired(changed)
        changed=copy.deepcopy(self.before);changed['rows']['nightcap_dungeon_spawns']=[patch.PRIVATE]
        with self.assertRaises(ValueError):patch.desired(changed)
        for field,value in [('instance_id','1'),('is_corpse','1'),('is_zone','1'),('spawn2_id','7')]:
            changed=copy.deepcopy(self.before)
            row=dict(zone_id='76',instance_id='0',is_corpse='0',is_zone='0',spawn2_id='9100012',spawngroup_id='998812',npc_id='998812')
            row[field]=value;changed['rows']['zone_state_spawns']=[row]
            with self.assertRaises(ValueError):patch.desired(changed)
    def test_successor_contract_is_repeatable(self):
        contract=json.loads((ROOT/'docs/dungeons/runtime-contract.json').read_text())
        self.assertEqual(patch.refresh_contract(copy.deepcopy(contract)),contract)
        self.assertEqual(len(contract['content']),499)
        old=json.loads((ROOT/'docs/dungeons/classic-expansion-20261022/install-rows.json').read_text())
        self.assertEqual(next(r for r in old['spawn2'] if r['id']==9100012)['zone'],'hateplane')

if __name__=='__main__':unittest.main()
