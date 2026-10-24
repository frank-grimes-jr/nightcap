import json
import gzip
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import loot_capture
import loot_refresh


def fixture(time='2026-10-23T00:00:00+00:00'):
    return {'schema':1,'captured_at':time,'items':[{'id':1}]},{'1':{'id':1,'name':'Sword'}}


class CaptureContractTests(unittest.TestCase):
    def test_queries_are_read_only_and_allowlisted(self):
        sql=loot_capture.statements('default')
        self.assertIn('WITH CONSISTENT SNAPSHOT, READ ONLY',sql)
        self.assertTrue(sql.endswith('ROLLBACK;'))
        for forbidden in ['character_data','account','password','SELECT *','UPDATE ','DELETE ','INSERT ','CREATE ','ALTER ']:
            self.assertNotIn(forbidden,sql)
        self.assertNotIn('comment',loot_capture.FIELDS['items'][1].split())
        self.assertNotIn('source',loot_capture.FIELDS['items'][1].split())
        self.assertIn('STRAIGHT_JOIN',sql)

    def test_configuration_cannot_inject_sql(self):
        for value in ["default'; DROP TABLE items;--",'',None,'default name']:
            with self.assertRaises((TypeError,ValueError)):loot_capture.statements(value)


@unittest.skipUnless(os.name=='posix','Atomic symlink recovery is verified on Linux')
class PublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)/'public';self.addCleanup(self.tmp.cleanup)

    def test_immutable_details_and_current_are_paired(self):
        first=loot_refresh.publish(self.root,*fixture())
        second=loot_refresh.publish(self.root,*fixture('2026-10-23T00:15:00+00:00'))
        self.assertNotEqual(first['snapshot'],second['snapshot'])
        index=json.loads(loot_refresh.read_payload(self.root/'current/index.json'))
        self.assertIn(second['snapshot'],index['base_url'])
        self.assertTrue((self.root/first['snapshot']/'item-1.json.gz').is_file())
        self.assertFalse((self.root/first['snapshot']/'item-1.json').exists())
        self.assertEqual((self.root/'current').readlink(),Path(second['snapshot']))
        self.assertEqual((self.root/second['snapshot']).stat().st_mode & 0o777,0o755)

    def test_failed_pointer_switch_preserves_previous(self):
        first=loot_refresh.publish(self.root,*fixture())
        with patch.object(loot_refresh.os,'replace',side_effect=OSError('disk unavailable')):
            with self.assertRaises(OSError):loot_refresh.publish(self.root,*fixture('2026-10-23T00:15:00+00:00'))
        self.assertEqual((self.root/'current').readlink(),Path(first['snapshot']))
        self.assertFalse((self.root/'.current-next').exists())

    def test_incomplete_snapshot_does_not_replace_current(self):
        first=loot_refresh.publish(self.root,*fixture())
        index,_=fixture()
        with self.assertRaises(ValueError):loot_refresh.publish(self.root,index,{})
        self.assertEqual((self.root/'current').readlink(),Path(first['snapshot']))

    def test_killed_process_pointer_is_recovered(self):
        first=loot_refresh.publish(self.root,*fixture())
        (self.root/'.current-next').symlink_to(first['snapshot'])
        second=loot_refresh.publish(self.root,*fixture('2026-10-23T00:15:00+00:00'))
        self.assertEqual((self.root/'current').readlink(),Path(second['snapshot']))
        (self.root/'.current-next').symlink_to('../private')
        with self.assertRaises(ValueError):loot_refresh.publish(self.root,*fixture('2026-10-23T00:30:00+00:00'))

    def test_unsafe_current_and_root_symlinks_fail(self):
        self.root.mkdir();(self.root/'current').symlink_to('../outside')
        with self.assertRaises(ValueError):loot_refresh.publish(self.root,*fixture())
        other=Path(self.tmp.name)/'other';other.symlink_to(self.root,target_is_directory=True)
        with self.assertRaises(ValueError):loot_refresh.publish(other,*fixture())

    def test_changed_immutable_payload_fails(self):
        first=loot_refresh.publish(self.root,*fixture())
        (self.root/first['snapshot']/'item-1.json.gz').write_bytes(gzip.compress(b'changed'))
        with self.assertRaises(ValueError):loot_refresh.publish(self.root,*fixture())

    def test_retention_preserves_unrelated_paths(self):
        self.root.mkdir();protected=self.root/'operator-notes';protected.mkdir();(protected/'keep').write_text('retain')
        for minute in range(4):loot_refresh.publish(self.root,*fixture(f'2026-10-23T00:0{minute}:00+00:00'),retain=2)
        self.assertTrue((protected/'keep').is_file())
        self.assertEqual(len([p for p in self.root.iterdir() if len(p.name)==16]),2)

    def test_low_disk_space_preserves_previous_snapshot(self):
        first=loot_refresh.publish(self.root,*fixture())
        with patch.object(loot_refresh.shutil,'disk_usage',return_value=type('Space',(),{'free':1})()):
            with self.assertRaisesRegex(OSError,'disk headroom'):
                loot_refresh.publish(self.root,*fixture('2026-10-23T00:15:00+00:00'))
        self.assertEqual((self.root/'current').readlink(),Path(first['snapshot']))
        self.assertTrue(loot_refresh.read_payload(self.root/'current/index.json'))


if __name__=='__main__': unittest.main()
