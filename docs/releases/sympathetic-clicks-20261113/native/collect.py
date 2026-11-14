"""Export checksums and the shipping zone after the scoped native build succeeds."""
import argparse
import hashlib
import json
import subprocess
from stage import HERE, ROOT, SERVER, STAGE


def read(name):
    return subprocess.check_output(["docker", "exec", SERVER, "cat", STAGE + "/" + name])


def digest(path):
    with path.open("rb") as f:
        return hashlib.file_digest(f, "sha256").hexdigest()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("phase", choices=["shipping", "cast"])
    args = p.parse_args()
    proof = json.loads(read("build.json"))
    if args.phase == "shipping":
        art = ROOT / "artifacts/sympathetic-prod"
        art.mkdir(exist_ok=True, parents=True)
        incoming = art / "zone.incoming"
        subprocess.run(["docker", "cp", SERVER + ":" + STAGE + "/zone", str(incoming)], check=True)
        assert digest(incoming) == proof["zone"]
        incoming.replace(art / "zone")
        for name in ("build.json", "layout.json", "actor-layout.json", "link-inputs.json"):
            (HERE / name).write_bytes(read(name))
        assert digest(HERE / "link-inputs.json") == proof["link_manifest_sha256"]
    else:
        cast = json.loads(read("cast.json"))
        assert cast["zone"] == proof["zone"]
        assert cast["shipping_objects"] == {n: obj["candidate"] for n, obj in proof["units"].items()}
        (HERE / "cast.json").write_bytes(read("cast.json"))
    print(proof["zone"])
