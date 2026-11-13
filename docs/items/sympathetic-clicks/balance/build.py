"""Build the instrumented encounter executable in its own /tmp sandbox inside the local game container."""
import hashlib
import json
import shutil
import shlex
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

R = Path("/tmp/nightcap-balance-sympathetic")
P = Path("/tmp/nightcap-balance-raid-augs-20261112")
B = Path("/tmp/nightcap-classic-raid-augs-105a250f/build")
S = B.parent / "source"


def replace(text, before, after):
    if text.count(before) != 1:
        raise ValueError("Diagnostic anchor count changed: " + before[:80])
    return text.replace(before, after)


def sha(path):
    digest=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            digest.update(block)
    return digest.hexdigest()


def command(target):
    output = subprocess.check_output(["ninja", "-t", "commands", target], cwd=B, text=True)
    return shlex.split(output.splitlines()[-1])


def compile_one(pair):
    name, source = pair
    flags = command("zone/CMakeFiles/zone.dir/main.cpp.o")
    # Don't import baseline Mob declarations through the retained precompiled header.
    flags = flags[:flags.index("-Winvalid-pch")]
    flags[1:1] = ["-I" + str(R / "source"), "-I" + str(R / "source/zone"), "-I" + str(P)]
    for header in ("common/pch/app-pch.h","common/pch/std-pch.h","zone/pch/pch.h"):
        flags.extend(["-include",str(R/"source"/header)])
    with (R / (name + ".log")).open("w") as log:
        subprocess.run([*flags, "-c", str(source), "-o", str(R / (name + ".o"))],
                       stdout=log, stderr=subprocess.STDOUT, cwd=B, check=True)


