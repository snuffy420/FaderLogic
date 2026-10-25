# Building MixLogic 1.3.0

The release target is Windows x64 with Python 3.12. The portable executable includes its Python/Qt runtime and needs no Python installation on the end user's machine.

## Set up a source checkout

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe main.py
```

`setup.ps1` installs the runtime requirements into `.venv`; `Run MixLogic.cmd` launches that environment. `requirements-build.txt` additionally installs PyInstaller. Use the pinned versions when reproducing this release.

## Test and build an executable

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m PyInstaller --clean --noconfirm MixLogic.spec
.\.venv\Scripts\python.exe tools\smoke_test_exe.py dist\MixLogic.exe
```

The frozen smoke test launches a temporary copy headlessly, checks the playlist toggle, loads Options and donation/QR dependencies, and exits. Its temporary data is separate from the user's real library. The one-file bootloader requires ordinary Windows temporary-directory access; restricted execution sandboxes can block it before Python starts.

The spec constrains Windows dependency discovery to system directories so unrelated applications on `PATH` cannot inject an incompatible ICU library. It also excludes unused optional notebook/array/plotting stacks and embeds the Windows 1.3.0 version resource. It does not modify system DLLs.

To create a separately named test executable, set `MIXLOGIC_BUILD_NAME` before building. For a public build, clear that variable and `MIXLOGIC_CONSOLE_BUILD`.

## Capture current screenshots

```powershell
.\.venv\Scripts\python.exe tools\render_screenshots.py
```

This renders the actual Qt interface into `docs/screenshots/1.3.0/`. It generates temporary mono WAV test audio, decodes a real waveform through the application, and uses example playlist metadata. It never loads a user's real saved library. Generated audio and temporary application state are removed after capture.

## Build the complete release

Install 7-Zip on the build machine, then run:

```powershell
.\.venv\Scripts\python.exe tools\build_release.py
```

The tool collects dependency notices, runs the source tests, renders screenshots, builds `dist/MixLogic.exe`, verifies the frozen executable, and creates:

- `releases/MixLogic-1.3.0-windows-x64-portable.7z`, containing one top-level **MixLogic** folder.
- `releases/MixLogic-1.3.0-source.7z`, containing **MixLogic-1.3.0-source**.
- Matching `.sha256` and `.sha` SHA-256 sidecars, plus `releases/SHA256SUMS.txt`.
- `GitHub/MixLogic-1.3.0/`, a clean source tree for uploading at a repository root. A numbered suffix is used if that folder already exists.

`--package-only` packages an already verified `dist/MixLogic.exe`. The archive integrity tests, allowlisted file selection and clean-tree checks still run. Release staging stays under `.build-temp/` and is removed after packaging.

The source/portable packages include no personal playlists, waveform database, generated demo audio, virtual environment, old test executable or local backup. Only versioned public screenshots are selected from `docs/screenshots/`.

Verify an archive with `Get-FileHash PATH_TO_ARCHIVE -Algorithm SHA256` and compare it with its sidecar or `SHA256SUMS.txt`. Files ending in `.sha` contain the same SHA-256 value as `.sha256`.

See [Publishing](PUBLISHING.md) for the local GitHub upload tree and third-party source requirements.
