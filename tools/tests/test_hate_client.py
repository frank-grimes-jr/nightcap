import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import hate_client


class HateClient(unittest.TestCase):
    def test_actor_closure_and_source_drift(self):
        # Synthetic archives isolate the importer; the pinned real archives are
        # independently validated in client-validation.json before packaging.
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory)
            raw={'hateplane_chr.s3d':b'old','hateplaneb_chr.s3d':b'new',
                 'hateplaneb_chr.txt':b'2\nrat,wrong_archive\ngob,goblin\n'}
            for name,data in raw.items():(root/name).write_bytes(data)
            plan=root/'plan.json'
            spec={'sources':{k:hashlib.sha256(v).hexdigest() for k,v in raw.items()},'imports':['inn','rat']}
            plan.write_text(json.dumps(spec))
            def read(data):return {'hateplane_chr.wld':data,'hateplaneb_chr.wld':data}
            def actors(data):return ['INN_ACTORDEF','RAT_ACTORDEF','ZOM_ACTORDEF'] if data==b'old' else ['ZOM_ACTORDEF']
            with patch.object(hate_client,'PLAN',plan),patch.object(hate_client,'read_pfs',read),patch.object(hate_client,'actor_names',actors):
                result=hate_client.files(root)
                self.assertEqual(result['hateplaneb_chr.txt'],b'3\ngob,goblin\ninn,hateplane_chr\nrat,hateplane_chr\n')
                self.assertEqual(result['hateplane_chr.s3d'],b'old')
                (root/'hateplane_chr.s3d').write_bytes(b'drift')
                with self.assertRaisesRegex(ValueError,'Unreviewed Hate client source'):hate_client.files(root)


if __name__=='__main__':unittest.main()
