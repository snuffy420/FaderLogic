"""Runtime data location for portable, source and installed copies."""
import os
from pathlib import Path
import sys
import shutil
import sqlite3
from uuid import uuid4
from contextlib import closing


def prepare_data_directory(base_dir):
    """Copy a previous library once, preserving its sources and original database.

    Portable copies discover the old folder beside the EXE. Installed copies also
    discover the former per-user location. Never merge over an existing library.
    """
    base = Path(base_dir).resolve()
    target = base / 'FaderLogic-data'
    if target.exists():
        return target
    candidates = [base / 'MixLogic-data']
    local = os.environ.get('LOCALAPPDATA')
    if local and base == (Path(local) / 'FaderLogic').resolve():
        candidates.append(Path(local) / 'MixLogic' / 'MixLogic-data')
    for source in candidates:
        database = source / 'library.sqlite3'
        if not database.is_file():
            continue
        base.mkdir(parents=True, exist_ok=True)
        stage = base / ('.faderlogic-migration-' + uuid4().hex)
        stage.mkdir()
        try:
            # SQLite backup includes committed data still in a WAL file.
            with closing(sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True)) as old:
                with closing(sqlite3.connect(stage / 'library.sqlite3')) as new:
                    old.backup(new)
                    if new.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                        raise sqlite3.DatabaseError('Previous library failed its integrity check')
            if (source / 'sources').is_dir():
                shutil.copytree(source / 'sources', stage / 'sources')
            os.replace(stage, target)
            return target
        finally:
            if stage.exists():
                if stage.resolve().parent != base or not stage.name.startswith('.faderlogic-migration-'):
                    raise RuntimeError('Invalid migration cleanup directory')
                shutil.rmtree(stage)
    return target


def runtime_data_dir(executable=None, frozen=None):
    frozen = getattr(sys, "frozen", False) if frozen is None else frozen
    if not frozen:
        return str(Path(__file__).resolve().parents[1])
    folder = Path(executable or sys.executable).resolve().parent
    if (folder / "installed.flag").is_file():
        local = os.environ.get("LOCALAPPDATA")
        if local:
            location = Path(local) / "FaderLogic"
        else:
            from PyQt6.QtCore import QStandardPaths
            location = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation))
        location.mkdir(parents=True, exist_ok=True)
        return str(location)
    return str(folder)
