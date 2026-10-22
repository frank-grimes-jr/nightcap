"""Promote this release's player notices only after a verified live receipt."""
import html,json,re
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
NAMES={'blackburrow':'Blackburrow','crushbone':'Crushbone','runnyeye':'Runnyeye',
       'soldunga':"Solusek's Eye",'guktop':'Upper Guk','gukbottom':'Lower Guk',
       'mistmoore':'Mistmoore','kedge':'Kedge Keep','paw':'Splitpaw','hole':'The Hole',
       'qcat':'Qeynos Catacombs','fearplane':'Plane of Fear','hateplane':'Plane of Hate','airplane':'Plane of Sky'}
def main():
    receipt=json.loads((HERE/'live-verification.json').read_text())
    assert receipt['gateway_open'] and receipt['checks']=={'schema':39,'content':497}
    for name in ('dungeon-modes','equipment','features','index','recent-changes','travel','unreleased'):
        path=ROOT/'wiki/articles'/(name+'.json');article=json.loads(path.read_text(encoding='utf-8'));body=article['body']
        def notice(match):
            value=match[0]
            if '#unique-rewards' not in value and '#classic-candidate' not in value:return value
            return (value.replace('Not released:','Live testing:').replace('Classic raid reward candidate','Classic raid rewards')
                .replace('all 414 dungeon rewards become MAGIC','all 414 dungeon rewards are MAGIC')
                .replace('Classic raid rewards</a> gives','Classic raid rewards</a> give')
                .replace('The original seven retain their live-testing status; broader gameplay and balance checks are pending.','All 21 are installed for live testing; gameplay and balance acceptance remain pending.'))
        body=re.sub(r'<p\b[^>]*>.*?</p>',notice,body,flags=re.S)
        body=body.replace('available from all seven entrance Keepers','available from all 21 entrance Keepers')
        body=body.replace('each of the seven released dungeons','each of the 21 released dungeons')
        body=body.replace('Raid or Grind in seven private dungeons','Raid or Grind in all 21 Classic dungeons')
        body=body.replace('All seven dungeons in both modes need in-game checks.','All 21 dungeons in both modes need in-game checks.')
        body=body.replace('Instance Keepers offer Befallen, Unrest, High Keep, Najena, Cazic-Thule, Permafrost, and Nagafen’s Lair.',
            'Instance Keepers offer all 21 Classic combat dungeons, including Fear, Hate and Sky.')
        body=body.replace('October 22 — every Classic dungeon candidate','October 22 — every Classic dungeon and unique rewards live')
        body=body.replace('The candidate also repairs stale dungeon item checks behind the reported Keeper error. This repair, the new dungeon coverage and permanent Sky key services require a paired release; none is live yet.',
             'The paired release also repairs stale dungeon item checks behind the reported Keeper error and installs durable Sky key services. Existing runs, earned rewards and the latest quest-tier and client updates are preserved. Native gameplay and balance acceptance remain open.')
        if name=='dungeon-modes':
            body=body.replace('Not released — every Classic dungeon:','Live testing — every Classic dungeon:')
            body=body.replace('A candidate extends Raid, Grind, Enter, Join, Status, Claim Rewards and Reset','The installed release extends Raid, Grind, Enter, Join, Status, Claim Rewards and Reset')
            body=body.replace('The seven live dungeons below retain their current release status.','All 21 dungeons and their new rewards are installed for testing.')
            body=body.replace('Every Classic dungeon candidate','Every Classic dungeon — live testing').replace('<strong>Not released.</strong> Added zones:','<strong>Live testing.</strong> Added zones:')
            body=body.replace('All dungeon rewards become MAGIC','All dungeon rewards are MAGIC')
            body=body.replace('Unique Classic raid rewards — candidate','Unique Classic raid rewards — live testing')
            body=body.replace('available from all seven entrance Keepers','available from all 21 entrance Keepers')
            body=body.replace('Raid and Grind choices are available in Befallen, Unrest, High Keep, Najena, Cazic-Thule, Permafrost and Nagafen’s Lair.',
                'Raid and Grind choices are available in all 21 Classic combat dungeons listed here, including Fear, Hate and Sky.')
            placements=json.loads((HERE.parent.parent/'classic-expansion-20261022/placements.json').read_text())
            rows=''.join('<tr><td>'+html.escape(NAMES[z])+'</td><td><code>'+','.join(str(p['selected']['pose'][key]) for key in ('y','x','z'))+'</code></td></tr>' for z,p in placements.items())
            table='<h2 id="added-keepers">Additional entrance Keepers</h2><p>Use <code>/target Instance_Keeper</code> and hail if its eye model is difficult to select. Locations use in-game <code>/loc</code> order. Each Keeper has Raid, Grind, Enter, Join, Status, Claim Rewards and Reset.</p><table><thead><tr><th>Dungeon</th><th>Keeper /loc</th></tr></thead><tbody>'+rows+'</tbody></table>'
            catalog=json.loads((ROOT/'docs/dungeons/catalog.json').read_text())['dungeons']
            bosses='<h2 id="added-objectives">Required bosses in the added dungeons</h2><p>Every listed boss requires personal credit. Raid unlocks the final boss after all required minibosses; Keeper Status is the live checklist.</p>'
            for d in catalog[7:]:
                bosses+='<h3>'+html.escape(NAMES[d['zone']])+'</h3><ul>'+''.join('<li>'+html.escape(b['name'])+(' — final boss' if b['is_final'] else '')+'</li>' for b in d['bosses'])+'</ul>'
            assert 'id="added-keepers"' not in body and 'id="added-objectives"' not in body
            body=body.replace('<h2 id="unique-rewards">',table+bosses+'<h2 id="unique-rewards">',1)
            body=body.replace('Every dungeon uses these designs at its equipment band:','Every dungeon uses these designs at its equipment band. Original dungeons:')
            article['summary']='Raid and Grind choices, Keepers, objectives and unique MAGIC rewards across 21 Classic dungeons, including Fear, Hate and Sky.'
        assert body!=article['body'],name
        article['body']=body;article['updated']='2026-10-22'
        article['sources'].append('docs/dungeons/classic-rewards-20261022/deployment/: paired21-zone/414-MAGIC release verified; owner gameplay and balance QA open')
        path.write_text(json.dumps(article,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Updated seven dungeon guides after verified deployment.')
if __name__=='__main__':main()
