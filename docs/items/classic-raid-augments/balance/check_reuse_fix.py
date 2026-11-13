"""Compare the corrected cooldown cohort with its exact before-fix control rows."""
import csv
import gzip
import json
from pathlib import Path
import sys

from analyze import HERE,aggregate


def main():
    output=HERE/'reuse-fix'
    output.mkdir(exist_ok=True)
    path=output/'measurements.json.gz'
    if len(sys.argv)>1:
        rows=[json.loads(line) for f in sorted(Path(sys.argv[1]).glob('post-*-measured.jsonl')) for line in f.read_text().splitlines()]
    else:
        rows=json.loads(gzip.decompress(path.read_bytes()))
    before=json.loads(gzip.decompress((HERE/'measurements.json.gz').read_bytes()))
    key=lambda r:(r['role'],r['npc'],r['item'],r['seed'])
    existing={key(r):r for r in before}
    assert len(rows)==len({key(r) for r in rows})==150
    assert all(key(r) in existing for r in rows)
    controls=[r for r in rows if r['item']<963200]
    for r in controls:
        for field in ['result','ms','base_hp','base_mana','aa_spent','min_sample_hp','final_boss_hp','raid']:
            assert existing[key(r)][field]==r[field], (key(r),field)
    arms=[r for r in rows if r['item']>=963200]
    def gaps(r):
        activations=[e for e in r['raid']['events'] if e[1]!=0]
        return [b[0]-a[0] for a,b in zip(activations,activations[1:])]
    pre=[n for r in arms for n in gaps(existing[key(r)])]
    post=[n for r in arms for n in gaps(r)]
    assert min(pre)<90000<=min(post)
    summary=aggregate(rows)
    assert len(summary)==15
    with (output/'comparisons.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(summary[0]));writer.writeheader();writer.writerows(summary)
    receipt={'executions':len(rows),'unchanged_hunt_and_empty_controls':len(controls),'paired_capstone_fights':len(arms),
        'before_minimum_observed_activation_gap_ms':min(pre),'after_minimum_observed_activation_gap_ms':min(post),
        'before_sub_90s_activation_pairs':sum(n<90000 for n in pre),'after_sub_90s_activation_pairs':sum(n<90000 for n in post),
        'before_measured_activation_pairs':len(pre),'after_measured_activation_pairs':len(post),
        'changed_capstone_outcomes':sum(existing[key(r)]['result']!=r['result'] for r in arms),
        'changed_capstone_end_times':sum(existing[key(r)]['ms']!=r['ms'] for r in arms),
        'kill_flags':sum(x['kill_flag'] for x in summary),'healing_flags':sum(x['heal_flag'] for x in summary)}
    if len(sys.argv)>1:
        path.write_bytes(gzip.compress(json.dumps(sorted(rows,key=key),separators=(',',':')).encode(),mtime=0))
    (output/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt))


if __name__=='__main__':main()
