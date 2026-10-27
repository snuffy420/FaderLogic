# Building FaderLogic 1.4.0

The release target is Windows x64 with Python 3.12. The portable executable includes its Python/Qt runtime and needs no Python installation on the end user's machine.

For beginner macOS/Linux runtime instructions, both with and without a virtual environment, see [SOURCE_SETUP.md](SOURCE_SETUP.md). The release-building tools below target Windows.

## Set up a source checkout

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe main.py
```

`setup.ps1` installs the runtime requirements into `.venv`; `Run FaderLogic.cmd` launches that environment. `requirements-build.txt` additionally installs PyInstaller. Use the pinned versions when reproducing this release.

## Test and build an executable

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm FaderLogic.spec
.\.venv\Scripts\python.exe tools\smoke_test_exe.py dist\FaderLogic.exe
```

The frozen smoke test launches a temporary copy headlessly, checks the playlist toggle, loads Options and donation/QR dependencies, and exits. Its temporary data is separate from the user's real library. The one-file bootloader requires ordinary Windows temporary-directory access; restricted execution sandboxes can block it before Python starts.

The spec constrains Windows dependency discovery to system directories so unrelated applications on `PATH` cannot inject an incompatible ICU library. It also excludes unused optional notebook/array/plotting stacks and embeds the Windows 1.4.0 version resource. It does not modify system DLLs.

To create a separately named test executable, set `FADERLOGIC_BUILD_NAME` before building. For a public build, clear that variable and `FADERLOGIC_CONSOLE_BUILD`.

## Capture current screenshots

```powershell
.\.venv\Scripts\python.exe tools\render_screenshots.py
```

This renders the actual Qt interface into `docs/screenshots/1.4.0/`. It generates temporary mono WAV test audio, decodes a real waveform through the application, and uses example playlist metadata. It never loads a user's real saved library. Generated audio and temporary application state are removed after capture.

## Build the complete release

Install 7-Zip and Inno Setup 7 on the build machine, then run:

```powershell
.\.venv\Scripts\python.exe tools\build_release.py
```

The tool collects dependency notices, runs the source tests, renders screenshots, builds `dist/FaderLogic.exe`, verifies the frozen executable, compiles the installer, and creates:

- `releases/FaderLogic-1.4.0-windows-x64-portable.7z`, containing one top-level **FaderLogic** folder.
- `releases/FaderLogic-1.4.0-source.7z`, containing **FaderLogic-1.4.0-source**.
- `releases/FaderLogic-1.4.0-windows-x64-setup.exe`, the themed x64 installer.
- Matching `.sha256` and `.sha` SHA-256 sidecars, plus `releases/SHA256SUMS.txt`.
- `GitHub/FaderLogic-1.4.0/`, a clean source tree for uploading at a repository root. A numbered suffix is used if that folder already exists.

`--package-only` packages an already verified `dist/FaderLogic.exe`. The archive integrity tests, allowlisted file selection and clean-tree checks still run. Release staging stays under `.build-temp/` and is removed after packaging.

To compile just the installer, run `python tools/build_installer.py` after building the public executable. It uses `installer/FaderLogic.iss` and generates logo artwork from the original app icon. Set `INNO_ISCC` to your Inno Setup 7 `ISCC.exe` path if needed; an optional local portable compiler at `.build-tools/InnoSetup/ISCC.exe` is also supported. That compiler is not part of the source archive.

The installer places an `installed.flag` marker beside the executable. This selects per-user `%LOCALAPPDATA%\\FaderLogic` storage. Do not add that marker to the portable archive. The default installer needs elevation for Program Files; `/CURRENTUSER` is available for isolated installer verification.

Run `python tools/test_installer.py` for an isolated per-user install, installed-app smoke check and uninstall. It briefly creates an Add/Remove Programs registration, removes its test installation afterward, and refuses to run if FaderLogic is already registered so it cannot disturb an existing installation. This check is separate from compilation.

The source/portable packages include no personal playlists, waveform database, generated demo audio, virtual environment, old test executable or local backup. Only versioned public screenshots are selected from `docs/screenshots/`.

Verify an archive with `Get-FileHash PATH_TO_ARCHIVE -Algorithm SHA256` and compare it with its sidecar or `SHA256SUMS.txt`. Files ending in `.sha` contain the same SHA-256 value as `.sha256`.

See [Publishing](PUBLISHING.md) for the local GitHub upload tree and third-party source requirements.
