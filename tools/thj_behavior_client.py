"""Stage a paired client delta from the verified current signed assets. Never install."""
import argparse,hashlib,json
from pathlib import Path
from decimal import Decimal,InvalidOperation
import thj_behavior_content as content

DESCRIPTIONS={
500:'Reduces spell hate by 20/40/60/80/100 percent. Available to all casting classes. Duration one hour; reuse 60 seconds; timer can suspend in safe zones.',
912:'Increases damage from all physical attack skills by 100 percent for up to 12 seconds. Reuse 60 seconds.',
3732:'Deals 1 opening damage and makes the target take 50 percent more physical hit damage for up to 12 seconds. Reuse 45 seconds.',
467:'Deals 1 opening damage and reduces target armor class by 50 for up to 12 seconds. Reuse 30 seconds.',
601:'Deals 1 opening damage and reduces target evasion by 50 for up to 12 seconds. Reuse 30 seconds.',
76:'Consumes 50 percent of maximum mana once to heal nearby group members for 2 HP per mana spent. Requires the full mana cost. No outgoing critical heal or Healing Amount bonus. Native reuse 72 minutes.',
172:'Activate to restore 40 percent of maximum mana. Existing rank cast time and reuse are retained.',
565:'Consumes 10 percent of maximum mana and deals 4 damage per mana spent. Requires the full cost. A target under Mana Burn immunity rejects all four ranks without consuming mana or cooldown. Base reuse 51 minutes, reduced to 15 minutes by full Hastened Manaburn.',
793:'Consumes 20 percent of maximum mana; otherwise follows Mana Burn rules and reuse.',
794:'Consumes 30 percent of maximum mana; otherwise follows Mana Burn rules and reuse.',
625:'Consumes 40 percent of maximum mana; otherwise follows Mana Burn rules and reuse.',
1156:'Reduces reuse of Mana Burn, Mana Blast, Mana Blaze and Volatile Mana Blaze by six minutes per rank, to 15 minutes at rank VI.',
514:'Fire spells meeting the retained level, mana and cast limits have a 35 percent Pyromancy proc chance. Adds initial fire damage and a fire damage-over-time effect that lowers cold resistance. Stacks with other buffs; duplicate ranks do not stack.',
640:'Cold spells meeting the retained level, mana and cast limits have a 35 percent Cryomancy proc chance. Adds initial cold damage and a cold damage-over-time effect that lowers fire resistance. Stacks with other buffs; duplicate ranks do not stack.',
30201:'Protects spellcasting from hit, movement, channeling and hostile spell-interrupt effects for 120 seconds. Does not prevent stuns or voluntary cancellation. Costs 12 AA; base reuse 30 minutes.',
}

def equivalent(a,b):
    if str(a)==str(b):return True
    try:return Decimal(a)==Decimal(b)
    except (InvalidOperation,ValueError,TypeError):return False

