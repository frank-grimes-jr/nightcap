"""Package the built Windows preview, notices and matching editable source for distribution."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import zipfile


def write(archive, path, name):
    if not path.is_file() or path.is_symlink():
        raise ValueError(path)
    info = zipfile.ZipInfo(name, (2026, 11, 22, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o100644 << 16
    archive.writestr(info, path.read_bytes())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for arg in ("source", "runtime", "deps", "output"):
        parser.add_argument(arg, type=Path)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    revision = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=source, text=True).strip()
    if revision != "45cf0cf6489f30f39f660c6791a85d4e531d6f8f":
        raise ValueError("unexpected Hailstone base")
    args.output.mkdir(parents=True, exist_ok=True)
    paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=source).decode().strip("\0").split("\0")
    paths += ["src/net/nightcap_creation.h", "tools/nightcap_ui_probe.h"]
    deps = sorted(p for p in args.deps.iterdir() if p.is_dir())
    source_zip = args.output / "nightcap-hailstone-source.zip"
    binary_zip = args.output / "nightcap-hailstone.zip"
    with zipfile.ZipFile(source_zip, "w") as archive:
        for name in sorted(set(paths)):
            write(archive, source / name, "hailstone/" + name)
        for dep in deps:
            for path in sorted(dep.rglob("*")):
                if path.is_file() and ".git" not in path.relative_to(dep).parts:
                    write(archive,path,"deps/" + path.relative_to(args.deps).as_posix())
        write(archive, Path(__file__), "package_preview.py")
        write(archive, Path(__file__).with_name("BUILD-PREVIEW.md"), "BUILD-PREVIEW.md")
    with zipfile.ZipFile(binary_zip, "w") as archive:
        for name in ("hailstone.exe", "SDL3.dll", "zlib1.dll"):
            write(archive,args.runtime / name,name)
        for name in ("flora", "icons", "pictures", "shaders", "ui"):
            for path in sorted((args.runtime / name).rglob("*")):
                if path.is_file():
                    write(archive,path,path.relative_to(args.runtime).as_posix())
        for name in ("LICENSE","NOTICE.md","THIRD_PARTY.md"):
            write(archive,source/name,name)
        for root in [*deps, source / "third_party"]:
            for path in sorted(root.rglob("*")):
                if path.is_file() and path.name.lower().startswith(("license","licence","copying","copyright")):
                    write(archive,path,"licenses/"+ root.name + "/" + path.relative_to(root).as_posix())
    for path in (source_zip,binary_zip):
        with path.open("rb") as file:
            print(path.name, path.stat().st_size, hashlib.file_digest(file,"sha256").hexdigest(), flush=True)


if __name__ == "__main__":
    main()