def adapter():
    tree = R / "source"
    tree.mkdir(exist_ok=True)
    for d in S.iterdir():
        if d.name == "zone":
            if not (tree / d.name).exists():
                shutil.copytree(d, tree / d.name)
        elif not (tree / d.name).exists():
            (tree / d.name).symlink_to(d)
    h = (P / "native_harness.cpp").read_text()
    h = replace(h, 'db.at("db") != "nightcap_raid_aug_balance_20261112" || db.at("username") != "raid_aug_balance_261112"',
                'db.at("host") != "nightcap-sympathetic-balance" || db.at("db") != "nightcap_sympathetic_balance" || db.at("username") != "sympathetic_fixture"')
    h = replace(h, '(policy == "caster_heal" && build.at("profile") == "war-clr-wiz")',
                '(policy == "caster_heal" && (build.at("profile") == "war-clr-wiz" || (build.at("profile") == "mag-nec-shm" && build.at("classes")==json::array({13,11,10}))))')
    (R / "harness-base.cpp").write_text(h)
    r = (P / "native_runtime.cpp").read_text()
    r = replace(r, 'const uint16 nuke = wpm ? 216 : melee_heal ? 0 : npc_id == 32040 ? 732 : 659;',
                'const uint16 nuke = input.at("nuke");')
    r = replace(r, 'const uint16 heal = c->GetSpellMinLevel(9) <= c->GetLevel() ? 9 : 15;',
                '''const uint16 heal = input.at("heal");
    if (c->GetSpellMinLevel(nuke)>c->GetLevel()) throw std::runtime_error("Ineligible hostile spell");''')
    r = replace(r, "entity_list.AddClient(c);\n\tjson preparation;", """entity_list.AddClient(c);
    // Install the real item click as a self buff, then restore the original worn slot.
    // The harness calls the same CastSpell entry used after native packet validation.
    if (input.contains("cover")) {
        for (int spell : input.at("cover").get<std::vector<int>>()) {
            if (c->GetSpellMinLevel(spell)>c->GetLevel()) throw std::runtime_error("Illegal preparation spell "+std::to_string(spell));
        }
        PrepareEncounter(c,{{"spell_ids",input.at("cover")},{"recover",true},{"max_duration_ms",900000}});
    }
    const uint32 cover_count=[&]() { uint32 n=0; for(int i=0;i<c->GetMaxTotalSlots();++i) n+=IsValidSpell(c->GetBuffs()[i].spellid); return n; }();
    const auto clicks=input.at("clicks").get<std::vector<uint32>>();
    for (uint32 id : {610338u,610150u}) {
        int slot = id == 610338 ? 5 : 15;
        std::unique_ptr<EQ::ItemInstance> original(c->GetInv().PopItem(slot));
        std::unique_ptr<EQ::ItemInstance> item(database.CreateItem(id));
        if (!item || !c->CanEquipItem(item->GetItem()) || !(item->GetItem()->Slots & (1u<<slot)) ||
            c->GetInv().PutItem(slot,*item)!=slot) throw std::runtime_error("Equip click failed");
        c->CalcBonuses();
        auto *d=item->GetItem();
        for (int n=0;n<20;++n) { Advance(50); c->Process(); }
        if (d->Click.Effect != (id==610338 ? 44379 : 44380) ||
            !c->CastSpell(d->Click.Effect,c->GetID(),EQ::spells::CastingSlot::Item,d->CastTime,0,0,slot))
            throw std::runtime_error("Native item click failed "+std::to_string(id)+" effect "+std::to_string(d->Click.Effect));
        for (int n=0;n<240 && !c->FindBuff(d->Click.Effect);++n) { Advance(50); c->Process(); }
        if (!c->FindBuff(d->Click.Effect)) throw std::runtime_error("Click buff absent");
        delete c->GetInv().PopItem(slot);
        if(original) c->GetInv().PutItem(slot,*original);
        c->CalcBonuses();
    }
    for (uint32 id : {610338u,610150u}) {
        const uint16 spell=id==610338 ? 44379 : 44380;
        bool active=std::find(clicks.begin(),clicks.end(),id)!=clicks.end();
        if (!active) c->BuffFadeBySpellID(spell);
        if (c->FindBuff(spell)!=active) throw std::runtime_error("Equipment swap or buff control failed");
    }
    json preparation;""")
    # Use fight-relative times even when no preparation controller was requested.
    r = replace(r,'{"player_autoattack",c->AutoAttackEnabled()},{"player_ai",c->IsAIControlled()},',
        '{"cover_buffs",cover_count},{"strike",c->FindBuff(44379)},{"healing",c->FindBuff(44380)},{"player_autoattack",c->AutoAttackEnabled()},{"player_ai",c->IsAIControlled()},')
    r = replace(r,'NCReset(); const uint32 combat_start = Timer::GetCurrentTime();',
                'NCReset(); streams.at(c)->events.clear(); const uint32 combat_start = Timer::GetCurrentTime();')
    r = replace(r, 'if (input.contains("preparation")) {\n\t\t// Keep native clocks continuous;',
                'if (true) {\n\t\t// Keep native clocks continuous;')
    (R / "native_runtime.cpp").write_text(r)
    compile_one(("native_runtime",R/"native_runtime.cpp"))


