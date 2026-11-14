"""Export and authenticate local Docker native build receipts and the shipping zone."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ART = HERE.parents[3] / "artifacts/heroic-cast-sources"
CONTAINER = "akk-stack-eqemu-server-1"
STAGE = "/tmp/nightcap-heroic-cast-sources-20261114"
UNITS = {"beacon", "effects", "special_attacks", "spell_effects", "spells"}


def collect(profile, phase):
    folder = f"{STAGE}/{profile}/{phase}"
    data = json.loads(subprocess.check_output(["docker","exec",CONTAINER,"cat",folder+"/build.json"]))
    assert data["profile"] == profile and data["link_input_count"] == (144 if profile == "shipping" else 133)
    if phase == "candidate":
        assert profile == "shipping" and set(data["units"]) == UNITS
        pins = subprocess.check_output(["docker","exec",CONTAINER,"sha256sum",STAGE+"/feature.patch",
                                       folder+"/zone"],text=True).splitlines()
        data["feature_patch_sha256"] = hashlib.sha256((HERE/"feature.patch").read_bytes()).hexdigest()
        assert pins[0].split()[0] == data["feature_patch_sha256"] and pins[1].split()[0] == data["zone"]
        ART.mkdir(exist_ok=True,parents=True)
        target = ART/"zone"
        subprocess.run(["docker","cp",CONTAINER+":"+folder+"/zone",str(target)],check=True)
        with target.open("rb") as stream:
            assert hashlib.file_digest(stream,"sha256").hexdigest() == data["zone"]
    (HERE/f"{profile}-{phase}.json").write_bytes((json.dumps(data,indent=2)+"\n").encode())
    print(profile,phase,data["zone"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("profile",choices=("shipping","local"))
    parser.add_argument("phase",choices=("baseline","candidate"))
    args = parser.parse_args()
    collect(args.profile,args.phase)
