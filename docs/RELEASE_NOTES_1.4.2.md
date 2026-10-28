# FaderLogic 1.4.2

Click highlighted keys directly on the Camelot wheel to filter your library, control how titles sort, and preview tracks with a detailed audio waveform.

## What's new

- Click an actual highlighted wheel wedge to filter to that exact key. The wedge gains a brighter fill, dashed white inset and white dot while retaining its relationship color. Click again to clear, or use the centered key control beneath the wheel. Its space stays reserved so the layout does not move.
- Combine wheel filtering with text search. Changing saved playlists clears the filter. All five wheels, both charts and the colour-blind patterns remain supported.
- New **Options → Behavior** preferences independently ignore leading punctuation and track-number prefixes when sorting Title. Both are off initially and saved when changed. Track names, files and the order of your built set remain intact.
- **Detailed audio waveform** retains fine signed audio peaks and short transients. Choose Normal, RGB, shared-centreline 3-band or original colours, with the same renderer in Options and the main window. Existing waveform styles remain available.
- Updated Help, screenshots and README explain the new controls and sorting formats. Audio analysis remains in the background and finer results are cached.

## Downloads

- **Windows x64 installer:** `FaderLogic-1.4.2-windows-x64-setup.exe`, with themed Inno Setup wizard, uninstaller, Start menu and optional desktop icon.
- **Windows x64 portable:** `FaderLogic-1.4.2-windows-x64-portable.zip` or `.7z`. Extract the entire nested **FaderLogic** folder and run **FaderLogic.exe**. No separate Python installation is required.
- **Source:** `FaderLogic-1.4.2-source.zip` or `.7z`. Includes beginner setup instructions for Windows, macOS and Linux, with and without a virtual environment.
- Verify downloads with `SHA256SUMS.txt` or the individual `.sha256` files.

Existing saved playlists and preferences remain compatible. Older waveform caches refresh once per track to collect finer detail. Keep your saved-data folder when updating a portable copy.

This is a waveform overview, not a full DJ deck: phrase labels, cues and beat grids are not generated. Sorting and filtering never change your built-set/export order. Native macOS/Linux operation and import into the author's Rekordbox remain manual checks.

See the [full changelog](../CHANGELOG.md), [source setup guide](SOURCE_SETUP.md) and [validation notes](VALIDATION.md).
