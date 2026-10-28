"""Build verified local source/portable releases and a clean GitHub upload tree."""
from pathlib import Path, PureWindowsPath
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from faderlogic import __version__

SOURCE_FILES = ("main.py", "FaderLogic.spec", "README.md", "CHANGELOG.md", "LICENSE", "COPYRIGHT",
                "THIRD_PARTY_NOTICES.md", "requirements.txt", "requirements-build.txt", ".gitignore",
                ".gitattributes", ".nojekyll", "setup.ps1", "Run FaderLogic.cmd", "run_faderlogic.sh")
SOURCE_DIRS = ("faderlogic", "assets", "tools", "tests", "licenses", ".github", "installer")


def run(*arguments):
    subprocess.run([sys.executable, *arguments], cwd=ROOT, check=True)


def sevenzip():
    command = shutil.which("7z") or shutil.which("7za")
    installed = Path(os.environ.get("ProgramFiles", "C:/Program Files")) / "7-Zip/7z.exe"
    if command:
        return command
    if installed.is_file():
        return str(installed)
    raise RuntimeError("7-Zip is needed on the build machine to create the release archives")


def copy_docs(target):
    target.mkdir(parents=True, exist_ok=True)
    public_docs=("SOURCE_SETUP.md","BUILDING.md","PUBLISHING.md","VALIDATION.md",
                 "APPEARANCE.md","RELEASE_NOTES_1.4.0.md","RELEASE_NOTES_1.4.2.md","CONTACT_README_BLOCK.md","MIGRATING.md","contact.html")
    for name in public_docs:
        shutil.copy2(ROOT/"docs"/name,target/name)
    shutil.copytree(ROOT / "docs/screenshots" / __version__, target / "screenshots" / __version__,
                    ignore=shutil.ignore_patterns('review-*'))


def copy_source(target):
    target.mkdir(parents=True)
    for name in SOURCE_FILES:
        shutil.copy2(ROOT / name, target / name)
    for name in SOURCE_DIRS:
        shutil.copytree(ROOT / name, target / name,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo"))
    copy_docs(target / "docs")
    return target


def verify_clean_tree(root, portable=False):
    executable_count = 0
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in {"FaderLogic-data", "MixLogic-data", ".venv", "__pycache__", "dist", "backups", ".freebuff"} for part in relative.parts):
            raise RuntimeError("Private/generated directory in release: " + str(relative))
        if path.is_file() and path.suffix.lower() in {".db", ".sqlite3", ".m3u8", ".wav", ".mp3", ".pyc"}:
            raise RuntimeError("Private/generated file in release: " + str(relative))
        if path.suffix.lower() == ".exe":
            executable_count += 1
            if not portable or relative.as_posix() != "FaderLogic.exe":
                raise RuntimeError("Unexpected executable in release: " + str(relative))
    if executable_count != int(portable):
        raise RuntimeError("Incorrect executable count in release")
    for path in root.rglob("*.md"):
        for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
            if "://" not in link and not link.startswith(("#", "mailto:")):
                local = path.parent / link.split("#")[0]
                if not local.exists():
                    raise RuntimeError(f"Broken local documentation link: {path.name}: {link}")


def archive(tool, stage, folder, name):
    target = stage / name
    subprocess.run([tool, "a", "-tzip" if name.endswith(".zip") else "-t7z", "-mx=5", "-mmt=2", "-bd", "-bso0", "-bsp0", str(target), folder.name],
                   cwd=stage, check=True)
    subprocess.run([tool, "t", "-bd", "-bso0", "-bsp0", str(target)], check=True)
    listing = subprocess.check_output([tool, "l", "-slt", str(target)], text=True)
    names = [line[7:] for line in listing.splitlines() if line.startswith("Path = ")][1:]
    if not names or any(PureWindowsPath(value).parts[0] != folder.name for value in names):
        raise RuntimeError("Archive must contain exactly one expected top-level folder")
    return target


def package():
    tool = sevenzip()
    temp_root = (ROOT / ".build-temp").resolve()
    temp_root.mkdir(exist_ok=True)
    stage = temp_root / ("package-" + uuid4().hex)
    stage.mkdir()
    if not stage.resolve().is_relative_to(temp_root):
        raise RuntimeError("Invalid release staging path")
    releases = ROOT / "releases"
    releases.mkdir(exist_ok=True)
    prefix = f"FaderLogic-{__version__}"
    try:
        portable = stage / "FaderLogic"
        portable.mkdir()
        shutil.copy2(ROOT / "dist/FaderLogic.exe", portable / "FaderLogic.exe")
        for name in ("README.md", "CHANGELOG.md", "LICENSE", "COPYRIGHT", "THIRD_PARTY_NOTICES.md"):
            shutil.copy2(ROOT / name, portable / name)
        for name in ("licenses", "assets"):
            shutil.copytree(ROOT / name, portable / name)
        copy_docs(portable / "docs")
        # Build-only instructions link to these files too; include them as useful
        # documentation without suggesting the portable app requires Python.
        for name in ("requirements.txt", "requirements-build.txt"):
            shutil.copy2(ROOT / name, portable / name)
        source = copy_source(stage / (prefix + "-source"))
        verify_clean_tree(portable, portable=True)
        verify_clean_tree(source)
        output = []
        for folder, name in ((portable, prefix + "-windows-x64-portable.7z"),
                             (portable, prefix + "-windows-x64-portable.zip"),
                             (source, prefix + "-source.7z"),
                             (source, prefix + "-source.zip")):
            candidate = archive(tool, stage, folder, name)
            final = releases / name
            os.replace(candidate, final)
            output.append(final)
        setup = releases / (prefix + "-windows-x64-setup.exe")
        if setup.is_file():
            output.append(setup)
        github_base = ROOT / "GitHub"
        github_base.mkdir(exist_ok=True)
        github = github_base / prefix
        number = 2
        while github.exists():
            github = github_base / (prefix + f"-{number}")
            number += 1
        copy_source(github)
        verify_clean_tree(github)
        checksum_lines = []
        for path in output:
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            line = digest + "  " + path.name + "\n"
            for extension in (".sha256", ".sha"):
                path.with_name(path.name + extension).write_text(line, encoding="ascii")
            checksum_lines.append(line)
            print(f"{path}: {path.stat().st_size / 1024**2:.2f} MiB")
        (releases / "SHA256SUMS.txt").write_text("".join(checksum_lines), encoding="ascii")
        print("Clean GitHub upload tree:", github)
    finally:
        shutil.rmtree(stage)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-only", action="store_true")
    arguments = parser.parse_args()
    os.chdir(ROOT)
    sevenzip()
    if not arguments.package_only:
        os.environ.pop("FADERLOGIC_BUILD_NAME", None)
        os.environ.pop("FADERLOGIC_CONSOLE_BUILD", None)
        run("tools/collect_licenses.py")
        run("-m", "unittest", "discover", "-s", "tests", "-v")
        run("tools/render_screenshots.py")
        run("-m", "PyInstaller", "--clean", "--noconfirm", "FaderLogic.spec")
        run("tools/check_bundle.py")
        run("tools/smoke_test_exe.py", "dist/FaderLogic.exe")
        run("tools/build_installer.py")
    package()


if __name__ == "__main__":
    main()
