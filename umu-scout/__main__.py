import hashlib
import json
import os
import shutil
import sys
import tarfile
from datetime import date
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
package_version_file = f"{package_name}.version.json"

github_repo = os.environ.get("UMU_SCOUT_REPO", f"Open-Wine-Components/{package_name}")
github_headers: dict[str, str] = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "",
}
github_latest_url = f"https://api.github.com/repos/{github_repo}/releases/latest"


def get_latest_release() -> dict | None:
    latest: dict | None = None

    with urlopen(github_latest_url) as url_fd:
        release = json.load(url_fd)

    if release is not None:
        asset = next((a for a in release["assets"] if a["name"] == package_version_file), None)
        if asset is not None:
            with urlopen(asset["browser_download_url"]) as url_fd:
                latest = json.load(url_fd)
        else:
            print(f"Could not find asset {package_version_file} at https://github.com/{github_repo}", file=sys.stderr)
    else:
        print(f"Could not find latest release at https://github.com/{github_repo}", file=sys.stderr)

    return latest


if __name__ == "__main__":
    old_ver: dict | None = None
    if len(sys.argv) > 1 and sys.argv[1] == "update":
        try:
            old_ver = get_latest_release()
        except Exception as e:
            print(f"Could not read old versions from {github_latest_url}: {str(e)}", file=sys.stderr)
            print("Downloading latest", file=sys.stderr)
    else:
        print("Downloading latest", file=sys.stderr)

    versions = {
        "app1070560": urlopen(app1070560_ver_url).read().strip().decode("utf-8"),
        "steam-runtime": urlopen(steam_runtime_ver_url).read().strip().decode("utf-8"),
        "tag": str(date.today()).replace("-", "")
    }

    for part in package_parts:
        print(f"{part}: {old_ver.get(part) if old_ver else None} -> {versions[part]}", file=sys.stderr)
    print(f"tag: {old_ver.get('tag') if old_ver else None} -> {versions['tag']}", file=sys.stderr)

    if old_ver is not None and all([old_ver.get(p) == versions[p] for p in package_parts]):
        print("Already up to date", file=sys.stderr)
        sys.exit(0)

    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(exist_ok=True)

    with tarfile.open(name=None, fileobj=BytesIO(urlopen(app1070560_tar_url).read())) as tar:
        tar.extractall(dist, filter="fully_trusted")

    with tarfile.open(name=None, fileobj=BytesIO(urlopen(steam_runtime_tar_url).read())) as tar:
        tar.extractall(dist.joinpath("SteamLinuxRuntime"), filter="fully_trusted")

    urlretrieve(steam_runtime_csum_url, dist.joinpath("SteamLinuxRuntime", "steam-runtime.tar.xz.checksum"))

    shutil.move(dist.joinpath("SteamLinuxRuntime"), dist.joinpath(package_name))
    shutil.make_archive(
        dist.joinpath(package_name).as_posix(),
        format="xztar",
        root_dir=dist,
    )

    archive = dist.joinpath(package_name).with_suffix(".tar.xz")
    with open(archive, "rb") as tar:
        sha512sum = hashlib.sha512(tar.read()).hexdigest()

    with open(dist.joinpath(package_name).with_suffix(".sha512sum"), "w") as fd:
        fd.write(f"{sha512sum} {archive.name}")

    with open(dist.joinpath(package_version_file), "w") as versions_json:
        versions_json.write(json.dumps(versions))

    # to stdout to be captured as tag
    print(versions["tag"], file=sys.stdout)

    sys.exit(0)
