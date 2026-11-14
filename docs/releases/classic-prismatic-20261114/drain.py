"""Run the reviewed activation with an occupied-world gateway drain."""
import hashlib
from pathlib import Path
import sys

stage=Path(__file__).resolve().parent
path=stage/'release.py'
raw=path.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='415c721bcba16e3fcf3e1ca965e4c2da17a3bcdbcd1c32d62d8c5281ce87e681'
source=raw.decode()
old="    assert a.prior.players()==0\n    folder=EVIDENCE/'activation'"
new="    connected_before=a.prior.players()\n    folder=EVIDENCE/'activation'"
wait="        time.sleep(125)\n        assert a.prior.players()==0"
drain="""        assert not r.compact('gateway')['running']
        p.save(folder/'drain.json',{'connected_before':connected_before,'source':m['source']})
        deadline=time.monotonic()+300
        time.sleep(125)
        while a.prior.players():
            assert time.monotonic()<deadline,'Connected character has not finished saving'
            time.sleep(5)"""
assert source.count(old)==source.count(wait)==1
assert sys.argv[1:]==['activate']
exec(compile(source.replace(old,new).replace(wait,drain),str(path),'exec'),{'__name__':'__main__','__file__':str(path)})
