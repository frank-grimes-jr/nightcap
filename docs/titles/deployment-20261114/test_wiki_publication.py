"""A stale runtime receipt must not permit a disabled title announcement."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace as NS
import unittest

spec=importlib.util.spec_from_file_location('title_publication',Path(__file__).with_name('wiki_publish.py'))
publication=importlib.util.module_from_spec(spec);spec.loader.exec_module(publication)


class PublicationGate(unittest.TestCase):
    def test_live_control_rechecked_each_time(self):
        enabled=[1];calls=[]
        op=NS(title_state=lambda:calls.append('state'),prior=NS(sql=None),
            title_schema=NS(settings=lambda sql:[dict(id=1,catalog_version=1,enabled=enabled[0])]))
        module=NS(initialize=lambda:op)
        loader=NS(exec_module=lambda mod:None)
        util=NS(spec_from_file_location=lambda name,path:NS(name=name,loader=loader),module_from_spec=lambda spec:module)
        namespace=dict(importlib=NS(util=util),release=Path('/fixture'),sha=lambda p:'pin',TITLE_OPERATOR='pin',
            check_game=lambda:{'image':'unchanged','gateway_open':True})
        exec(publication.TITLE_GUARD,namespace)
        self.assertTrue(namespace['check_game']()['gateway_open'])
        enabled[0]=0
        with self.assertRaises(AssertionError):namespace['check_game']()
        self.assertEqual(calls,['state','state'])


if __name__=='__main__':unittest.main()