def candidate(baseline=False,harness_only=False):
    replacements = {}
    staged = [S/"zone/spells.cpp"] if baseline else sorted((R / "candidate").glob("*"))
    for f in staged:
        shutil.copyfile(f, R / "source/zone" / f.name)
    assert baseline or {"mob.cpp","spells.cpp","spell_effects.cpp","nightcap_sympathetic.h"} <= {p.name for p in staged}
    if not baseline and "constexpr int StrikeAmount = 8, HealingAmount = 12;" in (R/"source/zone/nightcap_sympathetic.h").read_text():
        hdr=R/"source/zone/nightcap_sympathetic.h"
        x=replace(hdr.read_text(),"constexpr int StrikeAmount = 8, HealingAmount = 12;",
            '''inline int DiagnosticRankAmount(int original, int alternative) {
    const char *mode=std::getenv("NIGHTCAP_BALANCE_LARGER_RANK");
    return mode && std::string(mode)=="1" ? alternative : original;
}
inline const int StrikeAmount=DiagnosticRankAmount(8,40), HealingAmount=DiagnosticRankAmount(12,48);''')
        hdr.write_text('#include <cstdlib>\n#include <string>\n'+x)
    # Report actual mana charged (including fizzles) independently of regeneration.
    s = (R / "source/zone/spells.cpp").read_text()
    for statement, spent in [('Mob::SetMana(before - use_mana);','before - GetMana()'),
                             ('SetMana(before_mana - mana_used);','before_mana - GetMana()')]:
        s = replace(s, statement, statement+' if (IsClient()) NCSpellSpend(spell_id,'+spent+');')
    (R / "source/zone/spells.cpp").write_text('void NCSpellSpend(unsigned short,long long);\n'+s)
    if not (R/"harness-base.cpp").exists():
        shutil.copyfile(R/"native_harness.cpp",R/"harness-base.cpp")
    h = (R / "harness-base.cpp").read_text()
    h = replace(h, "static int64_t observed[8] = {};", """static int64_t observed[8] = {};
static std::map<unsigned short,long long> nc_spent;
void NCSpellSpend(unsigned short spell,long long amount) { nc_spent[spell]+=amount; }""")
    h = replace(h, 'std::ofstream output_file(argv[3]);', 'output["native_seed_hook_calls"]=balance_seed_calls.load(); output["mana_spent_by_spell"]=nc_spent; std::ofstream output_file(argv[3]);')
    (R / "native_harness.cpp").write_text(h)
    names = [(f.stem,R / "source/zone" / f.name) for f in staged if f.suffix == ".cpp"]
    bonus = (S/"zone/bonuses.cpp").read_text()
    anchor = "itembonuses.HealAmt = std::min(itembonuses.HealAmt, RuleI(Character, ItemHealAmtCap) + heal_headroom);"
    bonus = replace(bonus, anchor,anchor+'''
        if (const char *v=std::getenv("NIGHTCAP_BALANCE_CAP_STRESS"); v && std::string(v)=="1") {
            itembonuses.SpellDmg=RuleI(Character,ItemSpellDmgCap)+spell_headroom;
            itembonuses.HealAmt=RuleI(Character,ItemHealAmtCap)+heal_headroom;
        }''')
    (R/"source/zone/bonuses.cpp").write_text(bonus)
    names += [("bonuses",R/"source/zone/bonuses.cpp")]
    with ThreadPoolExecutor(2) as executor:
        list(executor.map(compile_one,[*([] if harness_only else names),("native_harness",R / "native_harness.cpp")]))
    for name, _ in names:
        replacements[name] = R / (name + ".o")
    for name, adapter_name in [('main','balance_main'),('client','balance_client'),('zone_hunt','balance_hunt'),
                               ('attack','balance_attack'),('client_packet','balance_packet')]:
        replacements.setdefault(name, P / (adapter_name + ".o"))
    link = command("bin/zone")[2:-2]
    for name, obj in replacements.items():
        link[link.index('zone/CMakeFiles/zone.dir/'+name+'.cpp.o')] = str(obj)
    binary = R / ('baseline-zone' if baseline else 'balance-zone')
    temporary=binary.with_suffix(".linking")
    link[link.index('-o')+1] = str(temporary)
    link[1:1] = [str(R/'native_runtime.o'),str(R/'native_harness.o'),
                 '-Wl,--wrap=_ZNSt13random_device9_M_getvalEv,--wrap=gettimeofday,--wrap=time,--wrap=_ZN11WorldServer10SendPacketEP12ServerPacket']
    subprocess.run(link,cwd=B,check=True)
    temporary.replace(binary)
    manifest = {"binary":sha(binary), "prior_diagnostic": sha(P/"balance-zone"),
                "staged_sources":{f.name:sha(f) for f in staged},"harness":sha(R/"native_harness.cpp"),
                "runtime":sha(R/"native_runtime.cpp"),
                "instrumented_sources":{f.name:sha(R/"source/zone"/f.name) for f in staged},
                "link_inputs":{x:sha(B/x) for x in link if x.endswith((".o",".a"))}}
    (R/("baseline-build.json" if baseline else "build.json")).write_text(json.dumps(manifest,indent=2)+"\n")


if __name__ == "__main__":
    assert Path.cwd() == R
    {"adapter":adapter, "candidate":candidate,"baseline":lambda: candidate(True),
     "relink-harness":lambda: candidate(harness_only=True)}[sys.argv[1]]()
