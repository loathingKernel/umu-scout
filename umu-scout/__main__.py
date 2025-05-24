import json
import shutil
import sys
import tarfile
from io import BytesIO
from pathlib import Path
from urllib.request import urlopen, urlretrieve

dist = Path("dist").resolve()

app1070560_tar_url = "https://repo.steampowered.com/pressure-vessel/snapshots/latest/app1070560/SteamLinuxRuntime.tar.xz"
app1070560_ver_url = "https://repo.steampowered.com/pressure-vessel/snapshots/latest/VERSION.txt"

steam_runtime_tar_url = "https://repo.steampowered.com/steamrt1/images/latest-public-beta/steam-runtime.tar.xz"
steam_runtime_ver_url = "https://repo.steampowered.com/steamrt1/images/latest-public-beta/steam-runtime.version.txt"
steam_runtime_csum_url = "https://repo.steampowered.com/steamrt1/images/latest-public-beta/steam-runtime.tar.xz.checksum"

package_parts =  ("app1070560", "steam-runtime")

package_name = "umu-scout"


if __name__ == "__main__":
    old_ver: dict | None = None
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1], "r") as fd:
                old_ver = json.loads(fd.read())
        except Exception as e:
            print(f"Could not read old versions from {sys.argv[1]}: {str(e)}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Downloading latest", file=sys.stderr)

    versions = {
        "app1070560": urlopen(app1070560_ver_url).read().strip().decode("utf-8"),
        "steam-runtime": urlopen(steam_runtime_ver_url).read().strip().decode("utf-8"),
    }

    for part in package_parts:
        print(f"{part}: {old_ver.get(part) if old_ver else None} -> {versions[part]}", file=sys.stderr)

    if old_ver is not None and all([old_ver.get(p) == versions[p] for p in package_parts]):
        print("Already up to date", file=sys.stderr)
        sys.exit(0)

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(exist_ok=True)

    with open(dist.joinpath(f"{package_name}.version.json"), "w") as versions_json:
        versions_json.write(json.dumps(versions))

    with tarfile.open(name=None, fileobj=BytesIO(urlopen(app1070560_tar_url).read())) as tar:
        tar.extractall(dist)

    with tarfile.open(name=None, fileobj=BytesIO(urlopen(steam_runtime_tar_url).read())) as tar:
        tar.extractall(dist.joinpath("SteamLinuxRuntime"))

    urlretrieve(steam_runtime_csum_url, dist.joinpath("SteamLinuxRuntime", "steam-runtime.tar.xz.checksum"))

    shutil.move(dist.joinpath("SteamLinuxRuntime"), dist.joinpath(package_name))
    shutil.make_archive(
        dist.joinpath(package_name).as_posix(),
        format="xztar",
        root_dir=dist,
    )

    sys.exit(0)
