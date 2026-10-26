"""Verify a setup/uninstall cycle in an isolated per-user workspace directory."""
from pathlib import Path
import os
import shutil
import struct
import subprocess
import winreg
import sys
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from mixlogic import __version__
KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\{31B8D0B6-96F3-4A49-8584-A6B20822D9BA}_is1"


def registration(hive):
    try:
        with winreg.OpenKey(hive, KEY, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as handle:
            return {name: winreg.QueryValueEx(handle, name)[0] for name in
                    ("DisplayName", "DisplayVersion", "InstallLocation", "UninstallString", "DisplayIcon")}
    except FileNotFoundError:
        return None


def main():
    if registration(winreg.HKEY_CURRENT_USER) or registration(winreg.HKEY_LOCAL_MACHINE):
        raise SystemExit("An existing MixLogic installation is registered; isolated test stopped to preserve it.")
    setup = ROOT / f"releases/MixLogic-{__version__}-windows-x64-setup.exe"
    data = setup.read_bytes()
    pe_offset = struct.unpack_from("<I", data, 0x3c)[0]
    assert struct.unpack_from("<H", data, pe_offset + 4)[0] == 0x8664, "Setup is not native x64"
    stage = ROOT / ".build-temp" / ("installer-test-" + uuid4().hex)
    stage.mkdir(parents=True)
    assert stage.resolve().is_relative_to((ROOT / ".build-temp").resolve())
    app = stage / "app"
    uninstaller = app / "unins000.exe"
    try:
        result = subprocess.run([str(setup), "/CURRENTUSER", "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                                 "/NOICONS", "/TASKS=", "/DIR=" + str(app), "/LOG=" + str(stage / "setup.log")], timeout=90)
        assert result.returncode == 0, f"Setup exit {result.returncode}; inspect {stage}"
        values = registration(winreg.HKEY_CURRENT_USER)
        assert values and values["DisplayVersion"] == __version__, values
        assert Path(values["InstallLocation"]).resolve() == app.resolve(), values
        assert "MixLogic" in values["DisplayName"] and str(app) in values["UninstallString"], values
        assert (app / "installed.flag").is_file() and uninstaller.is_file()
        assert (app / "docs/SOURCE_SETUP.md").is_file() and (app / "licenses/InnoSetup-LICENSE.txt").is_file()
        assert (app / "MixLogic.exe").read_bytes() == (ROOT / "dist/MixLogic.exe").read_bytes()
        profile = stage / "user-data"
        profile.mkdir()
        run = subprocess.run([str(app / "MixLogic.exe"), "--smoke-test"],
                             env=dict(os.environ, QT_QPA_PLATFORM="offscreen", LOCALAPPDATA=str(profile)),
                             capture_output=True, text=True, timeout=60)
        assert run.returncode == 0, (run.stdout, run.stderr)
        database = profile / "MixLogic/MixLogic-data/library.sqlite3"
        assert database.is_file(), "Installed app did not save to its user profile"
        assert not (app / "MixLogic-data").exists(), "Installed app wrote data in its program directory"
        remove = subprocess.run([str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], timeout=60)
        assert remove.returncode == 0, remove.returncode
        assert registration(winreg.HKEY_CURRENT_USER) is None, "Uninstall entry remains"
        assert not (app / "MixLogic.exe").exists(), "Application remains after uninstall"
        assert database.is_file(), "Uninstall deleted saved user data"
        print("PASS: native x64 setup, full payload, Add/Remove Programs registration, isolated installed startup, AppData storage, uninstall and saved-data retention")
    finally:
        # Remove only this test's installation, never a pre-existing installation.
        values = registration(winreg.HKEY_CURRENT_USER)
        if values and Path(values["InstallLocation"]).resolve() == app.resolve() and uninstaller.exists():
            subprocess.run([str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], timeout=60)
        if registration(winreg.HKEY_CURRENT_USER):
            print("Test registration remains; preserve diagnostics at", stage)
        else:
            shutil.rmtree(stage)


if __name__ == "__main__":
    main()