def spells(raw):
    before=content.snapshot();after,_=content.prepare();cols=before['schemas']['spells_new']
    assert len(cols)==237
    old={r['id']:r for r in before['tables']['spells_new']};new={r['id']:r for r in after['spells_new']}
    rows={};order=[]
    for line in raw.decode('latin1').splitlines():
        f=line.split('^');sid=int(f[0])
        if len(f)!=237 or sid in rows:raise ValueError('Malformed client spell file')
        rows[sid]=f;order.append(sid)
    changed=[]
    for sid,r in new.items():
        if sid in old and r==old[sid]:continue
        if sid not in old:
            if sid in rows:raise ValueError('Custom client spell ID occupied')
            rows[sid]=['' if r[c] is None else str(r[c]) for c in cols];order.append(sid)
        else:
            if sid not in rows or rows[sid][1]!=r['name']:raise ValueError(f'Client identity missing {sid}')
            for i,col in enumerate(cols):
                if r[col]==old[sid][col]:continue
                # Existing instant-DoT projection stays paired with server policy.
                if col=='cast_time' and rows[sid][i]=='0' and old[sid][col]==3000:continue
                if not equivalent(rows[sid][i],old[sid][col]) and not equivalent(rows[sid][i],r[col]):raise ValueError(f'Client field drift {sid}/{col}: {rows[sid][i]}')
                rows[sid][i]='' if r[col] is None else str(r[col])
        changed.append(sid)
    # Client inspection displays the native runtime focus projection. The server
    # database retains base values, preventing application of the multiplier twice.
    focus_changed=[]
    for sid,f in rows.items():
        bard=0<int(f[111])<255
        dot=any(int(f[86+i])==140 and int(f[20+i])>0 for i in range(12))
        updated=False
        for i in range(12):
            spa=int(f[86+i]);damage=spa in (124,461)
            if spa not in (124,461,125,132,131,130):continue
            base,limit=int(f[20+i]),int(f[32+i])
            if bard and damage:
                factor=1 if dot else 10;value,maximum=base*factor,limit*factor
            else:
                value=limit if abs(limit)>abs(base) else base
                if damage and sid not in (5915,11064):value*=10
                maximum=value
            f[20+i],f[32+i]=str(value),str(maximum);updated=True
        if updated:focus_changed.append(sid)
    return ('\r\n'.join('^'.join(rows[sid]) for sid in order)+'\r\n').encode('latin1'),dict(content_spells=changed,focus_display_spells=focus_changed)

def strings(raw):
    tables,_=content.prepare();abilities={a['id']:a for a in tables['aa_ability']};ranks={r['id']:r for r in tables['aa_ranks']};updates={}
    for aid,text in DESCRIPTIONS.items():
        for rank in content.chain(aid,abilities,ranks):updates[(rank['desc_sid'],4)]=text
    for aid in content.RETIRED:
        for rank in content.chain(aid,abilities,ranks):updates[(rank['desc_sid'],4)]='Retired by the THJ behavior update. Purchased ranks are removed and their recorded AA costs refunded atomically on login.'
    for kind in (1,2,3,6):updates[(43220,kind)]='Dimensional Shielding'
    updates[(43220,4)]=DESCRIPTIONS[30201]
    out=[];seen=set()
    for line in raw.decode('latin1').splitlines():
        parts=line.split('^',2)
        try:key=(int(parts[0]),int(parts[1]))
        except (ValueError,IndexError):out.append(line);continue
        if key in updates:
            if key in seen:raise ValueError('Duplicate client AA text')
            seen.add(key);line=f'{key[0]}^{key[1]}^{updates[key]}'
        out.append(line)
    for key in sorted(updates.keys()-seen):out.append(f'{key[0]}^{key[1]}^{updates[key]}')
    return ('\r\n'.join(out)+'\r\n').encode('latin1')

def main():
    p=argparse.ArgumentParser();p.add_argument('--base',type=Path,required=True);p.add_argument('--out',type=Path,required=True);args=p.parse_args()
    manifest=json.loads((args.base/'manifest.json').read_text());assert manifest['release']==2026101901
    for name,row in manifest['files'].items():assert hashlib.sha256((args.base/name).read_bytes()).hexdigest()==row['sha256']
    args.out.mkdir(exist_ok=False,parents=True)
    data,audit=spells((args.base/'spells_us.txt').read_bytes())
    (args.out/'spells_us.txt').write_bytes(data);(args.out/'dbstr_us.txt').write_bytes(strings((args.base/'dbstr_us.txt').read_bytes()))
    report=dict(status='unsigned_delta_not_installed',required_base_release=manifest['release'],proxy='unchanged 0.11.0',content=audit,files={p.name:dict(sha256=hashlib.sha256(p.read_bytes()).hexdigest(),size=p.stat().st_size) for p in args.out.iterdir()})
    (args.out/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='content'}))
if __name__=='__main__':main()
