"""Synthetic item-cache checks for exclusive identity and effective native fields."""
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch
import rollout

LAYOUT = dict(size=32,ID=0,LoreGroup=4,LoreFlag=8,Slots=12,AugType=16,ReqLevel=20,NoPet=21)

def file(path, rows):
    slots, count = 32, len(rows)
    data = bytearray(20+4*slots+32*count)
    struct.pack_into('<IIII',data,0,len(data)-8,slots,count,count)
    for i in range(slots):
        struct.pack_into('<I',data,16+4*i,0xffffffff)
    for i,(item,fields) in enumerate(rows.items()):
        struct.pack_into('<I',data,16+4*item,i)
        pos=16+4*slots+32*i
        struct.pack_into('<IiBxxxIIBB',data,pos,item,*fields)
    path.write_bytes(data)

class CacheTests(unittest.TestCase):
    def test_only_new_chest_trophies_can_change(self):
        stock=(0,0,0,0,0,0)
        good=(-1,1,131072,2097152,50,1)
        with tempfile.TemporaryDirectory() as tmp, patch.object(rollout,'IDS',{4,5}):
            before,after=Path(tmp)/'before',Path(tmp)/'after'
            file(before,{1:stock})
            file(after,{5:good,1:stock,4:good})
            self.assertEqual(rollout.cache_compare(before,after,LAYOUT)['original_items'],1)
            for rows in ({1:stock,4:good},{1:stock,4:good,7:good},{1:good,4:good,5:good},
                         {1:stock,4:good,5:(0,1,131072,2097152,50,1)},
                         {1:stock,4:good,5:(-1,1,131072,2097152,50,0)}):
                file(after,rows)
                with self.assertRaises(AssertionError):
                    rollout.cache_compare(before,after,LAYOUT)

    def test_existing_name_blocks_before_any_install(self):
        with patch.object(rollout,'m',{'names':['Frostbound Pearl']},create=True), patch.object(rollout,'sql',side_effect=['0','33961\tDeepwater Pearl\t11\n963000\tFrostbound Pearl\t54']) as db:
            with self.assertRaisesRegex(AssertionError,'name'):
                rollout.install('peq')
            self.assertEqual(db.call_count,2)

    def test_occupied_range_refuses_preflight(self):
        import types
        game={'running':True,'oom_killed':False,'image_id':'base','health':'healthy'}
        with tempfile.TemporaryDirectory() as t, patch.object(rollout,'EVIDENCE',Path(t)/'absent'), \
             patch.object(rollout,'a',types.SimpleNamespace(prior=types.SimpleNamespace(players=lambda:0)),create=True), \
             patch.object(rollout,'r',types.SimpleNamespace(compact=lambda name:game),create=True), \
             patch.object(rollout,'m',{'base_image_id':'base'},create=True), patch.object(rollout,'count',return_value=1):
            with self.assertRaises(AssertionError): rollout.preflight()

if __name__=='__main__': unittest.main()
