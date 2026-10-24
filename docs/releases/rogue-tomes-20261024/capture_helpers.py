"""Read the exact retained helper source for independent review, without execution."""
import base64,json
from pathlib import Path
paths={'state':'/opt/nightcap/releases/classic-dungeons-rewards-20261022/rollout.py'}
print(json.dumps({k:base64.b64encode(Path(p).read_bytes()).decode() for k,p in paths.items()}))
