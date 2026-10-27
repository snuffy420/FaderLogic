# PyInstaller spec: single-file, windowed FaderLogic.exe with the FaderLogic icon.
# Build with:  pyinstaller --noconfirm FaderLogic.spec

import os
import sys

block_cipher = None

# Resolve Windows dependencies against Windows, not DLLs injected into PATH by
# unrelated tools (for example Poppler's incompatible, versioned ICU library).
original_path = os.environ.get("PATH", "")
if sys.platform == "win32":
    windows = os.environ.get("SystemRoot", r"C:\Windows")
    os.environ["PATH"] = os.pathsep.join([
        os.path.join(windows, "System32"), windows, sys.base_prefix,
    ])

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=[],
    datas=[("assets/faderlogic.ico", "assets"), ("assets/faderlogic.png", "assets")],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    # Pillow has optional integrations with notebook/array stacks that this app
    # does not use. Keep the portable runtime focused on the actual GUI/QR needs.
    excludes=["tkinter", "IPython", "numpy", "matplotlib", "pytest", "PyQt6.QtQml", "PyQt6.QtQuick", "PyQt6.QtQuickWidgets", "PyQt6.QtQuick3D", "PyQt6.QtOpenGL"],
    cipher=block_cipher,
)
os.environ["PATH"] = original_path

if sys.platform == "win32":
    for destination, source, _kind in a.binaries:
        if os.path.basename(destination).lower() in {"icuuc.dll", "icuin.dll"}:
            raise RuntimeError(
                f"Unexpected bundled ICU library: {source}. Qt uses the Windows system ICU."
            )
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=os.environ.get("FADERLOGIC_BUILD_NAME", "FaderLogic"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=os.environ.get("FADERLOGIC_CONSOLE_BUILD") == "1",
    disable_windowed_traceback=False,
    icon="assets/faderlogic.ico",
    version="tools/version_info.txt",
)
