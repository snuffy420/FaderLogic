"""Verify the public executable's identity and dependency boundaries."""
from pathlib import Path, PureWindowsPath
import sys
from types import CodeType

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from mixlogic import __version__
from PyInstaller.archive.readers import CArchiveReader
import pefile


def strings(value):
    if isinstance(value, str):
        return [value]
    if isinstance(value, CodeType):
        return strings(value.co_consts)
    if isinstance(value, tuple):
        return [text for item in value for text in strings(item)]
    return []


def main():
    executable = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else ROOT / "dist/MixLogic.exe"
    archive = CArchiveReader(str(executable))
    filenames = {PureWindowsPath(name).name.lower() for name in archive.toc}
    if filenames & {"icuuc.dll", "icuin.dll", "icudt78.dll"}:
        raise RuntimeError("Unexpected third-party ICU DLL in the public bundle")
    if any('qtquick' in name or 'qtqml' in name for name in filenames):
        raise RuntimeError("Retired Qt Quick/3D runtime found in bundle")
    modules = archive.open_embedded_archive("PYZ.pyz")
    if __version__ not in modules.extract("mixlogic").co_consts:
        raise RuntimeError("Packaged version mismatch")
    for module in ("mixlogic.storage", "mixlogic.playlist_browser", "mixlogic.main_window", "mixlogic.dialogs"):
        modules.extract(module)
    if "#MIXLOGIC-PLAYLIST:1" not in strings(modules.extract("mixlogic.playlist")):
        raise RuntimeError("Export metadata support missing")
    for name in modules.toc:
        if name.split(".")[0] in {"IPython", "numpy", "matplotlib"}:
            raise RuntimeError("Unused optional package bundled: " + name)
    pe = pefile.PE(str(executable), fast_load=True)
    version = pe.VS_FIXEDFILEINFO[0] if hasattr(pe, "VS_FIXEDFILEINFO") else None
    if version is None:
        pe.parse_data_directories(directories=[pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_RESOURCE"]])
        version = pe.VS_FIXEDFILEINFO[0]
    actual = (version.FileVersionMS >> 16, version.FileVersionMS & 65535, version.FileVersionLS >> 16)
    if actual != tuple(map(int, __version__.split("."))):
        raise RuntimeError("Windows version resource mismatch")
    print(f"Verified MixLogic {__version__} executable and Windows version resource: {executable.name}")


if __name__ == "__main__":
    main()
