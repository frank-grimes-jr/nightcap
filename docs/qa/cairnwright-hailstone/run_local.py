"""Exercise a real LocalDev login, creation, camp, and second login with Hailstone."""
import argparse
import os
from pathlib import Path
import re
import secrets
import string
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playprobe", type=Path)
    parser.add_argument("game_dir", type=Path)
    parser.add_argument("--relog-only", action="store_true")
    args = parser.parse_args()
    exe = args.playprobe.resolve(strict=True)
    assets = args.game_dir.resolve(strict=True)
    suffix = "".join(secrets.choice(string.ascii_lowercase) for _ in range(5))
    user = os.environ.get("NIGHTCAP_QA_ACCOUNT", "")
    name = os.environ.get("NIGHTCAP_QA_CHARACTER", "Tor" + suffix)
    if not re.fullmatch("ncqa[a-z]{5}", user) or not re.fullmatch("Tor[a-z]{5}", name):
        parser.error("use a disposable ncqa account and Tor character with five lowercase suffix letters")
    if not os.environ.get("NIGHTCAP_QA_PASSWORD"):
        parser.error("set NIGHTCAP_QA_PASSWORD for the disposable account")
    if args.relog_only and not os.environ.get("NIGHTCAP_QA_CHARACTER"):
        parser.error("set NIGHTCAP_QA_CHARACTER to the previously created character")
    print(f"Disposable LocalDev account {user}, character {name}", flush=True)
    with tempfile.TemporaryDirectory(prefix="nightcap-hailstone-") as temp:
        env = {**os.environ, "EQ_GAME_DIR": str(assets), "HAILSTONE_DATA_DIR": temp}
        common = [str(exe), "127.0.0.1:5998", user, "--password-env", "--plugins", temp,
                  "--char", name, "--seconds", "3"]
        for phase, extra in [("create", ["--create", name, "--race", "8", "--class", "17",
                                         "--start-zone", "67"]), ("relog", [])]:
            if args.relog_only and phase == "create":
                continue
            p = subprocess.run(common + extra, env=env, cwd=temp, capture_output=True,
                               timeout=200, encoding="utf-8", errors="replace")
            log = p.stdout + p.stderr
            # Print only ordinary app status; login credentials never enter the command line or report.
            keep = ("creating ", "character(s):", "zone profile:", "final state:", "login:",
                    "login ok", "missing combination", "creation UI:", "connection:", "no servers", "no characters")
            for line in dict.fromkeys(line.strip() for line in log.splitlines() if any(key in line for key in keep)):
                print(f"{phase}: {line}", flush=True)
            expected = [fr"{name}\(L1 r8 c17 z\d+\)", r"zone profile: race 8 class 17 level 1",
                        r"final state: .*Camped out\."]
            if phase == "create":
                expected.append(fr"creating {name}: race 8 class 17 deity 202 zone 67")
            missing = [pattern for pattern in expected if not re.search(pattern, log)]
            if p.returncode or missing:
                raise SystemExit(f"{phase} failed (exit {p.returncode}, missing {missing})")


if __name__ == "__main__":
    main()
