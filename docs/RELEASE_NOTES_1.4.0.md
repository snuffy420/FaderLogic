# FaderLogic 1.4.0

First public release of FaderLogic: a Rekordbox-focused harmonic set builder with saved libraries, an interactive Camelot wheel, track previews and exact-order M3U8 export.

The private-test name MixLogic has been replaced throughout the release. Version remains 1.4.0. Earlier exported sets still import directly, and previous libraries/preferences are copied forward on first launch when found. See [migration instructions](MIGRATING.md).

## Downloads

- **Windows x64 installer:** FaderLogic-1.4.0-windows-x64-setup.exe — themed Inno Setup wizard, Program Files installation, uninstaller, Start menu and optional desktop shortcut.
- **Windows x64 portable:** FaderLogic-1.4.0-windows-x64-portable.7z — extract the entire nested FaderLogic folder, then run FaderLogic.exe. Python is included.
- **Source ZIP / 7z:** FaderLogic-1.4.0-source.zip or FaderLogic-1.4.0-source.7z — source, assets, tests, pinned dependencies, notices and beginner Windows/macOS/Linux setup instructions.
- **SHA256SUMS.txt** and per-file checksum sidecars for verification.

## Highlights

- Import Rekordbox M3U8/TXT pairs, save and switch libraries, remember linked folders and restore the session.
- Build, audition and reorder sets; export exact-order UTF-8 M3U8 and reopen FaderLogic exports with their metadata.
- Two directional relation charts, five wheel designs, selected-key centers, Both labels, independent wedge borders and matching legends.
- Color-blind wheel with alternative relation colors, patterns, printed codes and separate explanations for both charts.
- Nine waveform designs with Normal, RGB, 3-band and original FaderLogic colors. Cancellable background analysis and caching; accurate current-track previews in Options.
- Saved Dark/Light themes, adjustable panels/columns and independent column visibility.
- Missing fields display Unknown in both tables. Keys/BPM are never guessed.
- Integrated Help, metadata details, About and optional BTC support; themed static contact page for GitHub Pages.

Windows x64 is tested. macOS/Linux use source; their native GUI/audio operation remains untested here. Both venv and non-venv app-local instructions are included. No 3D runtime is required. No account or cloud playlist sync is needed.

Read the full [README](../README.md), [changelog](../CHANGELOG.md) and [source setup guide](SOURCE_SETUP.md). FaderLogic is independent of Rekordbox/AlphaTheta.
