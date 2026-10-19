"""Maintain reviewed candidate knowledge; never claims gameplay deployment."""
from pathlib import Path
import difflib,hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[3];REL=Path(__file__).resolve().parent
SKILL=Path('C:/Users/verre/.codex/skills/nightcap-development')
OUTPUT=Path(os.environ.get('NIGHTCAP_SKILL_EVIDENCE',str(REL)))
OUTPUT.mkdir(parents=True,exist_ok=True)
COMMON="""## THJ custom behavior and stock-gear candidate — October19

Source:C:/Users/verre/.codex/worktrees/thj-item-spell-parity/EQ_Local_Dev,
feature/thj-behaviors-gear. Gameplay is NOT deployed; Classic50 and209 starter
families remain. Exact behavior/calibrations, source evidence, automated receipts
and owner QA are in docs/releases/thj-behaviors-20261019/{README,CHANGELIST,QA}.md.
Do not use this candidate as live authority. Prior deployed releases below remain
valid for the running server; this candidate supersedes their future-work advice
only for the systems explicitly implemented here.

"""
TEXT={
'multiclass':"""Candidate has1845ranks/489families. Adds Warlord, four Mana Burns, six Hastened
ranks and separate Wizard Dimensional Shielding30201/43220. Rewrites Warrior
attack debuffs, group Valor, activated Harvest, Silent Casting and Pyro/Cryo.
Retires canonical families25/252/8300/3521/3522/758 with one atomic recorded-cost
refund via PersistEarnedAAState on login. Only25 was immediately legal; dormant
owned duplicates remain resolvable. Other costs, ownership, gates and starter
grants remain. tools/thj_behavior_content.py owns the new generated policy;
do not regenerate current policy with historical all_class_aa.py alone.

""",
'balance':"""NightcapTHJBehaviors gates new player/permanent-pet focuses and custom resource
conversions. Five focus types select strongest endpoints; ImprovedDamage/2 use10x,
Mage5915/11064 remain100/150%, Bard outgoing DD stays random10x and DoT stays
unmultiplied. Receiving songs get no focus; base3s songs become2.5s. Keep other
focus limits; supported AoE broadening is documented calibration. Valor pays50%
maxmana once and heals2HP/MP; Harvest restores40%; Burns pay10/20/30/40% and
retain4:1 damage, immunity guard before resource/timer mutation. Native branch
review and focus fixtures are executable; group/raid/client and encounter balance
remain owner QA. Dimensional120s/30min and stun exclusion are calibration.

""",
'items':"""tools/thj_stock_scaling.py uses pinned stock ProjectEQ2026-10-17 (not Daybreak
or THJ DB). All131 Normal observations match stock. Exact measured targets win;
ordinary top core stats2x, haste1.5x, SD=max(2INT,WIS), HA=2WIS, Accuracy=ceil(DEX/2),
new heroics=rounded finalstat/4 at Ascended only. Positive native SD/HA/Accuracy/
heroics and sparse utilities/Attack remain stock absent exact evidence. Intermediate
qualities interpolate1/3 and2/3.47809 families/143332definitions change;3563 overflow
families are excluded under actual ItemData bounds. Normal/starters/custom Hunt/
dungeon/augments/bags/quest epics retain treatment. Full285-column preimages guard
numeric SQL and inverse; bounded hash/value staging requires complete matching IDs; pet/WPM effects/sockets/ownership remain. Fresh setup
requires generating the ignored thj-stock-bootstrap.sql companion before SOURCE;
compressed artifact and SHA are retained. Legacy SD/HA planning protects this stock
projection. Do not rerun destructive bootstrap live.

""",
'client':"""tools/thj_behavior_client.py stages an unsigned spells_us/dbstr delta from the
verified signed2026101901 base. Proxy0.11.0/catalog and unrelated signed assets stay
paired. Custom43220 has new AA text; focus displays project native multipliers
without changing server base focus data. Preserve existing client-only class and
instant-DoT projections. No protected reference-client edits. This delta is not
signed or installed; use a separate candidate client and matching test runtime.

""",
'operations':"""Activation needs matching world/zone/shared_memory, guarded AA/spell/item SQL,
new Spells:NightcapTHJBehaviors rule and fresh target caches, then paired client.
The optional local cache smoke was skipped after new-account approval rejection;
no privileges/config changed. Regenerate on target with existing credentials.
Build/rehearse scripts use isolated local paths/DB; no production gameplay changes.
Final paired builds and source provenance pass. Full308932-row/285-column replay,
inverse, late-drift atomicity and bootstrap equivalence pass; separate3guard checks
pass.31-file bundle is staged; target caches and owner gameplay QA remain required.
Reconcile preimage drift; never bypass guards. FLOAT preimages compare exact
canonical stored text, with numeric/case drift rejection tests. Rollback retains
new AA identities and current earned state; never undo login refunds with a player
snapshot. Full build, SQL replay/inverse/fault, client and owner tests are separate
evidence. Do not infer production activation permission from this testing request.

""",
'wiki':"""Wiki20261019-thj-behaviors-candidate-v1 is published. All21guides/432generated
routes reviewed; eleven guides show Not released candidate details. Custom Hunt
catalog384items, commands and current deployed mechanics retain their values.
All465HTTPS hashes/headers and5private denials verify; guarded updater rehearsed
rollback and preserved services/config/private downloads without Nginx reload.
Windows21+9skips/Linux30 tests and6search/7equipment checks pass. Publication does
not deploy gameplay or sign the client. Receipts:wiki-publication.json and
wiki-public-verification.json in the candidate release directory.

"""}
PATHS={
'multiclass':['config/aa-policy.json','server-mods/code/common/nightcap_aa_policy.h','server-mods/code/zone/aa.cpp','server-mods/code/zone/client.h','tools/thj_behavior_content.py','tools/tests/test_thj_behaviors.py','tools/tests/test_aa_tbs_policy.py'],
'balance':['server-mods/code/common/nightcap_thj_behaviors.h','server-mods/code/zone/spells.cpp','server-mods/code/zone/effects.cpp','server-mods/code/zone/spell_effects.cpp','tools/tests/test_thj_behavior_native.py','tools/tests/test_thj_behavior_focus.py','tools/tests/test_aa_temporary_buffs.py'],
'items':['tools/thj_stock_scaling.py','tools/item_scaling_overrides.py','tools/wpm_migration.py','tools/thj_item_migration.py','tools/tests/test_thj_item_staging.py','tools/tests/test_thj_stock_scaling.py','tools/fixtures/thj-stock-equipment.json.gz','eq-solo-gm/scripts/tiered_loot_setup.sql'],
'client':['tools/thj_behavior_client.py','tools/tests/test_thj_behavior_client.py'],
'operations':['server-mods/code/common/ruletypes.h','docs/status.md','CHANGES.md','docs/releases/thj-behaviors-20261019/validation-summary.json','docs/releases/thj-behaviors-20261019/database-rehearsal.json','docs/releases/thj-behaviors-20261019/native-source-provenance.json'],
'wiki':['wiki/content-review.json']}
for name in ('ascension','combat','equipment','features','getting-started','index','item-upgrades','multiclass','pets','recent-changes','unreleased'):PATHS['wiki'].append('wiki/articles/'+name+'.json')
for topic in PATHS:
    for name in ('README.md','CHANGELIST.md','QA.md'):PATHS[topic].append('docs/releases/thj-behaviors-20261019/'+name)
