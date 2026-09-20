"""Compile the production immutable resolver and exercise actual spell ownership."""
import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("pet_catalog", ROOT / "tools/generate_pet_spell_catalog.py")
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)

class PetClassPolicy(unittest.TestCase):
    def test_original_class_ownership(self):
        fixture = r'''#include "pet_class_policy.h"
#include <cassert>
#include <algorithm>
int main() {
    using NightcapPetClasses::Resolve;
    std::array<uint8_t,3> held{10,11,13};
    do {
        assert(Resolve(633,50,held)==13);
        assert(Resolve(443,50,held)==11);
        assert(Resolve(166,50,held)==10);
    } while(std::next_permutation(held.begin(),held.end()));
    assert(Resolve(633,50,{1,11,10})==0); // widened WAR/SHM columns cannot steal mage summon
    assert(Resolve(443,50,{1,13,10})==0);
    assert(Resolve(633,48,{13,11,10})==0);
    assert(Resolve(443,50,{5,11,0})==11); // SHD not eligible for this shared spell until 64
    assert(Resolve(443,64,{5,11,0})==5);
    assert(Resolve(443,64,{11,5,0})==11);
    assert(NightcapPetClasses::Eligible(443,64,11,5)); // persisted NEC identity survives SHD reaching64
    assert(!NightcapPetClasses::Eligible(443,50,5,5));
    assert(!NightcapPetClasses::Eligible(633,50,10,10));
    assert(!NightcapPetClasses::Eligible(633,50,0,13));
    assert(Resolve(690,50,{1,14,13})==14);
    assert(Resolve(999999,50,{13,11,10})==0);
    assert(Resolve(633,50,{0,17,255})==0);
    for (const auto& spell : NightcapPetClasses::Catalog) {
        bool classed=false;
        for (auto n:spell.levels) classed|=n>0 && n<255;
        if (!classed) {
            assert(Resolve(spell.id,50,{1,13,11})==1);
            assert(Resolve(spell.id,50,{0,13,11})==0);
        }
    }
}
'''
        with tempfile.TemporaryDirectory(prefix="nightcap-pet-policy-") as temp:
            out=Path(temp)
            (out/"test.cpp").write_text(fixture)
            include=(ROOT/"server-mods/code/common").as_posix()
            (out/"build.cmd").write_text('@echo off\ncall "C:/BuildTools/VC/Auxiliary/Build/vcvars32.bat" >nul || exit /b 1\n'
                +f'cl /nologo /W4 /WX /EHsc /std:c++17 /I"{include}" test.cpp /Fe:test.exe >build.log 2>&1\nexit /b %errorlevel%\n')
            build=subprocess.run(["cmd","/d","/c",str(out/"build.cmd")],cwd=out)
            self.assertEqual(build.returncode,0,(out/"build.log").read_text())
            run=subprocess.run([str(out/"test.exe")],capture_output=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)

    def test_source_hash_guard(self):
        with self.assertRaisesRegex(ValueError,"hash changed"):
            catalog.generate(b"modified catalog")

    def test_parser_rejects_ambiguous_or_incomplete_data(self):
        row=["0"]*120
        row[0]="633"; row[86]="33"
        row[104:120]=["255"]*16; row[116]="49"
        text="^".join(row).encode()
        self.assertEqual(catalog.parse(text)[0][1][12],49)
        with self.assertRaisesRegex(ValueError,"duplicate"):
            catalog.parse(text+b"\n"+text)
        with self.assertRaisesRegex(ValueError,"Missing"):
            catalog.parse(b"633^Incomplete")
        row[116]="256"
        with self.assertRaisesRegex(ValueError,"Invalid original"):
            catalog.parse("^".join(row).encode())

if __name__=="__main__": unittest.main()
