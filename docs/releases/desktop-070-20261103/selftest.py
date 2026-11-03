"""Exercise publish.py against a temporary public folder (run beside the stage files)."""
import os
import shutil
import sys
import tempfile
from pathlib import Path

stage = Path(sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, str(Path(__file__).resolve().parent))
import publish as p

root = Path(tempfile.mkdtemp())
pub = root / 'public'
(pub / 'launcher').mkdir(parents=True)
shutil.copy(stage / 'previous-launcher-channel.json', pub / 'launcher-channel.json')
(pub / 'channel.json').write_text('game')
(pub / 'guide.html').write_text('g')
try:
    p.publish(stage, pub, 'switch')
    raise SystemExit('switch before exe was allowed')
except RuntimeError as e:
    assert 'Upload the desktop' in str(e)
assert p.publish(stage, pub, 'exe')['launcher_channel_sha256'] == p.OLD
p.publish(stage, pub, 'exe')
assert p.publish(stage, pub, 'switch')['launcher_channel_sha256'] == p.NEW
p.publish(stage, pub, 'switch')
(pub / 'launcher-channel.json').write_text('{}')
try:
    p.publish(stage, pub, 'switch')
    raise SystemExit('drifted channel accepted')
except RuntimeError as e:
    assert 'drift' in str(e)
shutil.rmtree(root)
print('selftest ok')
