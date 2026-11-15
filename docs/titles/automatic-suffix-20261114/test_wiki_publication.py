"""Do not publish title availability from stale runtime or disabled catalog proof."""
from pathlib import Path
from types import SimpleNamespace as NS
import unittest
import wiki_publish as publication


class PublicationGate(unittest.TestCase):
    def namespace(self):
        runtime=dict(started_at='generation',restart_count=0,errors={},processes=[('zone',)]*12)
        enabled=[1]
        op=NS(title_state=lambda:None,r=NS(running=lambda image,bins:runtime),prior=NS(sql=None),
            title_schema=NS(settings=lambda sql:[dict(id=1,catalog_version=1,enabled=enabled[0])]))
        module=NS(initialize=lambda:op)
        loader=NS(exec_module=lambda m:None)
        util=NS(spec_from_file_location=lambda name,path:NS(name=name,loader=loader),module_from_spec=lambda s:module)
        namespace=dict(importlib=NS(util=util),release=Path('/releases/successor'),sha=lambda p:'pin',TITLE_OPERATOR='pin',
            RUNTIME_BINARIES={'zone':'pin'},RUNTIME_STARTED='generation',check_game=lambda:{'image':'image','gateway_open':True})
        exec(publication.TITLE_GUARD,namespace)
        return namespace,runtime,enabled

    def test_current_runtime_passes(self):
        ns,_,_=self.namespace();self.assertTrue(ns['check_game']()['gateway_open'])

    def test_same_image_restart_or_different_generation_blocks(self):
        for change in [dict(restart_count=1),dict(started_at='later')]:
            with self.subTest(change=change):
                ns,runtime,_=self.namespace();runtime.update(change)
                with self.assertRaises(AssertionError):ns['check_game']()

    def test_missing_worker_or_native_error_blocks(self):
        for change in [dict(processes=[('zone',)]*11),dict(errors={'native':1})]:
            with self.subTest(change=change):
                ns,runtime,_=self.namespace();runtime.update(change)
                with self.assertRaises(AssertionError):ns['check_game']()

    def test_live_catalog_rechecked(self):
        ns,_,enabled=self.namespace();ns['check_game']();enabled[0]=0
        with self.assertRaises(AssertionError):ns['check_game']()


if __name__=='__main__':unittest.main()
