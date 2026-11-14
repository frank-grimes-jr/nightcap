"""Export native build identities and the final shipping executable from Docker."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ART = HERE.parents[3] / "artifacts/thj-combat-prod"
CONTAINER = "akk-stack-eqemu-server-1"


def collect(profile, phase):
    stage = "/tmp/nightcap-thj-combat-20261113/" + profile + "/" + phase
    raw = subprocess.check_output(["docker","exec",CONTAINER,"cat",stage+"/build.json"])
    data = json.loads(raw)
    assert data["profile"] == profile and len(data["zone"]) == 64
    if phase == "combined":
        for name in ("bow.patch","backstab.patch"):
            digest = subprocess.check_output(["docker","exec",CONTAINER,"sha256sum",
                "/tmp/nightcap-thj-combat-20261113/"+name],text=True).split()[0]
            assert digest == hashlib.sha256((HERE/name).read_bytes()).hexdigest()
            data.setdefault("feature_patches",{})[name] = digest
        assert data["feature_patches"]["backstab.patch"] == "f153b30a27a5b38e676964d9a614561350c803e92a0d918e89b34fd641b06ac8"
        raw=(json.dumps(data,indent=2,sort_keys=True)+"\n").encode()
    (HERE / (profile + "-" + phase + ".json")).write_bytes(raw)
    if phase == "combined" and profile == "shipping":
        ART.mkdir(parents=True,exist_ok=True)
        path = ART / "zone"
        subprocess.run(["docker","cp",CONTAINER+":"+stage+"/zone",str(path)],check=True)
        with path.open("rb") as f:
            assert hashlib.file_digest(f,"sha256").hexdigest() == data["zone"]
    print(profile, phase, data["zone"])


if __name__ == "__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("profile",choices=("shipping","local"))
    parser.add_argument("phase",choices=("baseline","bow","combined"))
    args=parser.parse_args()
    collect(args.profile,args.phase)