for name in ('wiki-review.json','wiki-publication.json','wiki-public-verification.json'):PATHS['wiki'].append('docs/releases/thj-behaviors-20261019/'+name)

def main():
    changes={};scope={};revision=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()+(' + reviewed candidate working changes' if subprocess.check_output(['git','status','--porcelain'],cwd=ROOT,text=True).strip() else '')
    for topic,body in TEXT.items():
        p=SKILL/'references'/(topic+'.md');old=p.read_text(encoding='utf-8');marker=COMMON.splitlines()[0]
        if marker in old:
            a=old.index(marker);b=old.find('\n## ',a+len(marker));oldbase=old[:a]+(old[b+1:] if b>=0 else '')
        else:oldbase=old
        first,rest=oldbase.split('\n',1);new=first+'\n\n'+COMMON+body+rest.lstrip('\n');changes[p]=(old,new)
    p=SKILL/'references/sources.json';old=p.read_text(encoding='utf-8');m=json.loads(old)
    m['observed_revisions']['thj_behaviors_candidate_20261019']=revision
    for topic,names in PATHS.items():
        entries={row['path']:row for row in m['topics'][topic]}
        for name in names:
            entries[name]=dict(root=str(ROOT).replace('\\','/'),path=name,role='Reviewed THJ behavior/gear candidate; gameplay not deployed, wiki publication separately verified',revision=revision,sha256=hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
        m['topics'][topic]=list(entries.values());scope[topic]=[entries[n] for n in names]
    changes[p]=(old,json.dumps(m,ensure_ascii=False,indent=2)+'\n')
    patch=''.join(''.join(difflib.unified_diff(a.splitlines(True),b.splitlines(True),fromfile=str(p),tofile=str(p))) for p,(a,b) in changes.items())
    (OUTPUT/'installed-skill.patch').write_text(patch,encoding='utf-8')
    for p,(_,new) in changes.items():p.write_text(new,encoding='utf-8')
    (OUTPUT/'skill-scope.json').write_text(json.dumps(dict(audited_at='2026-10-19',topics=scope),indent=2)+'\n')
    print('Updated six references and reviewed source entries; gameplay remains candidate')
if __name__=='__main__':main()
