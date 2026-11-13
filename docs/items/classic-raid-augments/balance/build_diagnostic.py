"""Run inside the local candidate container. Build a separate, fixture-only Ninja diagnostic."""
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shlex
import subprocess
import sys

R = Path('/tmp/nightcap-balance-raid-augs-20261112')
C = Path('/tmp/nightcap-classic-raid-augs-105a250f')
S, B = C / 'source', C / 'build'
D = 'nightcap_raid_aug_balance_20261112'
sys.path.insert(0, str(R))
from build_native import patched_client, patched_main


def once(source, old, new):
    if source.count(old) != 1:
        raise ValueError('Diagnostic anchor changed: ' + old[:100])
    return source.replace(old, new)


def ninja(target):
    line = subprocess.check_output(['ninja', '-t', 'commands', target], cwd=B, text=True).splitlines()[-1]
    return shlex.split(line)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda: f.read(1024*1024), b''):
            h.update(chunk)
    return h.hexdigest()


def main():
    assert Path.cwd() == R
    orig = {p: (S / 'zone' / p).read_text() for p in ['main.cpp', 'client.cpp', 'zone_hunt.cpp', 'raid_augment.inc','attack.cpp','client_packet.cpp']}
    (R / 'balance_main.cpp').write_text(patched_main(orig['main.cpp']))
    (R / 'balance_client.cpp').write_text(patched_client(orig['client.cpp']))
    inc = orig['raid_augment.inc']
    for old, new in [
        ('damage -= absorbed;', 'damage -= absorbed; NCObserve(0, absorbed);'),
        ('c.raid_augment.ward = 120;', 'NCObserve(1, 1); c.raid_augment.ward = 120;'),
        ('c.SetHP(c.GetHP() + healed);', 'NCObserve(2, healed); c.SetHP(c.GetHP() + healed);'),
        ('state.ClearSpend();','NCObserve(mana ? 3 : 4, restore); state.ClearSpend();'),
    ]:
        inc = once(inc, old, new)
    (R/'balance_hunt.cpp').write_text(once(orig['zone_hunt.cpp'], '#include "zone/raid_augment.inc"',
        'void NCObserve(int, int64_t);\n'+inc))
    (R/'balance_attack.cpp').write_text('void NCObserve(int, int64_t);\n'+once(orig['attack.cpp'],
        'const uint64 acthealed = curhp < maxhp ? std::min<uint64>(amount, maxhp - curhp) : 0;',
        '''const uint64 acthealed = curhp < maxhp ? std::min<uint64>(amount, maxhp - curhp) : 0;
        if (IsClient()) { NCObserve(5, acthealed); }
        else if (GetOwner() && GetOwner()->IsClient()) { NCObserve(6, acthealed); }'''))
    (R/'balance_packet.cpp').write_text('void NCObserve(int, int64_t);\n'+once(orig['client_packet.cpp'],
        'SetHP(GetHP() + healed);','NCObserve(7, healed); SetHP(GetHP() + healed);'))
    h = (R/'harness.in.cpp').read_text()
    start = h.index('if ((db.at("db")')
    end = h.index('|| server.contains("content_database")', start)
    h = h[:start]+f'if (db.at("db") != "{D}" || db.at("username") != "raid_aug_balance_261112" '+h[end:]
    h = once(h, 'extern Zone *zone;', '''extern Zone *zone;
static int64_t observed[8] = {};
static uint32_t nc_start = 0;
static json nc_events = json::array();
void NCReset() { for (auto &v : observed) { v=0; } nc_start=Timer::GetCurrentTime(); nc_events=json::array(); }
void NCObserve(int index, int64_t amount) { observed[index] += amount;
    if (index < 5) nc_events.push_back({Timer::GetCurrentTime()-nc_start,index,amount}); }''')
    h = once(h, 'std::ofstream output_file(argv[3]);', '''output["raid_effects"] = {{"absorbed",observed[0]}, {"wards", observed[1]}, {"healed",observed[2]}, {"mana",observed[3]}, {"endurance",observed[4]}, {"ordinary_owner_heals",observed[5]}, {"ordinary_pet_heals",observed[6]}, {"mend",observed[7]}, {"events", nc_events}};
        std::ofstream output_file(argv[3]);''')
    h = once(h, 'const auto purchases = c->Purchase(build);', '''const auto purchases = c->Purchase(build);
            if (input.contains("expect_raid_id") && c->raid_augment.item != input.at("expect_raid_id").get<uint32>()) throw std::runtime_error("Raid socket not active");''')
    (R / 'native_harness.cpp').write_text(h)
    r = (R / 'runtime.in.cpp').read_text()
    r='void NCReset();\n'+r
    r=once(r,'const uint32 combat_start = Timer::GetCurrentTime();','NCReset(); const uint32 combat_start = Timer::GetCurrentTime();')
    r=once(r,'trace.push_back(state());\n\tsize_t command_index', 'NCReset(); trace.push_back(state());\n\tsize_t command_index')
    r=once(r,'{"player_position",{c->GetX(),c->GetY(),c->GetZ()}},{"pets",pets}',
        '{"player_endurance",c->GetEndurance()},{"player_position",{c->GetX(),c->GetY(),c->GetZ()}},{"pets",pets}')
    ids = '(npc_id != 32040 && npc_id != 73057)'
    assert r.count(ids) == 2
    r = r.replace(ids,'(npc_id != 32040 && npc_id != 73057 && npc_id != 72003 && npc_id != 76007 && npc_id != 71065)')
    r = once(r,'{"player_hp",c->GetHP()},{"player_mana",c->GetMana()}', '{"player_endurance",c->GetEndurance()},{"player_hp",c->GetHP()},{"player_mana",c->GetMana()}')
    (R / 'native_runtime.cpp').write_text(r)
    base = ninja('zone/CMakeFiles/zone.dir/main.cpp.o')
    flags = base[:base.index('-MD')]+['-I'+str(S/'zone')]
    names = ['balance_main','balance_client','native_harness','native_runtime','balance_hunt','balance_attack','balance_packet']
    def compile_one(name):
        with (R/(name+'.log')).open('w') as log:
            subprocess.run([*flags,'-o',str(R/(name+'.o')),'-c',str(R/(name+'.cpp'))],cwd=B,stdout=log,stderr=subprocess.STDOUT,check=True)
    with ThreadPoolExecutor(3) as executor:
        list(executor.map(compile_one,names))
    raw = ninja('bin/zone')
    assert raw[:2] == [':','&&'] and raw[-2:] == ['&&',':']
    link = raw[2:-2]
    for original, replacement in [('main','balance_main'),('client','balance_client'),('zone_hunt','balance_hunt'),('attack','balance_attack'),('client_packet','balance_packet')]:
        idx = link.index('zone/CMakeFiles/zone.dir/'+original+'.cpp.o')
        link[idx] = str(R/(replacement+'.o'))
    link[link.index('-o')+1] = str(R/'balance-zone-new')
    link[1:1] = [str(R/'native_runtime.o'),str(R/'native_harness.o'),'-Wl,--wrap=_ZNSt13random_device9_M_getvalEv,--wrap=gettimeofday,--wrap=time,--wrap=_ZN11WorldServer10SendPacketEP12ServerPacket']
    subprocess.run(link,cwd=B,check=True)
    (R/'balance-zone-new').replace(R/'balance-zone')
    hashes = {str(x):sha(B/x) for x in link if x.endswith(('.o','.a'))}
    (R/'diagnostic-build.json').write_text(json.dumps({'binary':sha(R/'balance-zone'),'candidate_zone':sha(B/'bin/zone'),
        'shared_memory':sha(B/'bin/shared_memory'),'link_inputs':hashes,'input_sources':{p:sha(S/'zone'/p) for p in orig},
        'diagnostic_sources':{name:sha(R/(name+'.cpp')) for name in names}},indent=2))
    print('Candidate diagnostic linked',len(hashes),flush=True)


if __name__ == '__main__':
    main()
