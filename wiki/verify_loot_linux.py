"""Offline Linux verification in existing local Docker images, with networking disabled.

The checkout and captured content are mounted read-only. Tests use the container's
 temporary filesystem. No source or content is sent to a remote machine.
"""
import argparse
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parent.parent
RUNNER = r'''
import gzip,json,pathlib,resource,shutil,subprocess,sys,tempfile
report={}
with tempfile.TemporaryDirectory(prefix='wiki-loot-check-') as temporary:
 root=pathlib.Path(temporary)
 (root/'docs').symlink_to('/source/docs',target_is_directory=True)
 (root/'server-mods').symlink_to('/source/server-mods',target_is_directory=True)
 (root/'tools').symlink_to('/source/tools',target_is_directory=True)
 shutil.copytree('/source/wiki',root/'wiki',ignore=shutil.ignore_patterns('dist','__pycache__','loot-preview'))
 tests=subprocess.run([sys.executable,'-B','-m','unittest','test_loot_model','test_loot_refresh','test_loot_install','test_wiki','test_build_lab','test_deploy','test_update'],cwd=root/'wiki',text=True,capture_output=True,timeout=180)
 report['tests']={'returncode':tests.returncode,'output':(tests.stdout+tests.stderr)[-7000:]}
 if tests.returncode:print(json.dumps(report));sys.exit(1)
 sys.path.insert(0,str(root/'wiki'))
 import verify_loot_native,loot_model,loot_refresh
 report['native']=verify_loot_native.check('/source/server-mods/code/zone/loot.cpp')
 raw=json.loads(gzip.decompress(pathlib.Path('/source/artifacts/wiki-loot/content.json.gz').read_bytes()))
 index,details=loot_model.project(raw)
 public=root/'public';result=loot_refresh.publish(public,index,details)
 root.chmod(0o755)
 check=subprocess.run(['runuser','-u','nobody','--','head','-c','1',str(public/'current/index.json')],capture_output=True)
 report['projection']=result|{'unprivileged_readable':check.returncode==0}
 report['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
 if check.returncode:print(json.dumps(report));sys.exit(1)
print(json.dumps(report))
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--python-image',default='eqemulator/eqemu-server:v16')
    parser.add_argument('--nginx-image',default='akk-stack-peq-editor-proxy:latest')
    args=parser.parse_args()
    command=['docker','run','--rm','--network','none','-i','--user','0','--mount',f'type=bind,source={ROOT},target=/source,readonly','--entrypoint','python3',args.python_image,'-B','-']
    result=subprocess.run(command,input=RUNNER,text=True,capture_output=True,timeout=300)
    report=json.loads(result.stdout) if result.stdout else {'error':result.stderr[-5000:]}
    fragment=(ROOT/'wiki/loot-nginx.conf').read_text()
    config='error_log stderr; pid /tmp/wiki-loot-check.pid; events {} http { server { listen 127.0.0.1:18999; '+fragment+' } }'
    nginx=subprocess.run(['docker','run','--rm','--network','none','-i','--entrypoint','/bin/sh',args.nginx_image,'-c','cat > /tmp/verify-nginx.conf; exec nginx -t -c /tmp/verify-nginx.conf'],input=config,text=True,capture_output=True,timeout=30)
    report['nginx']={'returncode':nginx.returncode,'output':nginx.stdout+nginx.stderr}
    (ROOT/'artifacts/wiki-loot/linux-verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
    if result.returncode or nginx.returncode:raise SystemExit(result.stderr[-5000:] or 1)


if __name__=='__main__':main()
