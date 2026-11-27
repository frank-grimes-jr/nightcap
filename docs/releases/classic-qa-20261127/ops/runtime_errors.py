"""Count boot/runtime errors for this container generation without exporting player logs."""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess

from capture import SSH

PATTERNS = {'native':r'Segmentation fault|core dumped|a native process exited',
            'quest':r"Can't locate object method|Undefined subroutine|Perl runtime error|Lua runtime error|Lua syntax error",
            'database':r'Unknown column|SQL syntax'}


def main(target):
    game='akk-stack-eqemu-server-1' if target=='local' else 'nightcap-production-game-1'
    # Filter where the logs live. Only the generation, count and error counters leave the host.
    script = """
import json, re, subprocess, sys
name=sys.argv[1]
state=json.loads(subprocess.check_output(['docker','inspect',name]))[0]
start=state['State']['StartedAt']
logs=subprocess.check_output(['docker','logs','--since',start,name],stderr=subprocess.STDOUT)
patterns=json.loads(sys.argv[2])
counts={key:len(re.findall(pattern.encode(),logs,re.I)) for key,pattern in patterns.items()}
print(json.dumps({'started_at':start,'image':state['Image'],'health':state['State']['Health']['Status'],'restarts':state['RestartCount'],'errors':counts}))
"""
    args=['python3' if target=='production' else 'python','-c',script,game,json.dumps(PATTERNS)]
    if target=='production':
        args=[*SSH,shlex.join(['sudo','-n',*args])]
    result=json.loads(subprocess.check_output(args))
    print(json.dumps(result))
    assert result['health']=='healthy' and result['restarts']==0 and not any(result['errors'].values())
    out=Path(__file__).resolve().parent/(target+'-errors.json')
    out.write_text(json.dumps(result,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('target',choices=('local','production'))
    main(parser.parse_args().target)

