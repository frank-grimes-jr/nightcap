"""Analyze all six prespecified seeds without discarding failed attempts."""
import gzip
import json
from statistics import median

from analyze import HERE,WINS,effective


def main():
    folder=HERE/'reuse-fix'
    rows=json.loads(gzip.decompress((folder/'dreadbone-eye.json.gz').read_bytes()))
    ids=[963204,0,940483,940507]
    seeds=list(range(1115,1121))
    arms={item:sorted((r for r in rows if r['item']==item),key=lambda r:r['seed']) for item in ids}
    assert len(rows)==24
    for arm in arms.values():
        assert [r['seed'] for r in arm]==seeds and all(r['role']=='pet' and r['npc']==71065 and r['pet_roster']==3 and r['aa_spent']==500 for r in arm)
    report={'prespecified_seeds':seeds,'npc':71065,'arms':{},'paired_with_dreadbone':{}}
    for item,arm in arms.items():
        report['arms'][item]={
            'outcomes_by_seed':[r['result'] for r in arm],
            'elapsed_seconds_by_seed':[r['ms']/1000 for r in arm],
            'final_sampled_owner_hp_by_seed':[r['final_hp'] for r in arm],
            'lowest_sampled_owner_hp_by_seed':[r['min_sample_hp'] for r in arm],
            'effective_hp_per_second_by_seed':[round(effective(r),3) for r in arm],
            'median_effective_hp_per_second_all_attempts':round(median(effective(r) for r in arm),3),
            'wins':sum(r['result'] in WINS for r in arm)}
        if item==963204:continue
        dread=arms[963204]
        both=[(a,b) for a,b in zip(dread,arm) if a['result'] in WINS and b['result'] in WINS]
        report['paired_with_dreadbone'][item]={
            'jointly_winning_seeds':[a['seed'] for a,b in both],
            'dreadbone_median_joint_win_s':median(a['ms']/1000 for a,b in both) if both else None,
            'control_median_joint_win_s':median(b['ms']/1000 for a,b in both) if both else None,
            'all_attempt_median_hps_delta_pct':round(100*(median(effective(a) for a in dread)/median(effective(b) for b in arm)-1),3)}
    (folder/'dreadbone-eye-summary.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report['paired_with_dreadbone']))


if __name__=='__main__':main()
