"""Record verified activation/publication without asserting native acceptance."""
import json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
def replace(path,old,new):
    text=path.read_text(encoding='utf-8');assert old in text,str(path)
    path.write_text(text.replace(old,new,1),encoding='utf-8')
def main():
    deployed=json.loads((HERE/'deployment.json').read_text())
    publication=json.loads((HERE/'wiki-publication.json').read_text())
    public=json.loads((HERE/'wiki-public-verification.json').read_text())
    assert deployed['gateway_open'] and deployed['contract']=={'schema':39,'content':499}
    assert publication['result']==public['result']=='PASS' and public['files']==466
    replace(HERE/'README.md','**Built and tested candidate. Not deployed, merged to main, published or accepted\nin game.** User requested moving the Plane of Hate Keeper to Commonlands after\nthe production audit found the existing service behind Hate\'s GM access gate.\nThe repository\'s main promotion gate still requires owner sign-off.',
        '**Main and production deployment verified; owner gameplay acceptance remains open.**\nThe owner explicitly approved "Push to main and server". PR299 merged as\n`a736fb0`; the paired move is live and gateway access is open. All12 zone workers\nmatch the tested new binary and39 schema/499 content checks pass. A fresh stopped\nbackup and exact player/state/content/cache preservation were verified.\n`deployment.json` is the redacted receipt; private full backup stays on the host.\nWiki `20261022-hate-keeper-v1` verifies all466 public hashes/security headers and\nfive private-route denials. No client update. These checks do not replace the\nowner QA below.')
    replace(HERE/'README.md','1. Obtain owner main/live sign-off; merge the reviewed source through the\n   repository release process. Keep the manual checks below open.',
        '1. Owner main/live sign-off was received and PR299 merged. The steps below\n   describe the completed release; do not blindly replay its immutable stage.\n   Keep the manual checks below open.')
    replace(HERE/'README.md','Wiki candidate is based on the current published Build Lab checkout and retains\nits interactive shell. Seven affected guides/notices are updated; catalog item\nvalues, commands and other dungeon policies are unchanged. Publication pending.',
        'Wiki publication preserves the exact preceding Build Lab release and its\ninteractive shell. Only seven guides plus search changed. All22 guides and432\ngenerated routes were reviewed; catalog values, commands and other dungeon\npolicies remain.16 content/source checks,16 Linux publisher/recovery checks and\nthe real old/new pointer rollback rehearsal pass. Source:\n`E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki`; publication and HTTPS receipts are\nretained alongside this record. Owner gameplay acceptance remains open.')
    replace(ROOT/'CHANGES.md','## 2026-10-22 — Hate Keeper in Commonlands candidate','## 2026-10-22 — Hate Keeper moved to Commonlands')
    replace(ROOT/'CHANGES.md','Native build/tests, exact SQL rehearsal and terrain checks pass. Main/live approval,\nwiki publication and owner gameplay QA remain pending.',
        'Owner-approved PR299 is merged and the paired release is live. All12 zone\nworkers,39 schema/499 content checks and preserved state/cache checks pass.\nWiki466-file publication is verified. Owner gameplay QA remains open.')
    replace(ROOT/'docs/status.md','## 2026-10-22 — Hate Keeper relocation ready for approval','## 2026-10-22 — Hate Keeper relocation deployed')
    replace(ROOT/'docs/status.md','Candidate moves the public Hate Keeper to East Commonlands `/loc -1570,-346,3`,','The public Hate Keeper is now in East Commonlands `/loc -1570,-346,3`,')
    replace(ROOT/'docs/status.md','access. Built and tested against the exact live baseline; production unchanged.\nMain/live sign-off, wiki publication and owner QA remain open.',
        'access. Owner-authorized main PR299 and paired production activation are\nverified: all12 zones,39 schema/499 content checks, fresh stopped backup and\nplayer/state/cache preservation. Gateway open; no client update. Wiki466 files\nverify over HTTPS. Owner in-game visibility/travel/gameplay QA remains open.')
    replace(ROOT/'docs/milestones/phase-72-report.md','# Phase 72 — Hate Keeper in Commonlands candidate','# Phase 72 — Hate Keeper in Commonlands deployed')
    replace(ROOT/'docs/milestones/phase-72-report.md','has a tested cross-zone relocation candidate','has a verified cross-zone relocation')
    replace(ROOT/'docs/milestones/phase-72-report.md','Seven wiki notices are prepared on the\nlatest published Build Lab source; catalog values and commands are unchanged.',
        'Seven wiki notices are published on the\nretained Build Lab source; catalog values and commands are unchanged.')
    replace(ROOT/'docs/milestones/phase-72-report.md','No gameplay deployment, main merge, website publication or native owner QA has\noccurred. The concrete final gate is owner main/live sign-off, including the\naccess-policy correction and brief full runtime restart. Exact activation,\nrecovery boundaries and in-game checks:',
        'The owner approved main/server promotion. PR299 and the paired live release\nare verified with all12 workers and39/499 runtime checks. Fresh backup, saved\nstate and current cache preservation passed before access reopened. Wiki466\nHTTPS hashes/headers and five private denials pass after rollback rehearsal.\nNative owner visibility/travel/gameplay QA remains open. Exact activation,\nrecovery boundaries and in-game checks:')
    verification=json.loads((HERE/'verification.json').read_text())
    verification.update(status='deployed and published; owner native QA open',production_changed=True,
        wiki='16 local content/source checks and16 Linux recovery checks passed;459 pages built;466 public hashes/security headers and five private denials passed')
    verification['review']['live_operator_execution']='approved and completed; private receipt and redacted deployment.json retained'
    (HERE/'verification.json').write_text(json.dumps(verification,indent=2)+'\n')
    wiki_review=json.loads((HERE/'wiki-review.json').read_text())
    wiki_review.update(status='published for live testing; owner native QA open',release=public['release'],changed_public_files=publication['changed_files'],source_main=deployed['source_revision'])
    for article in wiki_review['articles']:
        if article['decision']=='candidate location/access notice':article['decision']='live location/access notice and Hate location table reconciled'
    (HERE/'wiki-review.json').write_text(json.dumps(wiki_review,indent=2)+'\n')
    result=subprocess.run(['python','-X','utf8','-B','E:/EQ_Local_Dev/_worktrees/hate-keeper-wiki/wiki/check_refresh.py','--repo',str(ROOT),'--ref','HEAD','--include-worktree'],capture_output=True,text=True,encoding='utf-8')
    assert result.returncode in (0,1);(HERE/'wiki-live-refresh.json').write_text(result.stdout,encoding='utf-8')
    print('Verified live release records updated; owner native QA stays open.')
if __name__=='__main__':main()
