# Native build evidence — October 29, 2026

`manifest.json` records the isolated Clang 14/C++20 build, complete source hashes,
all 138 candidate overlay hashes, exact commands for the changed translation
units, and the three linked executable hashes. This is compile/link evidence;
production installation and native player acceptance are separate gates.

The retained Oct28 paired source was copied from
`/tmp/nightcap-paladin-progression-20261028/source` into a new local Docker tree,
`/tmp/nightcap-hate-layout-20261029/source`. Every file in the candidate
`server-mods/code` overlay replaced its corresponding source file. No prior
object files or precompiled headers were reused. Existing vcpkg libraries were
used; all native targets were compiled with fresh CMake/PCH.

Recorded configure command (inside `akk-stack-eqemu-server-1`):

```sh
cmake -S /tmp/nightcap-hate-layout-20261029/source \
  -B /tmp/nightcap-hate-layout-20261029/build \
  -DCMAKE_BUILD_TYPE=RelWithDebInfo \
  -DCMAKE_CXX_COMPILER=/usr/bin/clang++ \
  -DCMAKE_CXX_COMPILER_LAUNCHER=/usr/bin/ccache \
  -DCMAKE_TOOLCHAIN_FILE=/home/eqemu/code/submodules/vcpkg/scripts/buildsystems/vcpkg.cmake \
  -DVCPKG_INSTALLED_DIR=/home/eqemu/code/build/vcpkg_installed \
  -DVCPKG_MANIFEST_MODE=OFF -DVCPKG_MANIFEST_INSTALL=OFF \
  -DEQEMU_BUILD_PCH=ON -DEQEMU_BUILD_TESTS=OFF \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build /tmp/nightcap-hate-layout-20261029/build \
  --target world zone shared_memory -j 3
```

Use a new isolated directory for a clean reproduction and authenticate the
source hashes against the manifest. For incremental verification, copying changed
files must refresh their modification times; preserving earlier source edit times
can leave newer build objects falsely up to date. The final contract/service
resync was therefore forced through a new service-object compile and zone relink,
and all final overlay hashes were checked against the repository again.

Binaries and complete configure/build logs remain in that local container tree;
Windows scratch copies and reproduction scripts are under `work/hate-native`.
They are not installed in the development runtime or published to production.
The build retains existing MySQL comparison warnings. Any future source changes
invalidate this pairing and require a dependency-aware rebuild.
