"""Collect the scoped measurements and source hashes. Run on the host after completion."""
import gzip
import json
from pathlib import Path
import subprocess

from prepare import R, SERVER

HERE=Path(__file__).resolve().parent
SCRIPT="""from pathlib import Path
import json,sys
d=Path(sys.argv[1]); out=[]
for f in sorted(d.glob('*rows-*.jsonl')):
    if f.name.startswith('base-'):continue
    for line in f.read_text().splitlines():
        row=json.loads(line)
        row['prepared']=f.name.startswith('prepared-')
        row['variant']='bounded48' if 'final-' in f.name else 'flat40/48' if 'large-' in f.name else 'flat8/12'
        out.append(row)
print(json.dumps(out,separators=(',',':')))
"""

if __name__=="__main__":
    rows=subprocess.check_output(["docker","exec",SERVER,"python3","-c",SCRIPT,R])
    assert len(json.loads(rows))>0
    for prepared,name in ((True,"measurements.json.gz"),(False,"unprepared-pilot.json.gz")):
        cohort=[r for r in json.loads(rows) if r["prepared"]==prepared]
        (HERE/name).write_bytes(gzip.compress(json.dumps(cohort,separators=(",",":")).encode(),mtime=0))
    for source,destination in (("measured-build.json","diagnostic-build.json"),("build.json","final-replay-build.json"),
                               ("replay.json","final-replay.json"),("holdout.json","holdout.json")):
        subprocess.run(["docker","cp",SERVER+":"+R+"/"+source,str(HERE/destination)],check=True)
