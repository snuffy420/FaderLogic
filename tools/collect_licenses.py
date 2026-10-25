"""Copy build-environment license texts and record exact runtime provenance."""
from importlib.metadata import distribution
from pathlib import Path
import ctypes
import hashlib
import json
import os
import shutil
import sys
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def main():
    destination = ROOT / "licenses"
    destination.mkdir(exist_ok=True)
    packages = {}
    for name in ("PyQt6", "PyQt6-Qt6", "PyQt6-sip", "Pillow", "qrcode", "PyInstaller"):
        package = distribution(name)
        copied = []
        for entry in package.files or []:
            value = str(entry)
            if "dist-info" in value and ("license" in Path(value).name.lower() or "copying" in Path(value).name.lower()):
                target = destination / (name + "-" + Path(value).name)
                shutil.copy2(package.locate_file(entry), target)
                copied.append(target.name)
        if not copied:
            raise RuntimeError(f"Missing license text for {name}")
        packages[name] = {"version": package.version, "license_files": copied}
    shutil.copy2(Path(sys.base_prefix) / "LICENSE.txt", destination / "Python-LICENSE.txt")
    import PyQt6
    qt_bin = Path(PyQt6.__file__).parent / "Qt6" / "bin"
    handle = os.add_dll_directory(str(qt_bin))
    av = ctypes.CDLL(str(qt_bin / "avutil-59.dll"))
    ffmpeg = {}
    for name in ("av_version_info", "avutil_configuration", "avutil_license"):
        function = getattr(av, name)
        function.restype = ctypes.c_char_p
        ffmpeg[name] = function().decode("utf-8")
    ffmpeg["source"] = "https://github.com/FFmpeg/FFmpeg/tree/n" + ffmpeg["av_version_info"]
    ffmpeg["libraries"] = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for pattern in ("avcodec-*.dll", "avformat-*.dll", "avutil-*.dll", "swresample-*.dll", "swscale-*.dll")
        for path in qt_bin.glob(pattern)
    }
    license_path = destination / "FFmpeg-COPYING.LGPLv2.1"
    if not license_path.exists():
        url = "https://raw.githubusercontent.com/FFmpeg/FFmpeg/n" + ffmpeg["av_version_info"] + "/COPYING.LGPLv2.1"
        license_path.write_bytes(urllib.request.urlopen(url, timeout=30).read())
    manifest = {"python": sys.version.split()[0], "packages": packages, "qt_multimedia_ffmpeg": ffmpeg}
    (destination / "runtime-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("Collected dependency licenses and runtime-manifest.json")


if __name__ == "__main__":
    main()
