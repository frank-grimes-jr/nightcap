"""Transmit the exact local operator and reload source through SSH stdin."""
import ast
import subprocess
from pathlib import Path

root = Path(__file__).resolve().parent
payload = 'RELOAD_SOURCE=' + repr((root/'reload_rules.py').read_text()) + '\n' + (root/'apply.py').read_text()
ast.parse(payload)
result = subprocess.run(['ssh','-i','C:/Users/verre/.ssh/nightcap_ovh',
    '-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes',
    'ubuntu@135.148.47.202','sudo -n python3 -'],input=payload,
    text=True,capture_output=True)
if result.returncode:
    raise RuntimeError(result.stderr)
(root.parent/'result.json').write_text(result.stdout)
print(result.stdout)
