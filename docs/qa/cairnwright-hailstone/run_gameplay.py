"""Exercise the opted-in client's own spellbook, cast and Chronicler dialog paths on LocalDev."""
import argparse
import os
from pathlib import Path
import re
import subprocess
import tempfile

SPELLS = [
    "memorize 44381 1", "memorize 44382 2", "rest-mana 9", "stand",
    "cast-self 1", "expect-chat You set your cairn into the ground",
    "step-east", "cast-self 2", "expect-chat Your hammer finds no foe along the seam",
]
PHASES = {
    "cast": SPELLS,
    "adopt": ["target-near chronicler", "say hail", "wait 1", "expect-chat I can help you choose",
              "say embrace Cairnwright", "confirm-popup 317", "expect-chat You have learned the Cairnwright discipline"],
    "release": ["target-near chronicler","say release second","confirm-popup 402",
                "expect-chat Your Cairnwright discipline has been released"],
    "check-release": ["target-near chronicler","say release second","expect-chat That binding is already empty"],
}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("probe",type=Path)
    p.add_argument("assets",type=Path)
    p.add_argument("character")
    p.add_argument("phase",choices=PHASES)
    a=p.parse_args()
    user=os.environ.get("NIGHTCAP_QA_ACCOUNT","")
    if not re.fullmatch(r"ncqa[a-z]{5}",user) or not re.fullmatch(r"Tor[a-z]{5}",a.character):
        p.error("use a disposable LocalDev ncqa account and Tor test character")
    if not os.environ.get("NIGHTCAP_QA_PASSWORD"): p.error("set NIGHTCAP_QA_PASSWORD")
    with tempfile.TemporaryDirectory(prefix="nightcap-gameplay-") as temp:
        quest=Path(temp)/"steps.txt"
        quest.write_text("\n".join(["stop-on-fail","wait 3",*PHASES[a.phase]])+"\n")
        args=[str(a.probe.resolve(strict=True)),"127.0.0.1:5998",user,"--password-env","--char",a.character,
              "--plugins",temp,"--seconds","230","--quest",str(quest)]
        if a.phase=="adopt": args += ["--create",a.character,"--race","8","--class","1"]
        env={**os.environ,"EQ_GAME_DIR":str(a.assets.resolve(strict=True)),"HAILSTONE_DATA_DIR":temp}
        for attempt in range(3):
            run=subprocess.run(args,cwd=temp,env=env,capture_output=True,text=True,errors="replace",timeout=340)
            log=run.stdout+run.stderr
            if (a.phase != "cast" or "QUEST FAIL" not in log or "Your spell fizzles!" not in log
                    or "Camped out." not in log or attempt == 2):
                break
            print("The server reported a fizzle. Retrying the two casts on a fresh login.")
        for line in log.splitlines():
            if any(key in line for key in ("QUEST PASS","QUEST FAIL","QUEST SUMMARY","REST:","final state:","zone profile:")):
                print(line.strip())
        if run.returncode or not re.search(r"QUEST SUMMARY: [1-9]\d* passed, 0 failed",log) or "Camped out." not in log:
            raise SystemExit(1)
        if a.phase=="adopt" and "zone profile: race 8 class 1 level 1" not in log:
            raise SystemExit("Chronicler control must have a stock Warrior primary")

if __name__=="__main__":
    main()
