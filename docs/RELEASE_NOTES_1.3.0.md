# MixLogic 1.3.0

A harmonic DJ set builder focused on Rekordbox playlists, with a larger wheel, saved libraries and a cleaner workspace.

## Highlights

- Import Rekordbox M3U8/TXT pairs once, then switch between saved playlists.
- Remember each playlist's linked music folder and restore the last session and current set.
- Preview a track from either table while keeping set reordering available.
- Explore two directional relation charts with clear wheel/table highlighting.
- Resize the tables and columns, or hide unused columns independently.
- Export an exact-order UTF-8 M3U8; reopen MixLogic exports directly for further editing.
- Use matching themed dialogs, a compact header, clearer Help/About and a fixed-layout BTC copy confirmation.

## Downloads

- `MixLogic-1.3.0-windows-x64-portable.7z` — extract the complete nested **MixLogic** folder and run `MixLogic.exe`. Python is included in the executable.
- `MixLogic-1.3.0-source.7z` — application source, pinned dependencies, tests, documentation and release tools.
- `.sha256` / `.sha` sidecars and `SHA256SUMS.txt` — SHA-256 checksums for both archives.

## Updating

Close the previous copy before updating. Keep `MixLogic-data/` beside the executable to retain your saved playlists, linked folders, preferences and current set. Keep your audio files at their referenced locations or use Relink Folder.

## Validation and scope

26 automated tests passed, along with the compiled startup/Options/donation smoke test. The UI was checked at 150% scaling. Both charts are verified against the supplied reference rows; current exports are tested for metadata round-trip, duplicates and exact order.

Rekordbox documents M3U8 import through File → Import → Import Playlist. A live import in the Rekordbox desktop application is a separate manual check; this release does not claim certification by Rekordbox/AlphaTheta.

See the [full changelog](../CHANGELOG.md), [README](../README.md), [validation notes](VALIDATION.md) and [license notices](../THIRD_PARTY_NOTICES.md).
