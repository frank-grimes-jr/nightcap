"""Prepare feature blobs and dated production pins in a local Docker build directory."""
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
SERVER = "akk-stack-eqemu-server-1"
STAGE = "/tmp/nightcap-sympathetic-shipping-20261113"
FROM, TO = "862eb1ac", "dceb54bd"


def place(name, data):
    subprocess.run(["docker", "exec", "-i", SERVER, "python3", "-c",
                    "from pathlib import Path; import sys; Path(sys.argv[1]).write_bytes(sys.stdin.buffer.read())",
                    STAGE + "/" + name], input=data, check=True)


def blob(path):
    return subprocess.check_output(["git", "show", TO + ":" + path], cwd=ROOT)


if __name__ == "__main__":
    subprocess.run(["docker", "exec", SERVER, "mkdir", "-p", STAGE], check=True)
    patch = subprocess.check_output(["git", "diff", "--no-ext-diff", "--no-color",
                                    FROM, TO, "--", "server-mods/code/zone"], cwd=ROOT)
    assert patch.count(b"diff --git ") == 7
    place("feature.patch", patch)
    for name in ("build.py", "verify_layout.py", "verify_actor_layout.py", "cast_probe.py"):
        place(name, (HERE / name).read_bytes())
    place("production-verified.json", (ROOT / "docs/releases/stock-worn-atk-20261113/production-verified.json").read_bytes())
    for name in ("cache_layout.cpp", "local_cast_probe.cpp"):
        place(name, blob("docs/items/sympathetic-clicks/runtime/" + name))
    for name in ("test_sympathetic_cast.py", "sympathetic_cast_fixture.cpp", "test_heal_targeting.py"):
        place(name, blob("tools/tests/" + name))
