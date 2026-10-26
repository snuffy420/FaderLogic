"""Runtime data location for portable, source and installed copies."""
import os
from pathlib import Path
import sys


def runtime_data_dir(executable=None, frozen=None):
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if not frozen:
        return str(Path(__file__).resolve().parents[1])
    folder = Path(executable or sys.executable).resolve().parent
    if (folder / "installed.flag").is_file():
        local = os.environ.get("LOCALAPPDATA")
        if local:
            location = Path(local) / "MixLogic"
        else:
            from PyQt6.QtCore import QStandardPaths
            location = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
        location.mkdir(parents=True, exist_ok=True)
        return str(location)
    return str(folder)
