"""Install the reviewed local wiki source update, without publishing it."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
UPDATE=ROOT/'docs/dungeons/wiki-update'
TARGET=Path('C:/Users/verre/.codex/worktrees/nightcap-wiki/EQ_Local_Dev/wiki')
preimages=json.loads((UPDATE/'preimages.json').read_text())
for relative,expected in preimages.items():
    target=(TARGET/relative).resolve()
    assert target.is_relative_to(TARGET.resolve())
    actual=hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
    after=hashlib.sha256((UPDATE/relative).read_bytes()).hexdigest()
    assert actual in (expected,after),'Wiki source changed: '+relative
for relative in preimages:
    target=TARGET/relative;target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes((UPDATE/relative).read_bytes())
receipt=dict(status='local_source_updated_not_published',
    target=str(TARGET),files={relative:hashlib.sha256((TARGET/relative).read_bytes()).hexdigest() for relative in preimages})
(UPDATE/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Installed the six reviewed local wiki source files; no website publication.')
