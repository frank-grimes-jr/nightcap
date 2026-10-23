"""Bounded SSH runner for this explicitly authorized deployment."""
import argparse,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
SSH=['C:/Windows/System32/OpenSSH/ssh.exe','-i','C:/Users/verre/.ssh/nightcap_ovh','-o','BatchMode=yes','-o','ConnectTimeout=10','-o','StrictHostKeyChecking=yes','ubuntu@135.148.47.202']
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('script');p.add_argument('--output');a=p.parse_args()
 result=subprocess.run(SSH+['sudo -n python3 -'],input=Path(a.script).read_text(encoding='utf-8'),text=True,capture_output=True,timeout=1800)
 if result.returncode:raise RuntimeError(result.stderr[-5000:])
 if a.output:
  data=json.loads(result.stdout);Path(a.output).write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
  print(json.dumps({k:data[k] for k in ('captured_at','disk_free','memory_available_kib','health','startup_guards','saved_chapterhouse_counts','chapterhouse_instances','existing_vigil_tables') if k in data}))
 else:print(result.stdout[-6000:])
