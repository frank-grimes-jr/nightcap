"""Pin the already-tested scoped client publisher to this signed candidate."""
import json
import re
from inventory_release_support import ROOT,HERE,ART


def main():
    receipt=json.loads((ART/'signed/verification.json').read_text())
    assert receipt['release']==2026111202 and receipt['changed_assets']==3
    source=(ROOT/'docs/releases/advanced-loot-bugs-20261106/publish.py').read_text(encoding='utf-8')
    values={'OLD':repr(receipt['previous_channel_sha256']),'NEW':repr(receipt['channel_sha256']),
            'RELEASE':'2026111202','PREVIOUS':'2026111201','PINS':repr(receipt['archive_sha256']),
            'PARTIAL':repr('.inventory-combat-stats-20261112-partial')}
    for key,value in values.items():
        source,count=re.subn(r'^'+key+r' = .*$',key+' = '+value,source,flags=re.MULTILINE);assert count==1,key
    source=source.replace('approved signed loot','approved signed Inventory')
    source=source.split("if __name__ == '__main__':")[0]
    source+="if __name__ == '__main__':\n    raise SystemExit('Paired release: use rollout.py publish-client behind the verified closed gateway')\n"
    destination=HERE/'client';destination.mkdir(exist_ok=True)
    (destination/'publish.py').write_text(source,encoding='utf-8',newline='\n')
    tests=(ROOT/'docs/releases/advanced-loot-bugs-20261106/test_publish.py').read_text(encoding='utf-8')
    tests=tests.replace('equi_petinfowindow.xml','equi_inventory.xml')
    extra='''class PairedEntryPointTests(unittest.TestCase):
    def test_standalone_publication_is_disabled(self):
        import subprocess,sys
        result=subprocess.run([sys.executable,str(Path(__file__).with_name('publish.py')),'--publish'],capture_output=True,text=True)
        self.assertNotEqual(result.returncode,0)
        self.assertIn('use rollout.py publish-client',result.stderr)


'''
    tests=tests.replace("if __name__ == '__main__':",extra+"if __name__ == '__main__':")
    (destination/'test_publish.py').write_text(tests,encoding='utf-8',newline='\n')
    print('Pinned three-asset publisher and recovery tests; no publication')


if __name__=='__main__':main()
